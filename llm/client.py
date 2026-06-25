"""LLM 호출 — provider 중립 (OpenAI 기본 / Anthropic 폴백) + 모의 모드"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from llm.prompts import build_messages
from llm.schema import coerce, default_analysis


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    s, e = text.find("{"), text.rfind("}")
    if s >= 0 and e > s:
        text = text[s:e + 1]
    return json.loads(text)


def _call_openai(msgs: Dict[str, str]) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI()  # OPENAI_API_KEY 환경변수 사용
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": msgs["system"]},
                  {"role": "user", "content": msgs["user"]}],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=4096,
    )
    return _extract_json(resp.choices[0].message.content)


def _call_anthropic(msgs: Dict[str, str]) -> Dict[str, Any]:
    import anthropic
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=msgs["system"] + "\n\n반드시 순수 JSON 한 개만 출력.",
        messages=[{"role": "user", "content": msgs["user"]}],
    )
    return _extract_json(resp.content[0].text)


def generate_analysis(context: Dict[str, Any], ticker_type: str,
                      provider: str | None = None, mock: bool = False) -> Dict[str, Any]:
    """그라운딩 컨텍스트로 AI 분석을 생성한다. 실패/모의 시 골격 또는 모의 데이터 반환."""
    if mock:
        return coerce(_mock(context, ticker_type))

    provider = provider or os.environ.get("LLM_PROVIDER", "openai")
    try:
        raw = _call_anthropic(build_messages(context, ticker_type)) if provider == "anthropic" \
            else _call_openai(build_messages(context, ticker_type))
        return coerce(raw)
    except Exception as e:
        # 실패해도 리포트는 나오게 — 빈 골격 + 에러 표시
        out = default_analysis()
        out["conclusion"] = {"text": f"AI 분석 생성 실패: {e}", "highlight": ""}
        out["_error"] = str(e)
        return out


# ──────────────────────────────────────────────────────────────────────────
# 모의 출력 (키 없이 디자인/렌더 검증용)
# ──────────────────────────────────────────────────────────────────────────
def _mock(context: Dict[str, Any], ticker_type: str) -> Dict[str, Any]:
    m = context.get("market", {})
    meta = context.get("meta", {})
    d = m.get("daily", {})
    price = (m.get("price") or {}).get("last") or d.get("last") or 0
    an = m.get("analyst", {})
    tgt = an.get("target_mean")
    is_etf = ticker_type == "etf_leveraged"

    base = {
        "conclusion": {
            "text": f"[모의데이터] {meta.get('name','')} — RSI {d.get('rsi','?')} / 현재가 ${price}. 실제 배포 시 AI가 채웁니다.",
            "highlight": "이 화면은 디자인 검증용 모의 출력입니다 (실데이터+가짜 판단)."},
        "headline_metrics": {
            "rsi_daily_label": "중립" if (d.get("rsi") or 50) < 70 else "과매수",
            "rsi_intraday_label": "조정권", "macd_daily_label": "약세 전환",
            "entry_zone": f"${round(price*0.93,1)}~{round(price*0.97,1)}",
            "exit_zone": f"${tgt or round(price*1.2,1)}"},
        "daily": {"ma_short": "5·20일 단기 흐름(모의)", "ma_mid": "100일 대비(모의)", "ma_long": "200일(모의)",
                  "rsi": f"RSI {d.get('rsi','?')} — 모의 해석", "macd": "MACD 모의 해석",
                  "bollinger": "볼린저 모의", "resistance": "저항 모의", "summary": "일봉 종합(모의)"},
        "intraday": {"info": "120분봉 모의 도입부.", "summary": "통합 판단(모의)",
                     "rows": {"ma": "정배열(모의)", "rsi": f"{(m.get('intraday_120m') or {}).get('rsi','?')}",
                              "stoch": "모의", "bollinger": "모의", "volume": "모의", "macd": "모의"}},
        "catalysts": [{"title": "모의 호재 1", "tag": "모의", "source": "(모의 — 실제는 뉴스 근거)"},
                      {"title": "모의 호재 2", "tag": "모의", "source": ""}],
        "risks": [{"title": "모의 리스크 1", "tag": "주의", "source": ""},
                  {"title": "모의 리스크 2", "tag": "경고", "source": ""}],
        "waves": [{"num": "1파", "range": "모의", "desc": "저점 반등", "current": False},
                  {"num": "2파", "range": "모의", "desc": "눌림", "current": False},
                  {"num": "3파 현재", "range": "모의", "desc": "진행중", "current": True}],
        "scenarios": [{"label": "시나리오1 — 모의 상승", "pct": 45, "dir": "bull"},
                      {"label": "시나리오2 — 모의 횡보", "pct": 30, "dir": "warn"},
                      {"label": "시나리오3 — 모의 하락", "pct": 25, "dir": "bear"}],
        "strategy": {"buy": [{"label": "1차 매수(모의)", "price": f"${round(price*0.95,1)}"},
                             {"label": "2차 매수(모의)", "price": f"${round(price*0.88,1)}"}],
                     "sell": [{"label": "분할매도(모의)", "price": f"${round(price*1.15,1)}"},
                              {"label": "손절(모의)", "price": f"${round(price*0.85,1)}"}]},
        "scores": {"technical_daily": 62, "technical_intraday": 48, "supply": 58,
                   "fundamental": 0 if is_etf else 55, "growth": 70, "total": 60},
        "simulation": {"target": f"${round(price*1.2,1)}", "stop": f"${round(price*0.85,1)}",
                       "target_pct": "+20%", "stop_pct": "-15%", "rr": "1.3:1", "weight": "20%"},
        "probability": [{"label": "상승", "pct": 45, "dir": "bull"},
                        {"label": "횡보", "pct": 30, "dir": "warn"},
                        {"label": "하락", "pct": 25, "dir": "bear"}],
        "investor": {"aggressive": "공격형 전략(모의)", "neutral": "중립형(모의)", "conservative": "보수형(모의)"},
        "sentiment": "시장심리 모의 요약.",
        "pcr_comment": f"PCR {(m.get('options') or {}).get('pcr','?')} — 모의 해석.",
    }
    if is_etf:
        base["etf"] = {"underlying_view": f"{meta.get('underlying','기초지수')} 방향(모의)",
                       "decay_warning": "일일 리밸런싱으로 횡보장 가치 소실 — 장기보유 부적합(모의)",
                       "volatility": "변동성 매우 높음(모의)", "hold_period": "수일 내 단기 트레이딩 권장(모의)"}
    return base
