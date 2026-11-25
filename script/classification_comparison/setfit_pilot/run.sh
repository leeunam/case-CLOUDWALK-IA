#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cache="$here/.cache"
mkdir -p "$cache/tmp"
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN FEITA_API_KEY TYPESAFE_API_KEY
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_HOME="$cache/hf" XDG_CACHE_HOME="$cache/xdg" TORCH_HOME="$cache/torch"
export HF_HUB_CACHE="$HF_HOME/hub" HF_DATASETS_CACHE="$HF_HOME/datasets"
export TMPDIR="$cache/tmp" TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2
exec python3 -B "$here/supervise.py" train "$@"
