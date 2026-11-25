"""Fresh theme (episode "theme": "fresh") for fruit episodes: vector fruits and scenes
fruit (hero + hook), nutrients (2x2 stat tiles), myth (миф/факт stamp), compare (bars with fruit icons),
caution (who should be careful), finale (subscribe + source + disclaimer). Generic scenes (list, fact, bars,
counter, donut) also work in this theme.
"""
import math, random
import cairo
import engine as E
from engine import p, eo, eob, clamp, text, wrap, fit, tw, rrect, fill, hexc, font
import tech

CREAM = "#FFF8EE"


# ---------------- drawing helpers ----------------

def shade(ctx, light, base, dark, cx, cy, r):
    g = cairo.RadialGradient(cx - r * 0.35, cy - r * 0.4, r * 0.05, cx, cy, r * 1.15)
    g.add_color_stop_rgb(0, *hexc(light)[:3]); g.add_color_stop_rgb(0.45, *hexc(base)[:3]); g.add_color_stop_rgb(1, *hexc(dark)[:3])
    ctx.set_source(g); ctx.fill_preserve()
    ctx.set_source_rgba(0, 0, 0, 0.18); ctx.set_line_width(max(1.5, r * 0.02)); ctx.stroke()


def spec(ctx, x, y, rx, ry, a=0.35, rot=-0.5):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(1, 1, 1, a); ctx.fill()


def leaf(ctx, x, y, L, ang, color="#4CAF50", dark="#2E7D32"):
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
    ctx.move_to(0, 0); ctx.curve_to(L * 0.3, -L * 0.32, L * 0.75, -L * 0.3, L, 0)
    ctx.curve_to(L * 0.75, L * 0.3, L * 0.3, L * 0.32, 0, 0); ctx.close_path()
    g = cairo.LinearGradient(0, -L * 0.3, 0, L * 0.3)
    g.add_color_stop_rgb(0, *hexc(color)[:3]); g.add_color_stop_rgb(1, *hexc(dark)[:3])
    ctx.set_source(g); ctx.fill()
    ctx.move_to(L * 0.08, 0); ctx.line_to(L * 0.85, 0); ctx.set_source_rgba(1, 1, 1, 0.35); ctx.set_line_width(max(1, L * 0.04)); ctx.stroke()
    ctx.restore()


def stem(ctx, x0, y0, x1, y1, w, color="#6D4C2F"):
    ctx.move_to(x0, y0); ctx.curve_to(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, x1, y1)
    ctx.set_source_rgba(*hexc(color)); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def round_fruit(ctx, r, light, base, dark, squash=1.0):
    ctx.save(); ctx.scale(1, squash); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
    shade(ctx, light, base, dark, 0, 0, r)


def apple_path(ctx, r):
    ctx.move_to(0, -r * 0.62)
    ctx.curve_to(r * 0.5, -r * 1.02, r * 1.08, -r * 0.62, r * 0.98, r * 0.05)
    ctx.curve_to(r * 0.92, r * 0.72, r * 0.45, r * 1.02, 0, r * 0.84)
    ctx.curve_to(-r * 0.45, r * 1.02, -r * 0.92, r * 0.72, -r * 0.98, r * 0.05)
    ctx.curve_to(-r * 1.08, -r * 0.62, -r * 0.5, -r * 1.02, 0, -r * 0.62); ctx.close_path()


def citrus_half(ctx, r, rind, rind_d, pulp, pulp_d, segs=10):
    ctx.arc(0, 0, r, 0, 2 * math.pi); shade(ctx, rind, rind, rind_d, 0, 0, r)
    ctx.arc(0, 0, r * 0.9, 0, 2 * math.pi); ctx.set_source_rgb(*hexc("#FFF6DC")[:3]); ctx.fill()
    for i in range(segs):
        a0 = 2 * math.pi * i / segs + 0.04; a1 = 2 * math.pi * (i + 1) / segs - 0.04
        ctx.move_to(math.cos((a0 + a1) / 2) * r * 0.1, math.sin((a0 + a1) / 2) * r * 0.1)
        ctx.arc(0, 0, r * 0.84, a0, a1); ctx.close_path()
        g = cairo.RadialGradient(0, 0, r * 0.1, 0, 0, r * 0.84)
        g.add_color_stop_rgb(0, *hexc(pulp)[:3]); g.add_color_stop_rgb(1, *hexc(pulp_d)[:3])
        ctx.set_source(g); ctx.fill()
    spec(ctx, -r * 0.35, -r * 0.4, r * 0.25, r * 0.12, 0.25)


# ---------------- real photos (assets/photos/<kind>/main.png, see tools/photos.py) ----------------
import os, io
PHOTO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "photos")
_SURF = {}


def photos_on():
    return E.THEME in ("fresh", "splash") and E.CURRENT_EP.get("photos", True)


def photo_path(kind, name="main.png"):
    p = os.path.join(PHOTO_DIR, kind, name)
    return p if os.path.exists(p) else None


def photo_surface(kind):
    if kind not in _SURF:
        p = photo_path(kind)
        _SURF[kind] = cairo.ImageSurface.create_from_png(p) if p else None
    return _SURF[kind]


def bg_surface(kind):
    key = "bg:" + kind
    if key not in _SURF:
        p = photo_path(kind, "bg.jpg")
        if not p:
            _SURF[key] = None
        else:
            from PIL import Image, ImageFilter, ImageEnhance
            im = Image.open(p).convert("RGB")
            sc = max(E.W / im.width, E.H / im.height) * 1.12
            im = im.resize((int(im.width * sc), int(im.height * sc)))
            l, t = (im.width - int(E.W * 1.12)) // 2, (im.height - int(E.H * 1.12)) // 2
            im = im.crop((l, t, l + int(E.W * 1.12), t + int(E.H * 1.12))).filter(ImageFilter.GaussianBlur(22))
            im = ImageEnhance.Brightness(im).enhance(0.55)
            buf = io.BytesIO(); im.save(buf, "PNG"); buf.seek(0)
            _SURF[key] = cairo.ImageSurface.create_from_png(buf)
    return _SURF[key]


