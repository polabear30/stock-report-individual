# 개별 종목 AI 분석 리포트 Cloud Run Job 이미지
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 의존성 먼저 설치(레이어 캐시)
COPY requirements-job.txt .
RUN pip install --no-cache-dir -r requirements-job.txt

# 애플리케이션 코드 — Job에 필요한 모듈만 명시적으로 복사.
# (레포 전체 COPY 시 비-ASCII 경로가 레이어에 섞여 Cloud Run의
#  컨테이너 import가 실패하는 문제가 있어 화이트리스트 방식 사용)
COPY run_job.py generate.py config.py ./
COPY fetch/ ./fetch/
COPY llm/ ./llm/
COPY render/ ./render/

# 배치: 실행 후 종료
CMD ["python", "run_job.py"]
