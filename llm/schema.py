"""AI 분석 출력 스키마 — 기본 골격 + 병합(coerce)

LLM이 반환한 JSON을 이 골격에 병합해 누락 필드를 안전하게 채운다.
렌더러는 항상 완전한 구조를 받는다(키 누락으로 깨지지 않음).
"""

from __future__ import annotations

from typing import Any, Dict


def default_analysis() -> Dict[str, Any]:
    return {
        "conclusion": {"text": "", "highlight": ""},
        "headline_metrics": {
            "rsi_daily_label": "", "rsi_intraday_label": "", "macd_daily_label": "",
            "entry_zone": "", "exit_zone": "",
        },
        "daily": {
            "ma_short": "", "ma_mid": "", "ma_long": "",
            "rsi": "", "macd": "", "bollinger": "", "resistance": "", "summary": "",
        },
        "intraday": {"info": "", "summary": "",
                     "rows": {"ma": "", "rsi": "", "stoch": "", "bollinger": "", "volume": "", "macd": ""}},
        "catalysts": [],   # [{title, tag, source}]
        "risks": [],       # [{title, tag, source}]
        "waves": [],       # [{num, range, desc, current(bool)}]
        "scenarios": [],   # [{label, pct, dir}]  dir: bull|warn|bear
        "strategy": {"buy": [], "sell": []},  # [{label, price}]
        "scores": {"technical_daily": 0, "technical_intraday": 0, "supply": 0,
                   "fundamental": 0, "growth": 0, "total": 0},
        "simulation": {"target": "", "stop": "", "target_pct": "", "stop_pct": "",
                       "rr": "", "weight": ""},
        "probability": [],  # [{label, pct, dir}]
        "investor": {"aggressive": "", "neutral": "", "conservative": ""},
        "sentiment": "",
        "pcr_comment": "",
        # 레버리지 ETF 전용
        "etf": {"underlying_view": "", "decay_warning": "", "volatility": "", "hold_period": ""},
    }


def _merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        out = dict(base)
        for k, v in patch.items():
            out[k] = _merge(base.get(k), v) if k in base else v
        return out
    if patch is None:
        return base
    return patch


def coerce(raw: Dict[str, Any]) -> Dict[str, Any]:
    """LLM 결과를 기본 골격에 병합."""
    if not isinstance(raw, dict):
        return default_analysis()
    return _merge(default_analysis(), raw)


# 프롬프트에 넣을 JSON 형태 설명 (모델이 따라야 할 구조)
JSON_SHAPE = """{
  "conclusion": {"text": "한 줄 핵심 결론", "highlight": "강조할 한 문장"},
  "headline_metrics": {"rsi_daily_label": "예: 과매수 극단", "rsi_intraday_label": "...",
                       "macd_daily_label": "예: Strong Buy", "entry_zone": "예: $48~50", "exit_zone": "예: $62~66"},
  "daily": {"ma_short": "5·20일 이평 해석", "ma_mid": "100일", "ma_long": "200일",
            "rsi": "RSI 해석", "macd": "MACD 해석", "bollinger": "볼린저 해석",
            "resistance": "핵심 저항/지지", "summary": "일봉 종합 한 줄"},
  "intraday": {"info": "120분봉 도입 설명 1~2문장", "summary": "통합 판단 한 줄",
               "rows": {"ma":"", "rsi":"", "stoch":"", "bollinger":"", "volume":"", "macd":""}},
  "catalysts": [{"title": "호재 제목", "tag": "짧은 태그", "source": "근거 기사 제목/날짜 (없으면 '')"}],
  "risks": [{"title": "리스크", "tag": "태그", "source": "근거"}],
  "waves": [{"num": "1파", "range": "$13→$19", "desc": "설명", "current": false}],
  "scenarios": [{"label": "시나리오 설명 + 목표가", "pct": 40, "dir": "bull"}],
  "strategy": {"buy": [{"label": "1차 매수 조건", "price": "$48~50"}],
               "sell": [{"label": "분할매도", "price": "$62~66"}]},
  "scores": {"technical_daily": 70, "technical_intraday": 50, "supply": 60,
             "fundamental": 55, "growth": 75, "total": 64},
  "simulation": {"target": "$66", "stop": "$48", "target_pct": "+23%", "stop_pct": "-10%",
                 "rr": "2.3:1", "weight": "20%"},
  "probability": [{"label": "상승", "pct": 45, "dir": "bull"}, {"label": "횡보", "pct": 30, "dir": "warn"}, {"label": "하락", "pct": 25, "dir": "bear"}],
  "investor": {"aggressive": "공격투자자 전략", "neutral": "중립투자자", "conservative": "보수투자자"},
  "sentiment": "시장심리/수급 요약",
  "pcr_comment": "PCR 해석",
  "etf": {"underlying_view": "기초지수 방향(ETF만)", "decay_warning": "레버리지 소실 경고(ETF만)",
          "volatility": "변동성(ETF만)", "hold_period": "권장 보유기간(ETF만)"}
}"""