def draw_photo(ctx, kind, cx, cy, s, a=1.0):
    xx, yx, xy, yy, _, _ = ctx.get_matrix()
    if a <= 0.001 or s <= 1 or abs(xx * yy - yx * xy) < 1e-6:
        return
    surf = photo_surface(kind)
    w, h = surf.get_width(), surf.get_height()
    k = s * 1.1 / max(w, h)
    # soft contact shadow
    sy = cy + h * k / 2 * 0.95
    ctx.save(); ctx.translate(cx, sy); ctx.scale(w * k * 0.42, h * k * 0.07)
    rg = cairo.RadialGradient(0, 0, 0, 0, 0, 1); rg.add_color_stop_rgba(0, 0, 0, 0, 0.45 * a); rg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(rg); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    ctx.save(); ctx.translate(cx - w * k / 2, cy - h * k / 2); ctx.scale(k, k)
    ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(max(0.0, min(1.0, a)))
    ctx.restore()


def main_kind(ep):
    for sc in ep.get("scenes", []):
        if sc.get("type") == "fruit" and sc.get("fruit"):
            return sc["fruit"]
    ks = used_kinds(ep)
    return ks[0] if ks else None


def deco_fresh(ctx, ep, idx, t, T):
    """Real photo of the episode's main fruit peeking from the bottom-right corner behind the content."""
    sc = ep["scenes"][idx]
    if not photos_on() or sc.get("type") in ("fruit", "finale", "compare") or sc.get("deco") is False:
        return
    kind = sc.get("deco_fruit") or main_kind(ep)
    if not kind or photo_surface(kind) is None:
        return
    q = eo(p(t, 0.05, 0.6)) * (1 - p(t, T - 0.2, 0.2))
    side = 1 if idx % 2 else -1
    cx = 540 + side * 360 + side * (1 - q) * 200
    ctx.save(); ctx.translate(cx, 1330 + 10 * math.sin(t * 1.8)); ctx.rotate(side * (0.18 + 0.03 * math.sin(t)))
    tech.glow(ctx, 0, 0, 380, E.GOLD, 0.15 * q)
    draw_photo(ctx, kind, 0, 0, 560, 0.92 * q)
    ctx.restore()


E.DECO_HOOKS["fresh"] = deco_fresh


GARNISH = ["mint", "raspberry", "blueberry", "lime", "ice"]


def used_kinds(ep):
    ks = []
    for sc in ep.get("scenes", []):
        for k in ([sc.get("fruit")] + list(sc.get("fruits", [])) + [r.get("fruit") for r in sc.get("rows", []) if isinstance(r, dict)]):
            if k and k not in ks:
                ks.append(k)
    if ep.get("theme") == "splash":
        for k in GARNISH:
            if k not in ks:
                ks.append(k)
    if any(sc.get("type") == "finale" and not sc.get("fruits") for sc in ep.get("scenes", [])):
        for k in ("apple", "kiwi", "orange"):
            if k not in ks:
                ks.append(k)
    return ks


def photo_credits(ep):
    if not (ep.get("theme") in ("fresh", "splash") and ep.get("photos", True)):
        return []
    import json as _j
    out = []
    for k in used_kinds(ep):
        m = os.path.join(PHOTO_DIR, k, "meta.json")
        if os.path.exists(m):
            c = _j.load(open(m))["credit"]
            if c not in out:
                out.append(c)
    return out


