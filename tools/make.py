"""Build a video from an episode folder.

  python3 tools/make.py episodes/2026-11-13            # full render -> episodes/<d>/video.mp4
  python3 tools/make.py episodes/2026-11-13 --stills   # only key frames -> episodes/<d>/stills/*.png + sheet.png

episode.json: {"header": "...", "speed": 0.84, "caption": "...", "scenes": [{"type": ..., "parts": [[tts, sub], ...], ...}]}
"""
import json, os, sys, wave, subprocess
from multiprocessing import Pool
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E

VOICE = os.environ.get("KG_VOICE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice", "ru-irinia-medium.onnx"))


def tts(ep, outdir):
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    voice = PiperVoice.load(VOICE)
    cfg = SynthesisConfig(length_scale=float(ep.get("speed", 0.84)), noise_scale=0.6, noise_w_scale=0.7)
    sr = voice.config.sample_rate
    timing = []
    for i, sc in enumerate(ep["scenes"]):
        text = " ".join(pt[0] for pt in sc["parts"])
        pcs = []
        for ch in voice.synthesize(text, syn_config=cfg):
            pcs.append(np.frombuffer(ch.audio_int16_bytes, dtype=np.int16))
            pcs.append(np.zeros(int(sr * 0.14), np.int16))
        audio = np.concatenate(pcs)
        with wave.open(os.path.join(outdir, f"scene{i:02d}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(audio.tobytes())
        dur = len(audio) / sr
        lens = [max(1, len(pt[0])) for pt in sc["parts"]]; tot = sum(lens); t = 0; parts = []
        for pt, L in zip(sc["parts"], lens):
            d = dur * L / tot; parts.append([round(t, 3), round(t + d, 3), pt[1] if len(pt) > 1 else pt[0]]); t += d
        timing.append({"dur": round(dur, 3), "parts": parts, "sr": sr})
    json.dump(timing, open(os.path.join(outdir, "timing.json"), "w"), ensure_ascii=False, indent=1)
    return timing


def offsets(ep, timing):
    offs, acc = [], 0.0
    for sc, tm in zip(ep["scenes"], timing):
        offs.append(acc); acc += E.scene_dur(sc, tm)
    return offs, acc


def _job(args):
    ep, i, timing, offs, outdir = args
    E.render_scene(ep, i, timing, offs, outdir)
    return i


def main():
    epdir = sys.argv[1]; stills = "--stills" in sys.argv; reuse = "--reuse-audio" in sys.argv
    ep = json.load(open(os.path.join(epdir, "episode.json")))
    work = os.path.join(epdir, "build"); os.makedirs(work, exist_ok=True)
    tpath = os.path.join(work, "timing.json")
    timing = json.load(open(tpath)) if (reuse and os.path.exists(tpath)) else tts(ep, work)
    offs, total = offsets(ep, timing)
    print("scene durations:", [round(E.scene_dur(s, t), 2) for s, t in zip(ep["scenes"], timing)], "total", round(total, 2))
    if stills:
        sd = os.path.join(epdir, "stills"); os.makedirs(sd, exist_ok=True)
        from PIL import Image
        ims = []
        for i, (sc, tm) in enumerate(zip(ep["scenes"], timing)):
            T = E.scene_dur(sc, tm); t = max(0.0, T - 0.6)
            f = os.path.join(sd, f"scene{i:02d}.png")
            E.draw(ep, i, t, timing, offs).write_to_png(f); ims.append(Image.open(f).convert("RGB"))
        cols = 4; rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (540 * cols, 960 * rows), "black")
        for k, im in enumerate(ims):
            sheet.paste(im.resize((540, 960)), ((k % cols) * 540, (k // cols) * 960))
        sheet.save(os.path.join(sd, "sheet.png")); print("stills ->", sd)
        return
    n = len(ep["scenes"])
    with Pool(min(4, os.cpu_count() or 2)) as pool:
        for i in pool.imap_unordered(_job, [(ep, i, timing, offs, work) for i in range(n)]):
            print("scene", i, "ok", flush=True)
    # narration track aligned to scene frame boundaries
    sr = timing[0]["sr"]; chunks = []
    for i, (sc, tm) in enumerate(zip(ep["scenes"], timing)):
        nfr = round(E.scene_dur(sc, tm) * E.FPS); total_s = int(round(nfr / E.FPS * sr))
        with wave.open(os.path.join(work, f"scene{i:02d}.wav")) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        buf = np.zeros(total_s, np.int16); st = int(E.LEAD * sr); L = min(len(a), total_s - st); buf[st:st + L] = a[:L]
        chunks.append(buf)
    with wave.open(os.path.join(work, "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.concatenate(chunks).tobytes())
    with open(os.path.join(work, "list.txt"), "w") as f:
        for i in range(n):
            f.write(f"file 'scene{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "list.txt"),
                    "-c", "copy", os.path.join(work, "video_only.mp4")], check=True)
    tmp = os.path.join(epdir, "video.tmp.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(work, "video_only.mp4"), "-i", os.path.join(work, "voice.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000",
                    "-ac", "2", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", tmp], check=True)
    os.replace(tmp, os.path.join(epdir, "video.mp4"))
    print("video ->", os.path.join(epdir, "video.mp4"), round(total, 2), "s")


if __name__ == "__main__":
    main()
