FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 bridge
COPY agent_flow.py .
ENV PYTHONUNBUFFERED=1
USER bridge
ENTRYPOINT ["python", "/app/agent_flow.py"]