def draw_fruit(ctx, kind, cx, cy, s, t=0.0, a=1.0):
    """Draw fruit `kind` centred at (cx, cy) with overall size ~s px (real photo cut-out when available)."""
    if photos_on() and photo_surface(kind) is not None:
        return draw_photo(ctx, kind, cx, cy, s, a)
    r = s / 2
    ctx.save(); ctx.translate(cx, cy)
    if a < 1:
        ctx.push_group()
    k = kind.lower()
    if k in ("apple", "green_apple", "яблоко"):
        green = k == "green_apple"
        stem(ctx, 0, -r * 0.6, r * 0.1, -r * 1.02, r * 0.08)
        apple_path(ctx, r)
        if green:
            shade(ctx, "#D7F58A", "#8BC34A", "#4E7D1E", 0, 0, r)
        else:
            shade(ctx, "#FF9A8B", "#E63946", "#7F1720", 0, 0, r)
        leaf(ctx, r * 0.08, -r * 0.92, r * 0.62, -0.5)
        spec(ctx, -r * 0.45, -r * 0.3, r * 0.2, r * 0.1, 0.4)
    elif k in ("orange", "tangerine", "mandarin"):
        sq = 0.88 if k != "orange" else 1.0
        round_fruit(ctx, r, "#FFD27A", "#FF8F1F", "#B34D00", sq)
        rnd = random.Random(3)
        for _ in range(60):
            ang = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, r * 0.9)
            ctx.new_sub_path(); ctx.arc(math.cos(ang) * d, math.sin(ang) * d * sq, r * 0.018, 0, 2 * math.pi)
        ctx.set_source_rgba(0.6, 0.25, 0, 0.25); ctx.fill()
        leaf(ctx, r * 0.05, -r * 0.92 * sq, r * 0.55, -0.35)
        spec(ctx, -r * 0.4, -r * 0.4, r * 0.22, r * 0.11, 0.35)
    elif k in ("lemon",):
        ctx.move_to(-r * 1.05, 0)
        ctx.curve_to(-r * 0.9, -r * 0.8, r * 0.9, -r * 0.8, r * 1.05, 0)
        ctx.curve_to(r * 0.9, r * 0.8, -r * 0.9, r * 0.8, -r * 1.05, 0); ctx.close_path()
        shade(ctx, "#FFF59D", "#FFD600", "#B08900", 0, 0, r)
        spec(ctx, -r * 0.35, -r * 0.3, r * 0.25, r * 0.1, 0.35)
    elif k in ("lime",):
        round_fruit(ctx, r * 0.9, "#D4F28A", "#7CB342", "#33691E", 0.9)
        spec(ctx, -r * 0.35, -r * 0.3, r * 0.2, r * 0.1, 0.3)
    elif k in ("grapefruit", "orange_half", "lemon_half"):
        cols = {"grapefruit": ("#FFB38A", "#E2643B", "#FF6F61", "#D9443A"),
                "orange_half": ("#FFB347", "#E07B00", "#FFA62B", "#F07800"),
                "lemon_half": ("#FFF176", "#C8A800", "#FFF59D", "#F2D53C")}[k]
        citrus_half(ctx, r, *cols)
    elif k in ("kiwi",):
        ctx.arc(0, 0, r, 0, 2 * math.pi); shade(ctx, "#A1887F", "#795548", "#4E342E", 0, 0, r)
        ctx.arc(0, 0, r * 0.9, 0, 2 * math.pi)
        g = cairo.RadialGradient(0, 0, r * 0.1, 0, 0, r * 0.9)
        g.add_color_stop_rgb(0, *hexc("#E8F5A8")[:3]); g.add_color_stop_rgb(0.45, *hexc("#9CCC3C")[:3]); g.add_color_stop_rgb(1, *hexc("#5C8F14")[:3])
        ctx.set_source(g); ctx.fill()
        for i in range(40):
            ang = 2 * math.pi * i / 40
            ctx.move_to(math.cos(ang) * r * 0.3, math.sin(ang) * r * 0.3); ctx.line_to(math.cos(ang) * r * 0.86, math.sin(ang) * r * 0.86)
        ctx.set_source_rgba(1, 1, 1, 0.12); ctx.set_line_width(max(1, r * 0.012)); ctx.stroke()
        ctx.save(); ctx.scale(1, 0.8); ctx.arc(0, 0, r * 0.26, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*hexc("#F7FBE1")[:3]); ctx.fill()
        for i in range(30):
            ang = 2 * math.pi * i / 30 + (0.05 if i % 2 else 0)
            d = r * (0.36 if i % 2 else 0.42)
            ctx.save(); ctx.translate(math.cos(ang) * d, math.sin(ang) * d); ctx.rotate(ang); ctx.scale(r * 0.045, r * 0.022)
            ctx.new_sub_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(0.08, 0.08, 0.05); ctx.fill()
        spec(ctx, -r * 0.4, -r * 0.45, r * 0.18, r * 0.07, 0.25)
    elif k in ("banana",):
        ctx.move_to(-r * 0.95, -r * 0.35)
        ctx.curve_to(-r * 0.6, r * 0.75, r * 0.65, r * 0.75, r * 1.0, -r * 0.45)
        ctx.curve_to(r * 0.55, r * 0.02, -r * 0.5, r * 0.06, -r * 0.82, -r * 0.5); ctx.close_path()
        shade(ctx, "#FFF7A8", "#FFD93B", "#C79A00", 0, r * 0.15, r)
        ctx.arc(-r * 0.9, -r * 0.43, r * 0.06, 0, 2 * math.pi); fill(ctx, "#5D4037")
        stem(ctx, r * 0.98, -r * 0.45, r * 1.1, -r * 0.62, r * 0.09, "#7A8B3A")
    elif k in ("pomegranate",):
        ctx.move_to(-r * 0.22, -r * 0.82)
        for i, x in enumerate([-0.22, -0.16, -0.08, 0.0, 0.08, 0.16, 0.22]):
            ctx.line_to(r * x, -r * (1.05 if i % 2 else 0.82))
        ctx.close_path(); fill(ctx, "#9B1B30")
        round_fruit(ctx, r * 0.95, "#FF8A80", "#C62839", "#6A0F1B")
        spec(ctx, -r * 0.4, -r * 0.35, r * 0.22, r * 0.1, 0.35)
    elif k in ("pomegranate_seeds", "anar_seeds"):
        rnd = random.Random(5)
        for _ in range(45):
            ang = rnd.uniform(0, 2 * math.pi); d = r * math.sqrt(rnd.uniform(0, 1)) * 0.95
            x, y = math.cos(ang) * d, math.sin(ang) * d
            ctx.save(); ctx.translate(x, y); ctx.rotate(rnd.uniform(0, 3)); ctx.scale(r * 0.12, r * 0.09)
            ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
            g = cairo.RadialGradient(x - r * 0.03, y - r * 0.03, 0, x, y, r * 0.12)
            g.add_color_stop_rgb(0, 1, 0.6, 0.65); g.add_color_stop_rgb(1, 0.65, 0.05, 0.15)
            ctx.set_source(g); ctx.fill()
    elif k in ("apricot", "peach", "урюк"):
        base = ("#FFD08A", "#FFA53B", "#C2620A") if k != "peach" else ("#FFD3B0", "#FF9D6C", "#C4503A")
        round_fruit(ctx, r * 0.95, *base)
        ctx.arc(r * 0.35, r * 0.25, r * 0.6, 0, 2 * math.pi)
        g = cairo.RadialGradient(r * 0.35, r * 0.25, 0, r * 0.35, r * 0.25, r * 0.6)
        g.add_color_stop_rgba(0, 0.9, 0.2, 0.15, 0.35); g.add_color_stop_rgba(1, 0.9, 0.2, 0.15, 0)
        ctx.set_source(g); ctx.fill()
        ctx.move_to(r * 0.05, -r * 0.9); ctx.curve_to(-r * 0.35, -r * 0.3, -r * 0.3, r * 0.4, r * 0.05, r * 0.92)
        ctx.set_source_rgba(0.5, 0.2, 0, 0.3); ctx.set_line_width(r * 0.04); ctx.stroke()
        leaf(ctx, r * 0.05, -r * 0.88, r * 0.5, -0.6)
        spec(ctx, -r * 0.45, -r * 0.35, r * 0.18, r * 0.09, 0.35)
    elif k in ("plum",):
        round_fruit(ctx, r * 0.9, "#B39DDB", "#5E2A84", "#2A0E3F", 1.08)
        ctx.move_to(0, -r * 0.95); ctx.curve_to(-r * 0.3, -r * 0.3, -r * 0.25, r * 0.4, 0, r * 0.95)
        ctx.set_source_rgba(0, 0, 0, 0.2); ctx.set_line_width(r * 0.035); ctx.stroke()
        spec(ctx, -r * 0.4, -r * 0.4, r * 0.2, r * 0.1, 0.3)
    elif k in ("grapes", "grapes_green"):
        cols = ("#C39BD3", "#6C2B8E", "#2E0F42") if k == "grapes" else ("#E6F5A6", "#A8C93A", "#5E7A12")
        stem(ctx, 0, -r * 0.7, r * 0.12, -r * 1.05, r * 0.07, "#6D4C2F")
        leaf(ctx, r * 0.1, -r * 0.85, r * 0.6, -0.2)
        rows = [4, 4, 3, 2, 1]; br = r * 0.21
        for ri, n in enumerate(rows):
            for j in range(n):
                x = (j - (n - 1) / 2) * br * 1.85; y = -r * 0.55 + ri * br * 1.6
                ctx.arc(x, y, br, 0, 2 * math.pi); shade(ctx, *cols, x, y, br)
                spec(ctx, x - br * 0.35, y - br * 0.4, br * 0.25, br * 0.12, 0.4)
    elif k in ("cherry", "черешня"):
        for (x, y) in [(-r * 0.4, r * 0.35), (r * 0.42, r * 0.45)]:
            stem(ctx, x, y - r * 0.4, r * 0.05, -r * 0.9, r * 0.05, "#5D7A2A")
            ctx.arc(x, y, r * 0.45, 0, 2 * math.pi); shade(ctx, "#FF8A80", "#C2185B", "#5A0820", x, y, r * 0.45)
            spec(ctx, x - r * 0.15, y - r * 0.18, r * 0.12, r * 0.06, 0.45)
        leaf(ctx, r * 0.05, -r * 0.9, r * 0.55, -0.4)
    elif k in ("strawberry",):
        ctx.move_to(0, r * 1.0)
        ctx.curve_to(-r * 0.55, r * 0.6, -r * 1.0, -r * 0.2, -r * 0.75, -r * 0.6)
        ctx.curve_to(-r * 0.45, -r * 0.95, r * 0.45, -r * 0.95, r * 0.75, -r * 0.6)
        ctx.curve_to(r * 1.0, -r * 0.2, r * 0.55, r * 0.6, 0, r * 1.0); ctx.close_path()
        shade(ctx, "#FF8A80", "#E53935", "#7F0E0E", 0, 0, r)
        for i in range(-3, 4):
            for j in range(0, 5):
                x = i * r * 0.22 + (j % 2) * r * 0.11; y = -r * 0.45 + j * r * 0.28
                if abs(x) < r * (0.75 - j * 0.12):
                    ctx.save(); ctx.translate(x, y); ctx.scale(r * 0.03, r * 0.045); ctx.new_sub_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(1, 0.88, 0.45); ctx.fill()
        for i in range(5):
            leaf(ctx, 0, -r * 0.72, r * 0.42, -math.pi / 2 + (i - 2) * 0.55, "#66BB6A", "#2E7D32")
    elif k in ("pear",):
        ctx.move_to(0, -r * 0.85)
        ctx.curve_to(r * 0.35, -r * 0.85, r * 0.3, -r * 0.3, r * 0.6, r * 0.05)
        ctx.curve_to(r * 0.95, r * 0.45, r * 0.7, r * 1.0, 0, r * 1.0)
        ctx.curve_to(-r * 0.7, r * 1.0, -r * 0.95, r * 0.45, -r * 0.6, r * 0.05)
        ctx.curve_to(-r * 0.3, -r * 0.3, -r * 0.35, -r * 0.85, 0, -r * 0.85); ctx.close_path()
        shade(ctx, "#F4FF9E", "#C6D93B", "#7D8C12", 0, r * 0.2, r)
        stem(ctx, 0, -r * 0.84, r * 0.1, -r * 1.08, r * 0.06)
        leaf(ctx, r * 0.08, -r * 1.0, r * 0.45, -0.3)
        spec(ctx, -r * 0.35, r * 0.1, r * 0.15, r * 0.08, 0.3)
    elif k in ("watermelon", "арбуз", "дарбыз"):
        ctx.new_path(); ctx.arc(0, -r * 0.35, r, 0, math.pi); ctx.close_path(); fill(ctx, "#2E7D32")
        ctx.arc(0, -r * 0.35, r * 0.92, 0, math.pi); ctx.close_path(); fill(ctx, "#E8F5C8")
        ctx.arc(0, -r * 0.35, r * 0.85, 0, math.pi); ctx.close_path()
        g = cairo.RadialGradient(0, -r * 0.35, r * 0.1, 0, -r * 0.35, r * 0.85)
        g.add_color_stop_rgb(0, 1, 0.45, 0.5); g.add_color_stop_rgb(1, 0.86, 0.12, 0.25); ctx.set_source(g); ctx.fill()
        for i in range(9):
            ang = math.pi * (i + 0.5) / 9; d = r * (0.5 if i % 2 else 0.62)
            ctx.save(); ctx.translate(math.cos(ang) * d, -r * 0.35 + math.sin(ang) * d); ctx.rotate(ang); ctx.scale(r * 0.05, r * 0.028)
            ctx.new_sub_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(0.1, 0.08, 0.06); ctx.fill()
    elif k in ("melon", "дыня"):
        ctx.save(); ctx.scale(1.0, 0.72); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        shade(ctx, "#FFF3A8", "#F2C94C", "#A9821A", 0, 0, r)
        ctx.save(); ctx.scale(1.0, 0.72); ctx.arc(0, 0, r * 0.98, 0, 2 * math.pi); ctx.restore(); ctx.clip()
        for i in range(-8, 9):
            ctx.move_to(i * r * 0.2 - r, -r); ctx.line_to(i * r * 0.2 + r, r)
            ctx.move_to(i * r * 0.2 + r, -r); ctx.line_to(i * r * 0.2 - r, r)
        ctx.set_source_rgba(1, 1, 0.9, 0.22); ctx.set_line_width(r * 0.015); ctx.stroke()
        ctx.reset_clip()
    elif k in ("persimmon", "хурма"):
        round_fruit(ctx, r * 0.95, "#FFB36B", "#F26B1D", "#9C3A05", 0.86)
        for i in range(4):
            leaf(ctx, 0, -r * 0.78, r * 0.38, -math.pi / 2 + (i - 1.5) * 0.9, "#7CB342", "#3E6B1A")
        spec(ctx, -r * 0.4, -r * 0.25, r * 0.2, r * 0.09, 0.35)
    elif k in ("sea_buckthorn", "oblepikha", "облепиха"):
        ctx.move_to(-r * 0.9, r * 0.9); ctx.curve_to(-r * 0.3, r * 0.2, r * 0.2, -r * 0.3, r * 0.9, -r * 0.9)
        ctx.set_source_rgb(*hexc("#6D4C2F")[:3]); ctx.set_line_width(r * 0.07); ctx.stroke()
        rnd = random.Random(7)
        for i in range(9):
            tt = i / 8; bx = -r * 0.9 + tt * r * 1.8; by = r * 0.9 - tt * r * 1.8
            leaf(ctx, bx, by, r * 0.5, -math.pi / 2 - 0.9 + rnd.uniform(-0.3, 0.3) + (i % 2) * 1.8, "#B7C9A8", "#6E8A62")
        for i in range(26):
            tt = rnd.uniform(0.05, 0.95); bx = -r * 0.9 + tt * r * 1.8 + rnd.uniform(-r * 0.16, r * 0.16)
            by = r * 0.9 - tt * r * 1.8 + rnd.uniform(-r * 0.16, r * 0.16); br = r * 0.1
            ctx.save(); ctx.translate(bx, by); ctx.scale(1, 1.2); ctx.arc(0, 0, br, 0, 2 * math.pi); ctx.restore()
            shade(ctx, "#FFE082", "#FF9800", "#B35400", bx, by, br)
    elif k in ("currant", "blueberry", "смородина"):
        rnd = random.Random(11); br = r * 0.26
        for (x, y) in [(-0.45, -0.25), (0.15, -0.4), (0.5, 0.05), (-0.15, 0.2), (-0.55, 0.45), (0.25, 0.5), (0.0, -0.05)]:
            X, Y = x * r, y * r
            ctx.arc(X, Y, br, 0, 2 * math.pi); shade(ctx, "#7986CB", "#283593", "#0D1033", X, Y, br)
            spec(ctx, X - br * 0.35, Y - br * 0.35, br * 0.25, br * 0.12, 0.35)
    elif k in ("avocado",):
        ctx.move_to(0, -r * 0.95)
        ctx.curve_to(r * 0.45, -r * 0.95, r * 0.45, -r * 0.3, r * 0.68, r * 0.15)
        ctx.curve_to(r * 0.9, r * 0.65, r * 0.55, r * 1.0, 0, r * 1.0)
        ctx.curve_to(-r * 0.55, r * 1.0, -r * 0.9, r * 0.65, -r * 0.68, r * 0.15)
        ctx.curve_to(-r * 0.45, -r * 0.3, -r * 0.45, -r * 0.95, 0, -r * 0.95); ctx.close_path()
        fill(ctx, "#2E5B1E")
        ctx.save(); ctx.scale(0.88, 0.9); ctx.move_to(0, -r * 0.95)
        ctx.curve_to(r * 0.45, -r * 0.95, r * 0.45, -r * 0.3, r * 0.68, r * 0.15)
        ctx.curve_to(r * 0.9, r * 0.65, r * 0.55, r * 1.0, 0, r * 1.0)
        ctx.curve_to(-r * 0.55, r * 1.0, -r * 0.9, r * 0.65, -r * 0.68, r * 0.15)
        ctx.curve_to(-r * 0.45, -r * 0.3, -r * 0.45, -r * 0.95, 0, -r * 0.95); ctx.close_path(); ctx.restore()
        shade(ctx, "#F4F7B0", "#C5D86D", "#7FA33A", 0, r * 0.2, r)
        ctx.arc(0, r * 0.35, r * 0.34, 0, 2 * math.pi); shade(ctx, "#C18A5A", "#8D5524", "#4A2A10", 0, r * 0.35, r * 0.34)
    elif k in ("mango",):
        ctx.save(); ctx.rotate(-0.35); ctx.scale(1.0, 0.78); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        g = cairo.LinearGradient(-r, r, r, -r)
        g.add_color_stop_rgb(0, *hexc("#7CB342")[:3]); g.add_color_stop_rgb(0.45, *hexc("#FFC233")[:3]); g.add_color_stop_rgb(1, *hexc("#F4511E")[:3])
        ctx.set_source(g); ctx.fill()
        spec(ctx, -r * 0.3, -r * 0.35, r * 0.25, r * 0.1, 0.35)
    else:  # generic round fruit
        round_fruit(ctx, r * 0.95, "#FFD08A", "#FF8A3D", "#B34D00")
        leaf(ctx, 0, -r * 0.9, r * 0.5, -0.5)
    if a < 1:
        ctx.pop_group_to_source(); ctx.paint_with_alpha(max(0.0, a))
    ctx.restore()


