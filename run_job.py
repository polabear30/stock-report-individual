"""Cloud Run Job 엔트리포인트 — 개별 종목 AI 분석 리포트 생성·게시

GitHub Actions를 대체한다. 한 번 실행되고 종료되는 배치(Job)다.

흐름:
    1) generate.build()  로 리포트 HTML + 수집 상태(status) 생성
       (종목별 시세·지표 → 뉴스 → LLM 분석 → 렌더)
    2) Cloud Storage 공개 버킷에 index.html 업로드 (매일 같은 URL, 내용만 갱신)

환경변수:
    GCS_BUCKET            — 업로드 대상 버킷명 (필수)
    GCS_OBJECT            — 오브젝트 경로 (기본 index.html)
    LLM_PROVIDER          — openai(기본) | anthropic
    OPENAI_API_KEY        — provider=openai 일 때 필요
    ANTHROPIC_API_KEY     — provider=anthropic 일 때 필요
    ALPHA_VANTAGE_API_KEY — 뉴스 그라운딩
    MOCK                  — "1"/"true" 면 키 없이 모의 AI로 생성(인프라 검증용)

로컬 테스트:
    python run_job.py --mock --no-upload --out _site/index.html
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate import build  # noqa: E402


def upload_to_gcs(bucket_name: str, object_name: str, html: str) -> str:
    """HTML을 GCS 버킷에 업로드하고 공개 URL을 반환한다."""
    from google.cloud import storage

    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    blob.cache_control = "no-cache, max-age=0"
    blob.upload_from_string(html, content_type="text/html; charset=utf-8")
    return f"https://storage.googleapis.com/{bucket_name}/{object_name}"


def main() -> int:
    ap = argparse.ArgumentParser(description="개별 종목 AI 리포트 Job")
    ap.add_argument("--no-upload", action="store_true", help="GCS 업로드 생략(로컬 테스트)")
    ap.add_argument("--mock", action="store_true", help="키 없이 모의 AI로 생성")
    ap.add_argument("--only", default=None, help="특정 티커만 (콤마 구분)")
    ap.add_argument("--out", default=None, help="로컬 HTML 저장 경로(선택)")
    args = ap.parse_args()

    mock = args.mock or os.environ.get("MOCK", "").lower() in ("1", "true", "yes")

    print(f"[1/2] 리포트 생성 중… (mock={mock})")
    doc, status = build(only=args.only, mock=mock)
    failed = [k for k, v in status.items() if not v]
    print(f"      생성 완료 ({len(doc):,} bytes) · 상태: {status}")
    if failed:
        print(f"      ⚠ 실패: {', '.join(failed)}")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"      로컬 저장: {args.out}")

    if args.no_upload:
        print("[2/2] 업로드 생략(--no-upload)")
        return 0

    bucket = os.environ.get("GCS_BUCKET")
    if not bucket:
        print("[2/2] ✗ GCS_BUCKET 환경변수가 없습니다.", file=sys.stderr)
        return 1
    obj = os.environ.get("GCS_OBJECT", "index.html")
    print(f"[2/2] GCS 업로드 중… gs://{bucket}/{obj}")
    url = upload_to_gcs(bucket, obj, doc)
    print(f"      게시 URL: {url}")
    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
