"""대상 종목 및 설정"""

from __future__ import annotations

# 종목 정의
# type: "stock"(단일주) | "etf_leveraged"(레버리지 ETF)
TICKERS = [
    {"ticker": "IONQ", "type": "stock", "name": "IonQ", "sector": "양자컴퓨팅"},
    {"ticker": "EOSE", "type": "stock", "name": "Eos Energy", "sector": "에너지저장(ESS)"},
    {"ticker": "OKLO", "type": "stock", "name": "Oklo", "sector": "소형모듈원전(SMR)"},
    {"ticker": "SOXL", "type": "etf_leveraged", "name": "Direxion 반도체 불 3X",
     "underlying": "미국 반도체(ICE Semiconductor Index)", "leverage": 3},
    {"ticker": "KORU", "type": "etf_leveraged", "name": "Direxion 한국 불 3X",
     "underlying": "한국 증시(MSCI Korea 25/50)", "leverage": 3},
]

# 보고서 메타
REPORT_TITLE = "미국주식 개별 종목 AI 분석"
REPORT_SUBTITLE = "Individual Equity AI Analysis"

# LLM provider: "openai"(기본) | "anthropic"(폴백) — 환경변수 LLM_PROVIDER로 덮어씀
DEFAULT_LLM_PROVIDER = "openai"