# ---------------- background ----------------

_PARTS = [(random.Random(i).uniform(0, 1080), random.Random(i + 99).uniform(0, 1920),
           random.Random(i + 7).uniform(4, 14), random.Random(i + 3).uniform(10, 40)) for i in range(38)]


def background_fresh(ctx, tg):
    g = cairo.LinearGradient(0, 0, 0, E.H)
    g.add_color_stop_rgb(0, *hexc(E.BG1)[:3]); g.add_color_stop_rgb(1, *hexc(E.BG2)[:3])
    ctx.set_source(g); ctx.paint()
    for (cx, cy, r, c, a) in [(540 + 280 * math.sin(tg * 0.3), 430, 760, "#FFB547", 0.16),
                              (540 - 300 * math.sin(tg * 0.22 + 1), 1380, 820, "#7BD389", 0.14)]:
        rg = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        rg.add_color_stop_rgba(0, *hexc(c)[:3], a); rg.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(rg); ctx.paint()
    for (x, y, r, sp) in _PARTS:
        yy = (y - tg * sp) % 1980 - 30
        ctx.arc(x + 12 * math.sin(tg * 0.8 + x), yy, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.95, 0.85, 0.05); ctx.fill()


E.BG_HOOKS["fresh"] = background_fresh


# ---------------- scenes ----------------

