"""Real fruit photos from Wikimedia Commons (free licences only) -> background-removed cut-outs.

  python3 tools/photos.py search <kind> "<english query>" [--n 12]
      downloads candidates to assets/photos/<kind>/cand/ and writes cand/sheet.png (numbered) — LOOK at it.
  python3 tools/photos.py pick <kind> <number>
      makes assets/photos/<kind>/main.png (cut-out, transparent) + bg.jpg (original) + meta.json (author, licence, url).
  python3 tools/photos.py list

Only CC0, Public domain and CC BY (any version) are accepted: no BY-SA, NC or ND (those would put conditions on the video).
Credit for every photo used is shown in the video finale and must be added to the caption (make.py prints it).
"""
import json, os, re, sys, html, io, glob
import urllib.request, urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "photos")
API = "https://commons.wikimedia.org/w/api.php"
UA = "kg-v-cifrah/1.0 (https://github.com/Talantbey/kg-v-cifrah; educational fruit reels)"


def get(url, binary=False, tries=5):
    import time, urllib.error
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            time.sleep(1.0)  # be polite to Wikimedia
            return data if binary else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and k < tries - 1:
                time.sleep(int(e.headers.get("Retry-After", 0) or 0) or 10 * (k + 1)); continue
            raise


def fetch(url):
    """Download an image (prefers a 1280px thumbnail on upload.wikimedia.org, falls back to the original)."""
    import subprocess, hashlib
    p = urllib.parse.urlparse(url).path  # /wikipedia/commons/a/ab/Name.jpg
    parts = p.split("/")
    tries = []
    if len(parts) >= 6 and parts[3] != "thumb":
        name = parts[-1]
        tries.append(f"https://upload.wikimedia.org/{'/'.join(parts[1:3])}/thumb/{'/'.join(parts[3:])}/1280px-{name}")
    tries.append(url)
    import time
    for u in tries:
        for k in range(4):
            r = subprocess.run(["curl", "-sS", "-L", "-m", "120", "-A", UA, "-w", "%{http_code}", "-o", "/tmp/_wm.bin", u],
                               capture_output=True, text=True)
            code = r.stdout.strip()[-3:]
            if code == "200" and os.path.getsize("/tmp/_wm.bin") > 5000:
                time.sleep(1.5)
                return open("/tmp/_wm.bin", "rb").read()
            if code != "429":
                break
            time.sleep(8 * (k + 1))
    raise RuntimeError(f"download failed: {url}")


def licence_ok(lic):
    l = (lic or "").lower().replace("-", " ").strip()
    return (l.startswith("cc0") or "public domain" in l or l.startswith("pd")
            or re.match(r"^cc by( \d(\.\d)?)?$", l) is not None)


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def search(kind, query, n=12):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
                                "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": 50, "prop": "imageinfo",
                                "iiprop": "url|extmetadata|size"})
    pages = get(f"{API}?{q}").get("query", {}).get("pages", {})
    out = []
    for pg in sorted(pages.values(), key=lambda x: x.get("index", 0)):
        ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        if not licence_ok(lic) or ii.get("width", 0) < 800:
            continue
        if ii.get("size", 0) > 15_000_000 or not urllib.parse.urlparse(ii["url"]).path.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        out.append({"title": pg["title"], "thumb": ii["url"].split("?")[0], "page": ii.get("descriptionurl"),
                    "licence": lic, "licence_url": m.get("LicenseUrl", {}).get("value", ""),
                    "author": strip_html(m.get("Artist", {}).get("value", "")) or "unknown"})
        if len(out) >= n:
            break
    cdir = os.path.join(ROOT, kind, "cand"); os.makedirs(cdir, exist_ok=True)
    for f in glob.glob(os.path.join(cdir, "*")):
        os.remove(f)
    from PIL import Image, ImageDraw
    thumbs = []
    for i, c in enumerate(out):
        print("  downloading", i + 1, c["title"][:50], flush=True); data = fetch(c["thumb"])
        p = os.path.join(cdir, f"{i + 1:02d}.jpg"); open(p, "wb").write(data)
        im = Image.open(io.BytesIO(data)).convert("RGB"); im.thumbnail((360, 360)); thumbs.append(im)
    json.dump(out, open(os.path.join(cdir, "candidates.json"), "w"), ensure_ascii=False, indent=1)
    if thumbs:
        cols = 4; rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 370, rows * 400), "white"); d = ImageDraw.Draw(sheet)
        for i, im in enumerate(thumbs):
            x, y = (i % cols) * 370 + 5, (i // cols) * 400 + 5
            sheet.paste(im, (x, y)); d.text((x + 4, y + 365), f"#{i + 1} {out[i]['licence']}", fill="black")
        sheet.save(os.path.join(cdir, "sheet.png"))
    print(f"{len(out)} candidates -> {cdir}/sheet.png")
    for i, c in enumerate(out):
        print(f"#{i + 1}", c["licence"], "|", c["author"][:40], "|", c["title"][:70])


def pick(kind, num):
    cdir = os.path.join(ROOT, kind, "cand")
    c = json.load(open(os.path.join(cdir, "candidates.json")))[int(num) - 1]
    src = os.path.join(cdir, f"{int(num):02d}.jpg")
    from PIL import Image
    from rembg import remove, new_session
    im = Image.open(src).convert("RGB")
    cut = remove(im, session=new_session("isnet-general-use"))
    bbox = cut.getbbox()
    if bbox:
        pad = 12
        cut = cut.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(cut.width, bbox[2] + pad), min(cut.height, bbox[3] + pad)))
    cut.thumbnail((1000, 1000))
    d = os.path.join(ROOT, kind)
    cut.save(os.path.join(d, "main.png"), optimize=True)
    bg = im.copy(); bg.thumbnail((1400, 1400)); bg.save(os.path.join(d, "bg.jpg"), quality=86)
    meta = {k: c[k] for k in ("title", "page", "licence", "licence_url", "author")}
    who = meta["author"] if meta["author"].lower() not in ("unknown", "") else ""
    meta["credit"] = (f"{who} / " if who else "") + f"Wikimedia Commons, {meta['licence']}"
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), ensure_ascii=False, indent=1)
    for f in glob.glob(os.path.join(cdir, "*")):
        os.remove(f)
    os.rmdir(cdir)
    print("ok ->", os.path.join(d, "main.png"), "|", meta["credit"])


def credit(kind):
    f = os.path.join(ROOT, kind, "meta.json")
    return json.load(open(f))["credit"] if os.path.exists(f) else None


def has_photo(kind):
    return os.path.exists(os.path.join(ROOT, kind, "main.png"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "search":
        n = int(a[a.index("--n") + 1]) if "--n" in a else 12
        search(a[1], a[2], n)
    elif a and a[0] == "pick":
        pick(a[1], a[2])
    elif a and a[0] == "list":
        for d in sorted(glob.glob(os.path.join(ROOT, "*", "meta.json"))):
            print(os.path.basename(os.path.dirname(d)), "|", json.load(open(d))["credit"])
    else:
        print(__doc__)
