#!/usr/bin/env bash
# One-time setup per fresh environment: Python deps + Russian Piper voice.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q pycairo piper-tts numpy pillow 2>&1 | grep -v -i "warning" || true
mkdir -p voice
if [ ! -f voice/ru-irinia-medium.onnx ]; then
  curl -sSL -m 300 -o voice/v.tgz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-ru-irinia-medium.tar.gz
  tar xzf voice/v.tgz -C voice && rm voice/v.tgz
fi
which ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
fc-list | grep -qi "Inter" || echo "WARN: Inter font missing, fallback font will be used"
python3 -c "import cairo, piper; print('setup ok')"
