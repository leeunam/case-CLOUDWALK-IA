FROM python:3.13.7-slim
COPY requirements.txt /tmp/f08-requirements.txt
RUN pip install --no-cache-dir -r /tmp/f08-requirements.txt
ENV PYTHONUNBUFFERED=1
