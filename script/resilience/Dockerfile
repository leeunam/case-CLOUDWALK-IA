FROM python:3.13-slim
COPY --from=product requirements.txt /tmp/product-requirements.txt
COPY requirements.txt /tmp/probe-requirements.txt
RUN pip install --no-cache-dir -r /tmp/product-requirements.txt -r /tmp/probe-requirements.txt
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/product
