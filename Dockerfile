# 베이스 이미지
FROM python:3.12-slim

# 작업 디렉터리 생성 및 이동
WORKDIR /app

# 소스 코드 복사
COPY requirements.txt .

# 필요한 패키지 설치 (필요 시 requirements.txt로 대체 가능)
RUN pip install --no-cache-dir -r requirements.txt

# source
COPY src/ ./src/
ENV PYTHONPATH=/app/src

# 기본 실행 명령어 (인자는 Kaniko 쪽에서 지정하므로 여기서는 생략하거나 디폴트 설정만)
ENTRYPOINT ["python3", "-m", "collector.rss_collector"]