def chip(ctx, s, cx, cy, a, color=None, fg=None, size=32, solid=False):
    if a <= 0 or not s:
        return
    color = color or E.GOLD
    w = tw(ctx, s, size) + 64
    rrect(ctx, cx - w / 2, cy - size * 0.9, w, size * 1.8, size * 0.9)
    fill(ctx, color, (1.0 if solid else 0.16) * a)
    if not solid:
        rrect(ctx, cx - w / 2, cy - size * 0.9, w, size * 1.8, size * 0.9); tech.stroke(ctx, color, 0.85 * a, 2)
    text(ctx, s, cx, cy + size * 0.36, size, fg or (E.DARK if solid else color), "c", True, a)


def s_fruit(ctx, t, c):
    sc = c.sc; a = c.out(t)
    kind = sc.get("fruit", "apple")
    if E.THEME == "fresh" and photos_on() and sc.get("bg_photo", True) and bg_surface(kind) is not None:
        bs = bg_surface(kind); z = 1.0 + 0.04 * t / max(c.T, 1)
        ctx.save(); ctx.translate(540, 960); ctx.scale(z / 1.12, z / 1.12); ctx.translate(-bs.get_width() / 2, -bs.get_height() / 2)
        ctx.set_source_surface(bs, 0, 0); ctx.paint_with_alpha(0.55 * a); ctx.restore()
        g = cairo.LinearGradient(0, 0, 0, E.H)
        g.add_color_stop_rgba(0, *hexc(E.BG2)[:3], 0.75); g.add_color_stop_rgba(0.4, *hexc(E.BG2)[:3], 0.15)
        g.add_color_stop_rgba(0.7, *hexc(E.BG2)[:3], 0.35); g.add_color_stop_rgba(1, *hexc(E.BG2)[:3], 0.85)
        ctx.set_source(g); ctx.paint()
    k = eob(p(t, 0.15, 0.7))
    bob = 10 * math.sin(t * 2.2)
    tech.glow(ctx, 540, 880, 420, E.GOLD, 0.22 * a)
    if k > 0.02:
        ctx.save(); ctx.translate(540, 880 + bob); ctx.rotate(0.06 * math.sin(t * 1.6)); ctx.scale(k, k)
        draw_fruit(ctx, sc.get("fruit", "apple"), 0, 0, sc.get("size", 470), t, a)
        ctx.restore()
    q = eo(p(t, 0.5, 0.4))
    name = sc.get("name", "")
    if name:
        ctx.save(); ctx.translate(0, (1 - q) * 40)
        text(ctx, name, 540, 1255, fit(ctx, name, 110, 980), E.WHITE, "c", True, q * a)
        ctx.restore()
    chip(ctx, sc.get("kicker"), 540, 1340, eo(p(t, 0.7, 0.35)) * a, solid=True, size=30)
    hl = [w.lower() for w in sc.get("highlight", [])]
    for i, l in enumerate(sc.get("lines", [])[:2]):
        q = p(t, 0.05 + 0.12 * i, 0.3)
        size = fit(ctx, l, 84, 980)
        tech.rich_line(ctx, l, 540, 440 + i * 100, size, hl, eo(q) * a, 1.3 - 0.3 * eob(q), hcol=E.GOLD, base=E.WHITE)


