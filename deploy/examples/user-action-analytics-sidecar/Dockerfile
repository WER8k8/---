FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless maven curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py mysql_repo.py task_runner.py ./

ENV USER_ACTION_ANALYTICS_REPO=/opt/UserActionAnalyzePlatform
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

EXPOSE 8093
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8093"]
