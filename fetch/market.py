"""yfinance 기반 시세·기술지표·옵션·애널리스트·어닝 수집

순수 '데이터' 계층 — 해석/판단은 하지 않고 수치만 산출한다(해석은 LLM 담당).
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands


def _r(v, n: int = 2):
    try:
        f = float(v)
        if math.isnan(f):
            return None
        return round(f, n)
    except (TypeError, ValueError):
        return None


def _indicator_snapshot(df: pd.DataFrame) -> Dict[str, Any]:
    """OHLCV 데이터프레임에서 최신 기술지표 스냅샷을 계산한다."""
    close, high, low, vol = df["Close"], df["High"], df["Low"], df["Volume"]
    out: Dict[str, Any] = {"last": _r(close.iloc[-1])}

    if len(close) >= 15:
        rsi_s = RSIIndicator(close, 14).rsi().dropna()
        out["rsi"] = _r(rsi_s.iloc[-1], 1)
        # 방향성/최근 저점 — 진입 단계 판정용 (값뿐 아니라 추세 반영)
        out["rsi_prev"] = _r(rsi_s.iloc[-4], 1) if len(rsi_s) >= 4 else out["rsi"]
        recent = rsi_s.tail(14)
        out["rsi_min"] = _r(recent.min(), 1) if len(recent) else out["rsi"]
        st = StochasticOscillator(high, low, close)
        out["stoch_k"] = _r(st.stoch().iloc[-1], 1)
        out["stoch_d"] = _r(st.stoch_signal().iloc[-1], 1)
    if len(close) >= 26:
        macd = MACD(close)
        out["macd"] = _r(macd.macd().iloc[-1], 3)
        out["macd_signal"] = _r(macd.macd_signal().iloc[-1], 3)
        out["macd_hist"] = _r(macd.macd_diff().iloc[-1], 3)
    if len(close) >= 20:
        bb = BollingerBands(close)
        out["bb_high"] = _r(bb.bollinger_hband().iloc[-1])
        out["bb_mid"] = _r(bb.bollinger_mavg().iloc[-1])
        out["bb_low"] = _r(bb.bollinger_lband().iloc[-1])
    for w in (5, 20, 100, 200):
        if len(close) >= w:
            out[f"sma{w}"] = _r(SMAIndicator(close, w).sma_indicator().iloc[-1])

    if out.get("last") and out.get("sma20"):
        out["vs_sma20_pct"] = _r((out["last"] / out["sma20"] - 1) * 100, 1)
    v = vol.iloc[-1]
    out["volume"] = int(v) if not math.isnan(v) else None
    # 최근 거래량 추세(직전 5봉 평균 대비)
    if len(vol) >= 6:
        recent_avg = vol.iloc[-6:-1].mean()
        out["vol_vs_avg_pct"] = _r((v / recent_avg - 1) * 100, 0) if recent_avg else None
    return out


def _resample_120m(df60: pd.DataFrame) -> pd.DataFrame:
    """60분봉을 거래일별로 '장 시작(첫 봉) 기준' 2개씩 묶어 120분봉 생성.

    단순 시계 기준 resample('120min')은 미 정규장 9:30 ET 세션과 어긋나
    차트 플랫폼(TradingView 등)의 120분봉과 불일치한다. 세션 시작 기준으로
    묶어야 9:30-11:30, 11:30-13:30, 13:30-15:30, 15:30-16:00 봉이 맞춰진다.
    """
    rows, idx = [], []
    for _, g in df60.groupby(df60.index.date):
        g = g.sort_index()
        for i in range(0, len(g), 2):
            chunk = g.iloc[i:i + 2]
            rows.append({
                "Open": chunk["Open"].iloc[0], "High": chunk["High"].max(),
                "Low": chunk["Low"].min(), "Close": chunk["Close"].iloc[-1],
                "Volume": chunk["Volume"].sum(),
            })
            idx.append(chunk.index[0])
    if not rows:
        return df60.iloc[0:0]
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx))


def _options_pcr(t: yf.Ticker) -> Dict[str, Any]:
    """옵션 PCR + 만기별 Put/Call Wall + 심리 게이지 + 달러 플로우(추산)."""
    exps = list(t.options[:4])
    spot = None
    try:
        spot = float(t.fast_info.get("lastPrice"))
    except Exception:
        pass

    total_c = total_p = 0.0
    call_dollar = put_dollar = 0.0
    per_exp = []
    for exp in exps:
        try:
            ch = t.option_chain(exp)
            calls, puts = ch.calls, ch.puts
            c_oi = calls["openInterest"].fillna(0)
            p_oi = puts["openInterest"].fillna(0)
            c_sum, p_sum = c_oi.sum(), p_oi.sum()
            if c_sum + p_sum == 0:  # OI 없으면 거래량 대체
                c_oi, p_oi = calls["volume"].fillna(0), puts["volume"].fillna(0)
                c_sum, p_sum = c_oi.sum(), p_oi.sum()
            total_c += c_sum
            total_p += p_sum
            # 달러 플로우 추산 (거래량 × 종가 × 100)
            call_dollar += (calls["volume"].fillna(0) * calls["lastPrice"].fillna(0) * 100).sum()
            put_dollar += (puts["volume"].fillna(0) * puts["lastPrice"].fillna(0) * 100).sum()
            # Wall (최대 OI 행사가)
            call_wall = _r(calls.loc[c_oi.idxmax(), "strike"]) if c_sum > 0 else None
            put_wall = _r(puts.loc[p_oi.idxmax(), "strike"]) if p_sum > 0 else None
            tot = c_sum + p_sum
            per_exp.append({
                "exp": exp,
                "pcr": _r(p_sum / c_sum, 2) if c_sum > 0 else None,
                "put_wall": put_wall, "call_wall": call_wall,
                "put_pct": round(p_sum / tot * 100) if tot else None,
                "call_pct": round(c_sum / tot * 100) if tot else None,
            })
        except Exception:
            continue

    pcr_all = _r(total_p / total_c, 2) if total_c > 0 else None
    # 심리 게이지: PCR 0.5→0%, 1.0→50%, 2.0→100%
    gauge = 50
    if pcr_all is not None:
        gauge = (pcr_all - 0.5) / 0.5 * 50 if pcr_all <= 1.0 else 50 + (pcr_all - 1.0) / 1.0 * 50
        gauge = round(max(0, min(100, gauge)))
    return {
        "pcr": pcr_all,
        "gauge_pct": gauge,
        "spot": _r(spot),
        "per_exp": per_exp,
        "call_dollar": round(call_dollar),
        "put_dollar": round(put_dollar),
    }


def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """종목의 시세·지표·옵션·애널리스트·어닝 데이터를 수집한다."""
    t = yf.Ticker(ticker)
    result: Dict[str, Any] = {"ticker": ticker, "errors": []}

    # 일봉
    try:
        d = t.history(period="1y", interval="1d")
        if not d.empty:
            result["daily"] = _indicator_snapshot(d)
            close = d["Close"]
            result["price"] = {
                "last": _r(close.iloc[-1]),
                "prev": _r(close.iloc[-2]) if len(close) >= 2 else None,
                "chg_pct": _r((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) >= 2 else None,
            }
            result["series_daily"] = [_r(x) for x in close.tail(120).tolist()]
    except Exception as e:
        result["errors"].append(f"daily:{e}")

    # 120분봉 (60분봉 → 리샘플). 프리장·애프터장 포함 → 증권사 차트(실시간/연장거래)와 정합
    try:
        h = t.history(period="60d", interval="60m", prepost=True)
        if not h.empty:
            r120 = _resample_120m(h)
            if len(r120) >= 15:
                result["intraday_120m"] = _indicator_snapshot(r120)
    except Exception as e:
        result["errors"].append(f"120m:{e}")

    # 기본 정보 + 애널리스트
    try:
        info = t.info or {}
        result["info"] = {
            "name": info.get("shortName") or info.get("longName"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": _r(info.get("trailingPE")),
            "forward_pe": _r(info.get("forwardPE")),
            "high_52w": _r(info.get("fiftyTwoWeekHigh")),
            "low_52w": _r(info.get("fiftyTwoWeekLow")),
            "beta": _r(info.get("beta")),
        }
        analyst = {
            "target_mean": _r(info.get("targetMeanPrice")),
            "target_high": _r(info.get("targetHighPrice")),
            "target_low": _r(info.get("targetLowPrice")),
            "recommendation": info.get("recommendationKey"),
            "num_analysts": info.get("numberOfAnalystOpinions"),
            "buy": None, "hold": None, "sell": None,
        }
        # Buy/Hold/Sell 분포 (yfinance recommendations)
        try:
            rec = t.recommendations
            if rec is not None and len(rec) > 0:
                row = rec.iloc[0]
                analyst["buy"] = int(row.get("strongBuy", 0)) + int(row.get("buy", 0))
                analyst["hold"] = int(row.get("hold", 0))
                analyst["sell"] = int(row.get("sell", 0)) + int(row.get("strongSell", 0))
        except Exception:
            pass
        result["analyst"] = analyst
    except Exception as e:
        result["errors"].append(f"info:{e}")

    # 어닝일
    try:
        cal = t.calendar
        ed = None
        if isinstance(cal, dict):
            v = cal.get("Earnings Date")
            ed = (v[0] if isinstance(v, list) and v else v) if v else None
        elif isinstance(cal, pd.DataFrame) and "Earnings Date" in cal.index:
            ed = cal.loc["Earnings Date"].iloc[0]
        if ed is not None:
            result["earnings_date"] = str(ed)[:10]
    except Exception as e:
        result["errors"].append(f"earnings:{e}")

    # 옵션 PCR
    try:
        result["options"] = _options_pcr(t)
    except Exception as e:
        result["errors"].append(f"options:{e}")

    return result


if __name__ == "__main__":
    import json
    import sys
    tk = sys.argv[1] if len(sys.argv) > 1 else "IONQ"
    data = fetch_stock_data(tk)
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