def s_nutrients(ctx, t, c):
    sc = c.sc; a = c.out(t)
    E.titles(ctx, sc, t, a)
    tiles = sc["tiles"][:4]; n = len(tiles)
    act_map = sc.get("active"); k = c.active(t)
    act = act_map[min(k, len(act_map) - 1)] if act_map else None
    W2, H2, gap = 440, 330, 40
    for i, tl in enumerate(tiles):
        row, colm = divmod(i, 2)
        full = (n % 2 == 1 and i == n - 1)
        w = W2 * 2 + gap if full else W2
        x = 80 + (0 if full else colm * (W2 + gap)); y = 600 + row * (H2 + gap)
        st = c.at(tl["at_part"]) if tl.get("at_part") is not None else 0.3 + 0.18 * i
        q = eo(p(t, st, 0.4)); la = q * a
        if la <= 0:
            continue
        on = act is None or act == i
        cc = E.col(tl.get("color"), i)
        ctx.save(); ctx.translate(x + w / 2, y + H2 / 2); s = (0.9 + 0.1 * q) * (1.03 if (act == i) else 1.0); ctx.scale(s, s)
        rrect(ctx, -w / 2, -H2 / 2, w, H2, 34); fill(ctx, E.CARD, 0.95 * la)
        if act == i:
            rrect(ctx, -w / 2, -H2 / 2, w, H2, 34); tech.stroke(ctx, cc, la, 4)
        dim = 1.0 if on else 0.5
        v = float(tl["value"]); dec = int(tl.get("decimals", 0))
        cnt = eo(p(t, st, 1.2))
        vs = E.num(v * cnt, dec)
        unit = tl.get("unit", "")
        size = 110
        vw = tw(ctx, E.num(v, dec), size); uw = tw(ctx, " " + unit, 44) if unit else 0
        while vw + uw > w - 60 and size > 60:
            size -= 4; vw = tw(ctx, E.num(v, dec), size)
        x0 = -(vw + uw) / 2
        text(ctx, vs, x0, -H2 / 2 + 150, size, cc, "l", True, la * dim)
        if unit:
            text(ctx, " " + unit, x0 + vw, -H2 / 2 + 150, 44, E.MUTED, "l", True, la * dim)
        lab = tl.get("label", "")
        text(ctx, lab, 0, -H2 / 2 + 215, fit(ctx, lab, 40, w - 50), E.WHITE, "c", True, la * dim)
        if tl.get("note"):
            chip(ctx, tl["note"], 0, H2 / 2 - 52, la * dim, cc, size=28)
        ctx.restore()


