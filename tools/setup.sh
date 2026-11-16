#!/usr/bin/env bash
# One-time setup per fresh environment: Python deps + Russian Piper voice.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q pycairo piper-tts numpy pillow 2>&1 | grep -v -i "warning" || true
mkdir -p voice
# Main voice: Ruslan (male). Pinned mirror of rhasspy/piper-voices ru_RU-ruslan-medium.
RUSLAN=https://media.githubusercontent.com/media/moonshine-ai/moonshine-tts/dba0b7cb5857ff4b0a08fad47f6fbb8630a3ca70/data/ru/piper-voices
for f in ru_RU-ruslan-medium.onnx ru_RU-ruslan-medium.onnx.json; do
  min=1000; [ "${f##*.}" = "onnx" ] && min=1000000
  if [ ! -f voice/$f ] || [ $(stat -c%s voice/$f) -lt $min ]; then
    curl -sSL -m 300 -o voice/$f $RUSLAN/$f
  fi
done
[ $(stat -c%s voice/ru_RU-ruslan-medium.onnx 2>/dev/null || echo 0) -gt 1000000 ] || rm -f voice/ru_RU-ruslan-medium.onnx*
# Fallback voice (female), used only if Ruslan can't be downloaded.
if [ ! -f voice/ru_RU-ruslan-medium.onnx ] && [ ! -f voice/ru-irinia-medium.onnx ]; then
  curl -sSL -m 300 -o voice/v.tgz https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-ru-irinia-medium.tar.gz
  tar xzf voice/v.tgz -C voice && rm voice/v.tgz
fi
which ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
fc-list | grep -qi "Inter" || echo "WARN: Inter font missing, fallback font will be used"
python3 -c "import cairo, piper; print('setup ok')"
