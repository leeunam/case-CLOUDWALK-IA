FROM python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY script/classification_comparison/setfit_sf2/serving/requirements-linux-amd64.lock /tmp/requirements.lock
RUN python -m pip --isolated install --no-cache-dir --only-binary=:all: --require-hashes --index-url https://pypi.org/simple -r /tmp/requirements.lock && python -m pip check
COPY . .
ENV HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false HF_HOME=/tmp/huggingface
USER 65534:65534
CMD ["python", "-B", "-m", "script.classification_comparison.setfit_sf2.serving"]