def s_myth(ctx, t, c):
    sc = c.sc; a = c.out(t)
    chip(ctx, sc.get("kicker", "Миф или факт?"), 540, 470, eo(p(t, 0.05, 0.35)) * a, size=32)
    st = sc.get("statement", "")
    lines = wrap(ctx, "«" + st + "»", 70, 940, True, True)[:3]
    for i, l in enumerate(lines):
        q = eo(p(t, 0.15 + 0.1 * i, 0.4))
        ctx.save(); ctx.translate(0, (1 - q) * 30)
        text(ctx, l, 540, 640 + i * 86, fit(ctx, l, 70, 960), E.WHITE, "c", True, q * a)
        ctx.restore()
    if sc.get("fruit"):
        draw_fruit(ctx, sc["fruit"], 900, 400, 120, t, 0.9 * eo(p(t, 0.2, 0.4)) * a)
    vt = c.at(sc.get("verdict_at_part", 1)) if len(c.tm["parts"]) > 1 else 1.0
    v = sc.get("verdict", "МИФ").upper()
    vc = {"МИФ": "#FF5A5F", "ФАКТ": "#7BD389"}.get(v, "#F7D154")
    q = p(t, vt, 0.3)
    if q > 0:
        s = 2.2 - 1.2 * eob(q)
        ctx.save(); ctx.translate(540, 1035); ctx.rotate(-0.12); ctx.scale(s, s)
        size = 120 if len(v) <= 4 else 86
        w = tw(ctx, v, size) + 90; h = size * 1.45
        rrect(ctx, -w / 2, -h / 2, w, h, 26); fill(ctx, vc, 0.14 * q * a)
        rrect(ctx, -w / 2, -h / 2, w, h, 26); tech.stroke(ctx, vc, q * a, 10)
        text(ctx, v, 0, size * 0.36, size, vc, "c", True, q * a)
        ctx.restore()
    if sc.get("body"):
        bt = c.at(sc.get("body_at_part", 2)) if len(c.tm["parts"]) > 2 else vt + 0.6
        ba = eo(p(t, bt, 0.4)) * a
        for j, l in enumerate(wrap(ctx, sc["body"], 40, 920, False, True)[:3]):
            text(ctx, l, 540, 1215 + j * 52, 40, E.MUTED, "c", False, ba)


def s_compare(ctx, t, c):
    sc = c.sc; a = c.out(t)
    E.titles(ctx, sc, t, a)
    rows = sc["rows"][:5]; n = len(rows)
    mx = float(sc.get("max", max(float(r["value"]) for r in rows)))
    step = min(150, 760 / max(n, 1)); y0 = 620
    for i, r in enumerate(rows):
        y = y0 + i * step
        st = c.at(r["at_part"]) if r.get("at_part") is not None else 0.35 + 0.22 * i
        la = eo(p(t, st, 0.4)) * a
        if la <= 0:
            continue
        best = r.get("best", False)
        cc = E.GOLD if best else E.col(r.get("color", "teal"))
        if r.get("fruit"):
            draw_fruit(ctx, r["fruit"], 150, y + 48, min(110, step - 20), t, la)
        lab = r["label"]
        text(ctx, lab, 230, y + 22, fit(ctx, lab, 40, 560, best), E.WHITE, "l", best, la)
        g = eo(p(t, st + 0.1, 1.0))
        bw = 600
        w = max(10, bw * float(r["value"]) / mx * g)
        rrect(ctx, 230, y + 42, bw, 44, 14); ctx.set_source_rgba(*hexc(E.WHITE)[:3], 0.08 * la); ctx.fill()
        rrect(ctx, 230, y + 42, w, 44, 14); fill(ctx, cc, la)
        vt = r.get("text", E.num(float(r["value"]) * g, int(sc.get("decimals", 0))) + sc.get("unit", ""))
        text(ctx, vt, min(230 + w + 16, 1000 - tw(ctx, vt, 38)), y + 78, 38, cc, "l", True, la * p(t, st + 0.3, 0.3))


