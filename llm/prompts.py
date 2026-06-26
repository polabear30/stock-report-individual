"""그라운딩 프롬프트 — 제공된 사실만 근거, 날조 금지"""

from __future__ import annotations

import json
from typing import Any, Dict

from llm.schema import JSON_SHAPE

SYSTEM = """당신은 신중한 미국주식 애널리스트다. 반드시 아래 원칙을 지킨다.
1) 제공된 '데이터'와 '뉴스'에 근거해서만 분석한다. 제공되지 않은 사건·수치·날짜·목표가를 절대 지어내지 않는다.
2) 카탈리스트/리스크는 제공된 뉴스 기사에서만 도출하고, 각 항목의 source에 근거 기사 제목/날짜를 적는다.
   관련 뉴스가 없으면 catalysts/risks를 비우거나 "최근 특이 뉴스 없음"으로 적는다(허구 금지).
3) 기술적 해석은 제공된 지표 수치에 근거한다.
4) 시나리오·확률·엘리어트 파동·목표가는 '추정'임을 전제로 보수적으로 제시한다.
5) 출력은 지정된 JSON 한 개만. 다른 텍스트·마크다운·코드펜스 없이 순수 JSON."""

STOCK_TASK = """대상은 '단일 종목'이다. 어닝·애널리스트 목표가·펀더멘털을 활용한다.
catalysts/risks는 뉴스 기반, scores의 fundamental/growth는 제공된 펀더멘털·애널리스트 데이터에 근거."""

ETF_TASK = """대상은 '3배 레버리지 ETF'다. 다음을 반드시 반영한다.
- 어닝·애널리스트 목표가·내부자매매·펀더멘털 점수는 해당 없음(scores.fundamental은 N/A 의미로 낮게/0, 또는 기초지수 추세로 대체).
- etf.underlying_view(기초지수 방향), etf.decay_warning(일일 리밸런싱·변동성 소실), etf.volatility, etf.hold_period(장기보유 부적합 경고)를 반드시 채운다.
- catalysts/risks는 '기초지수(섹터/국가) 동인'과 '레버리지 구조 위험' 중심으로, 뉴스가 있으면 근거 연결."""


def build_messages(context: Dict[str, Any], ticker_type: str) -> Dict[str, str]:
    task = ETF_TASK if ticker_type == "etf_leveraged" else STOCK_TASK
    user = f"""[종목 메타]
{json.dumps(context.get('meta', {}), ensure_ascii=False)}

[시세·기술지표 데이터]
{json.dumps(context.get('market', {}), ensure_ascii=False, default=str)}

[최근 뉴스 (그라운딩 근거 — 이 기사들만 카탈리스트/리스크 근거로 사용)]
{json.dumps(context.get('news', {}).get('articles', []), ensure_ascii=False)[:6000]}

[작업 지시]
{task}

[120분봉 RSI 핵심 시그널 — 반드시 이 관점으로 분석]
- market.intraday_120m.rsi_series(최근 20봉 RSI)를 근거로 120분봉 분석·결론을 작성한다.
- RSI가 30 이하를 '터치 후 반등'하면 매수 시그널, 70 이상을 '터치 후 하락'하면 매도 시그널로 해석한다.
- 현재 RSI 값뿐 아니라 '최근 저점/고점을 찍고 올라가는지/내려가는지(방향)'를 중심으로 서술한다.
- intraday.rows/criteria/combined, conclusion, scenarios가 이 RSI 시그널과 모순되지 않게 한다.

위 데이터/뉴스에만 근거해, 아래 JSON 구조에 맞춰 한국어로 채워라.

[완결성 규칙 — 빈 칸 금지]
- 모든 필드를 채운다. waves 정확히 5개(엘리어트 1~5파를 빠짐없이; current=true는 현재 진행 파동 정확히 1개),
  scenarios 3개(pct 합=100), probability 3개(pct 합=100),
  strategy.buy 정확히 4개·strategy.sell 정확히 4개(가격대별 분할로 빠짐없이), entry_timeline.steps 정확히 4개(현재→1차→2차→진입구간),
  investor 3개(신규/보유/장기), pcr_comment 필수 작성.
- entry_timeline은 120분봉 RSI가 목표(보통 30)까지 가는 단계별 예상 경로를 단계마다 RSI·가격·소요 캔들 추정으로.
- 숫자 점수(scores, *.pct, target_rsi, reliability.stars)는 정수. dir/level/verdict_dir은 bull|warn|bear 중 하나.
- 예시에 적힌 숫자(예: 64, 40)를 그대로 복사하지 말고, 데이터에 근거해 종목마다 다르게 산출.
- 근거가 약한 항목도 비우지 말고 보수적으로 기술(단, 없는 사건·수치는 날조 금지).
순수 JSON만 출력:

{JSON_SHAPE}"""
    return {"system": SYSTEM, "user": user}
