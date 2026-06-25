"""Alpha Vantage NEWS_SENTIMENT — 종목별 최근 뉴스/감성 수집

카탈리스트·리스크의 '그라운딩 근거'로 사용된다. LLM은 여기서 받은 실제 기사만
근거로 삼아야 하며, 뉴스가 없으면 카탈리스트를 지어내선 안 된다.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

_URL = "https://www.alphavantage.co/query"


def fetch_news(ticker: str, limit: int = 12, api_key: Optional[str] = None) -> Dict[str, Any]:
    """종목 관련 최근 뉴스와 감성을 반환한다.

    반환: {"ticker", "articles": [{title, summary, source, time, url,
            overall_sentiment, ticker_sentiment_score, ticker_sentiment_label}], "error"}
    """
    api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {"ticker": ticker, "articles": [], "error": "ALPHA_VANTAGE_API_KEY 없음"}

    try:
        resp = requests.get(_URL, params={
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": limit,
            "sort": "LATEST",
            "apikey": api_key,
        }, timeout=20)
        data = resp.json()
    except Exception as e:
        return {"ticker": ticker, "articles": [], "error": str(e)}

    # 무료 한도 초과 시 'Note'/'Information' 메시지가 옴
    if "feed" not in data:
        msg = data.get("Information") or data.get("Note") or data.get("Error Message") or str(data)[:200]
        return {"ticker": ticker, "articles": [], "error": msg}

    articles: List[Dict[str, Any]] = []
    for item in data["feed"][:limit]:
        tsent = {}
        for ts in item.get("ticker_sentiment", []):
            if ts.get("ticker") == ticker:
                tsent = ts
                break
        articles.append({
            "title": item.get("title"),
            "summary": (item.get("summary") or "")[:400],
            "source": item.get("source"),
            "time": item.get("time_published", "")[:8],  # YYYYMMDD
            "url": item.get("url"),
            "overall_sentiment": item.get("overall_sentiment_label"),
            "ticker_sentiment_score": _f(tsent.get("ticker_sentiment_score")),
            "ticker_sentiment_label": tsent.get("ticker_sentiment_label"),
        })

    return {"ticker": ticker, "articles": articles, "error": None}


def _f(v):
    try:
        return round(float(v), 3)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    import json
    import sys
    tk = sys.argv[1] if len(sys.argv) > 1 else "IONQ"
    print(json.dumps(fetch_news(tk), ensure_ascii=False, indent=2))