def s_caution(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eob(p(t, 0.05, 0.5))
    amber = E.PAL.get("yellow", "#F7D154")
    tech.glow(ctx, 540, 560, 220 * k, amber, 0.3 * a)
    ctx.arc(540, 560, 105 * k, 0, 2 * math.pi); fill(ctx, E.CARD, 0.95 * a)
    if k > 0:
        tech.icon(ctx, "warning", 540, 555, 120 * k, amber, a)
    title = sc.get("title", "Кому осторожно")
    text(ctx, title, 540, 770, fit(ctx, title, 64, 960), E.WHITE, "c", True, eo(p(t, 0.15, 0.4)) * a)
    items = sc.get("items", [])[:4]
    y = 860
    for i, it in enumerate(items):
        st = c.at(it["at_part"]) if isinstance(it, dict) and it.get("at_part") is not None else 0.5 + 0.35 * i
        s = it["text"] if isinstance(it, dict) else it
        q = eo(p(t, st, 0.4)); la = q * a
        ls = wrap(ctx, s, 40, 800, False, False)[:2]
        h = 40 + 50 * len(ls)
        if la > 0:
            ctx.save(); ctx.translate((1 - q) * 60, 0)
            rrect(ctx, 90, y, 900, h, 24); fill(ctx, E.CARD, 0.9 * la)
            ctx.arc(140, y + h / 2, 12, 0, 2 * math.pi); fill(ctx, amber, la)
            for j, l in enumerate(ls):
                text(ctx, l, 180, y + h / 2 - (len(ls) - 1) * 25 + 14 + j * 50, 40, E.WHITE, "l", False, la)
            ctx.restore()
        y += h + 22


def s_finale(ctx, t, c):
    sc = c.sc; a = c.out(t)
    fr = sc.get("fruits", ["apple", "kiwi", "orange"])[:3]
    for i, f in enumerate(fr):
        k = eob(p(t, 0.05 + 0.12 * i, 0.5))
        x = 540 + (i - (len(fr) - 1) / 2) * 260
        if k > 0.02:
            ctx.save(); ctx.translate(x, 640 + 12 * math.sin(t * 3 + i)); ctx.scale(k, k)
            draw_fruit(ctx, f, 0, 0, 210, t, a); ctx.restore()
    q = eo(p(t, 0.3, 0.4))
    cta = sc.get("cta", "Подпишись")
    text(ctx, cta, 540, 910, fit(ctx, cta, 104, 980), E.WHITE, "c", True, q * a)
    if sc.get("sub"):
        text(ctx, sc["sub"], 540, 985, fit(ctx, sc["sub"], 44, 960, False), E.MUTED, "c", False, q * a)
    if sc.get("save"):
        chip(ctx, sc["save"], 540, 1105, eo(p(t, 0.6, 0.4)) * a, size=34, solid=True)
    if sc.get("source"):
        text(ctx, sc["source"], 540, 1235, fit(ctx, sc["source"], 28, 960, False), E.MUTED, "c", False, eo(p(t, 0.8, 0.4)) * a)
    disc = sc.get("disclaimer", "Не является медицинской рекомендацией")
    if disc:
        text(ctx, disc, 540, 1285, fit(ctx, disc, 26, 960, False), E.MUTED, "c", False, 0.8 * eo(p(t, 0.9, 0.4)) * a)
    cr = photo_credits(E.CURRENT_EP)
    if cr:
        line = "Фото: " + "; ".join(cr)
        ls = wrap(ctx, line, 22, 980, False, False)
        if len(ls) > 2:
            ls = ["Фото: Wikimedia Commons (CC0, Public domain, CC BY)", "авторы и лицензии — в описании"]
        for j, l in enumerate(ls):
            text(ctx, l, 540, 1325 + j * 28, 22, E.MUTED, "c", False, 0.8 * eo(p(t, 0.9, 0.4)) * a)


E.SCENES.update(fruit=s_fruit, nutrients=s_nutrients, myth=s_myth, compare=s_compare, caution=s_caution, finale=s_finale)

if __name__ == "__main__":  # contact sheet of all fruits: python3 tools/fruits.py out.png
    import sys
    kinds = ["apple", "green_apple", "orange", "tangerine", "lemon", "lime", "grapefruit", "orange_half", "kiwi", "banana",
             "pomegranate", "pomegranate_seeds", "apricot", "peach", "plum", "grapes", "grapes_green", "cherry", "strawberry",
             "pear", "watermelon", "melon", "persimmon", "sea_buckthorn", "currant", "avocado", "mango", "lemon_half"]
    cols = 7; rows = (len(kinds) + cols - 1) // cols
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, cols * 260, rows * 300)
    ctx = cairo.Context(surf)
    E.apply_theme({"theme": "fresh"}); background_fresh(ctx, 0)
    for i, kd in enumerate(kinds):
        x = (i % cols) * 260 + 130; y = (i // cols) * 300 + 130
        draw_fruit(ctx, kd, x, y, 180)
        text(ctx, kd, x, y + 140, 22, E.WHITE, "c", False)
    surf.write_to_png(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fruits.png")
