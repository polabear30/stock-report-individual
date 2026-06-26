"""개별 종목 AI 분석 리포트 생성 오케스트레이터

종목별: 시세·지표 수집(재시도) → 뉴스 수집 → AI 분석(OpenAI/Anthropic, 또는 모의) → 렌더 → HTML.

사용법:
    python generate.py --out _site/index.html
    python generate.py --mock                 # 키 없이 디자인 검증(모의 AI)
    python generate.py --only IONQ --mock
    python generate.py --provider anthropic
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from fetch.market import fetch_stock_data
from fetch.news import fetch_news
from llm.client import generate_analysis
from render.template import render_report

KST = timezone(timedelta(hours=9))


def _retry(fn, validate, attempts=3, delay=3):
    result = None
    for i in range(attempts):
        try:
            result = fn()
        except Exception:
            result = None
        try:
            if result is not None and validate(result):
                return result, True
        except Exception:
            pass
        if i < attempts - 1:
            time.sleep(delay)
    return result, False


def build(only=None, mock=False, provider=None):
    """리포트 HTML과 수집 상태를 생성해 (doc, status)로 반환한다.

    CLI(main)와 Cloud Run Job(run_job)이 공유하는 오케스트레이션 코어.
    """
    tickers = config.TICKERS
    if only:
        want = {t.strip().upper() for t in only.split(",")}
        tickers = [t for t in tickers if t["ticker"] in want]

    panels = []
    status = {}
    for meta in tickers:
        tk = meta["ticker"]
        print(f"[{tk}] 시세·지표 수집…")
        market, ok = _retry(lambda: fetch_stock_data(tk),
                            lambda r: bool(r.get("daily")))
        status[f"{tk}·데이터"] = ok

        print(f"[{tk}] 뉴스 수집…")
        news = fetch_news(tk) if not mock else {"articles": []}

        print(f"[{tk}] AI 분석 생성… ({'모의' if mock else (provider or os.environ.get('LLM_PROVIDER','openai'))})")
        context = {"meta": meta, "market": market or {}, "news": news}
        analysis = generate_analysis(context, meta["type"], provider=provider, mock=mock)
        status[f"{tk}·AI"] = "_error" not in analysis

        panels.append({"meta": meta, "market": market or {}, "analysis": analysis})

    gen = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    doc = render_report(panels, gen, status)
    return doc, status


def main():
    ap = argparse.ArgumentParser(description="개별 종목 AI 분석 리포트 생성")
    ap.add_argument("--out", default="_site/index.html")
    ap.add_argument("--status-out", default="status.json")
    ap.add_argument("--mock", action="store_true", help="키 없이 모의 AI로 렌더 검증")
    ap.add_argument("--only", default=None, help="특정 티커만 (콤마 구분)")
    ap.add_argument("--provider", default=None, help="openai | anthropic")
    args = ap.parse_args()

    doc, status = build(only=args.only, mock=args.mock, provider=args.provider)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(doc)
    with open(args.status_out, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False)

    failed = [k for k, v in status.items() if not v]
    print(f"\n생성 완료: {args.out} ({os.path.getsize(args.out):,} bytes)")
    print(f"  상태: {status}")
    if failed:
        print(f"  ⚠ 실패: {', '.join(failed)}")


if __name__ == "__main__":
    main()
