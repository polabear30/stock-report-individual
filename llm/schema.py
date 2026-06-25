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
                     "rows": {"ma": "", "rsi": "", "stoch": "", "bollinger": "", "volume": "", "macd": ""},
                     "criteria": {"rsi": "", "stoch": "", "bollinger": "", "macd": "", "entry": ""},
                     "combined": {"daily": "", "intraday": ""}},
        "entry_timeline": {
            "phase": "wait", "phase_label": "",
            "target_rsi": 30,
            "steps": [],   # [{title, desc, date, level(bear|warn|bull)}]
            "window": {"date": "", "price": "", "note": ""},
        },
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
        "investor": [],   # [{type, verdict, verdict_dir(bull|warn|bear), detail}]
        "sentiment_detail": {
            "retail": "", "retail_dir": "warn",
            "insider": "", "summary": "", "deadline": "",
        },
        "reliability": {"stars": 3, "note": ""},
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
               "rows": {"ma":"이동평균 신호", "rsi":"RSI 신호", "stoch":"스토캐스틱", "bollinger":"볼린저", "volume":"거래량", "macd":"MACD"},
               "criteria": {"rsi":"RSI 진입 기준", "stoch":"스토캐스틱 기준", "bollinger":"볼린저 기준", "macd":"MACD 기준", "entry":"예상 진입 타이밍(가격/시기)"},
               "combined": {"daily":"일봉 한 줄 요약", "intraday":"120분봉 한 줄 요약"}},
  "entry_timeline": {"phase":"wait|imminent|enter 중 하나", "phase_label":"예: 조정 대기 / 진입 임박",
    "target_rsi": 30,
    "steps": [{"title":"📍 현재 — RSI ... 단계", "desc":"근거 설명", "date":"예: 4/23 현재 또는 날짜범위", "level":"bear|warn|bull"}],
    "window": {"date":"예상 진입 윈도우(날짜범위)", "price":"예상 진입 가격대 $..~$..", "note":"⚠ 진입 필수 확인 조건"}},
  "catalysts": [{"title": "호재 제목", "tag": "짧은 태그", "source": "근거 기사 제목/날짜 (없으면 '')"}],
  "risks": [{"title": "리스크", "tag": "태그", "source": "근거"}],
  "waves": [{"num": "1파", "range": "$13→$19", "desc": "설명", "current": false}],
  "scenarios": [{"label": "시나리오 설명 + 목표가", "pct": "<확률 정수, 3개 합 100>", "dir": "bull"}],
  "strategy": {"buy": [{"label": "1차 매수 조건", "price": "$48~50"}],
               "sell": [{"label": "분할매도", "price": "$62~66"}]},
  "scores": {"technical_daily": "<0~100 정수, 데이터로 산출>", "technical_intraday": "<0~100>", "supply": "<0~100>",
             "fundamental": "<0~100>", "growth": "<0~100>", "total": "<5개 평균 근처 0~100, 종목마다 다르게>"},
  "simulation": {"target": "<목표가 $>", "stop": "<손절가 $>", "target_pct": "<+%>", "stop_pct": "<-%>",
                 "rr": "<손익비 예 1.8:1>", "weight": "<권장비중 %>"},
  "probability": [{"label": "상승", "pct": "<정수>", "dir": "bull"}, {"label": "횡보", "pct": "<정수>", "dir": "warn"}, {"label": "하락", "pct": "<정수, 합100>", "dir": "bear"}],
  "investor": [{"type":"신규 진입자", "verdict":"예: 지금 금지", "verdict_dir":"bull|warn|bear", "detail":"상세 전략"},
               {"type":"기존 보유자", "verdict":"", "verdict_dir":"warn", "detail":""},
               {"type":"장기 투자자", "verdict":"", "verdict_dir":"bull", "detail":""}],
  "sentiment_detail": {"retail":"개인/소매 심리 한 줄(예: Extremely Bullish · 언급량 급증)", "retail_dir":"bull|warn|bear",
    "insider":"내부자 동향(뉴스 근거 또는 '공개 정보 없음')", "summary":"심리 요약 한 줄(개인 vs 월가 vs 내부자)",
    "deadline":"주요 이슈 데드라인(예: FDA 일정, 정책 이벤트)"},
  "reliability": {"stars":"1~5 정수(데이터/뉴스 충분도)", "note":"신뢰도 코멘트 한 줄"},
  "sentiment": "시장심리/수급 요약(보조)",
  "pcr_comment": "PCR 종합 해석(반드시 작성)",
  "etf": {"underlying_view": "기초지수 방향(ETF만)", "decay_warning": "레버리지 소실 경고(ETF만)",
          "volatility": "변동성(ETF만)", "hold_period": "권장 보유기간(ETF만)"}
}"""
