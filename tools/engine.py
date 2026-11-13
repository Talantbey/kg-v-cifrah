"""Vertical (1080x1920, 30 fps) infographic video engine driven by an episode JSON.

Scene types: title, counter, donut, bars, dotgrid, scale, list, fact, word, timeline, outro.
Every scene has "parts": [[tts_text, subtitle_text], ...] — what the narrator says and the
subtitle shown while it is said. Elements that reveal "at_part": n appear when part n starts.
"""
import cairo, math, json, os, subprocess

W, H, FPS = 1080, 1920, 30
LEAD, TAIL, OUTRO_TAIL = 0.30, 0.40, 1.2

PAL = {"gold": "#FFC23D", "red": "#EF4B5F", "teal": "#2EC4B6", "grey": "#55657F",
       "blue": "#4D8DFF", "violet": "#A06BFF", "green": "#4CD07D", "orange": "#FF8A3D",
       "white": "#F4F6FA", "muted": "#93A3BC"}
CYCLE = ["gold", "teal", "red", "blue", "violet", "green", "orange", "grey"]
BG1, BG2, CARD = "#0E1830", "#070B16", "#141F36"
GOLD, WHITE, MUTED, DARK = PAL["gold"], PAL["white"], PAL["muted"], "#1A1405"
FONT = "Inter"


def col(c, i=0):
    if not c:
        c = CYCLE[i % len(CYCLE)]
    return PAL.get(c, c)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def p(t, s, d):
    return clamp((t - s) / d) if d > 0 else float(t >= s)


def eo(x):
    return 1 - (1 - x) ** 3


def eob(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def font(ctx, size, bold=True):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def tw(ctx, s, size, bold=True):
    font(ctx, size, bold)
    return ctx.text_extents(s).x_advance


def fit(ctx, s, size, maxw, bold=True, minsize=20):
    while size > minsize and tw(ctx, s, size, bold) > maxw:
        size -= 2
    return size


def text(ctx, s, x, y, size, color, align="c", bold=True, alpha=1.0, spacing=0):
    font(ctx, size, bold)
    if spacing:
        widths = [ctx.text_extents(ch).x_advance + spacing for ch in s]
        w = sum(widths) - spacing
    else:
        w = ctx.text_extents(s).x_advance
    x0 = x - w / 2 if align == "c" else (x - w if align == "r" else x)
    ctx.set_source_rgba(*hexc(col(color), max(0.0, min(1.0, alpha))))
    if spacing:
        cx = x0
        for ch, wd in zip(s, widths):
            ctx.move_to(cx, y); ctx.show_text(ch); cx += wd
    else:
        ctx.move_to(x0, y); ctx.show_text(s)
    ctx.new_path()
    return w


def wrap(ctx, s, size, maxw, bold=True, balance=True):
    s = s.replace(" —", " —")
    font(ctx, size, bold)
    words, lines, cur = s.split(" "), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if ctx.text_extents(trial).x_advance > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = trial
    lines.append(cur)
    if balance and len(lines) == 2:
        best = None
        for k in range(1, len(words)):
            a, b = " ".join(words[:k]), " ".join(words[k:])
            m = max(ctx.text_extents(a).x_advance, ctx.text_extents(b).x_advance)
            if m <= maxw and (best is None or m < best[0]):
                best = (m, [a, b])
        if best:
            lines = best[1]
    return [l.replace(" ", " ") for l in lines]


def rrect(ctx, x, y, w, h, r):
    r = min(r, h / 2, w / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def fill(ctx, color, a=1.0):
    ctx.set_source_rgba(*hexc(col(color), max(0.0, min(1.0, a)))); ctx.fill()


def num(v, dec=0):
    s = f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s


class Ctx:
    """Per-scene helpers: timing of narration parts."""

    def __init__(self, sc, tm, T):
        self.sc, self.tm, self.T = sc, tm, T

    def at(self, i, default=0.0):
        if i is None:
            return default
        parts = self.tm["parts"]
        i = max(0, min(int(i), len(parts) - 1))
        return LEAD + parts[i][0]

    def active(self, t):
        ta = t - LEAD; k = 0
        for i, pt in enumerate(self.tm["parts"]):
            if ta >= pt[0] - 0.05:
                k = i
        return k

    def out(self, t):
        d = 0.4 if self.sc["type"] == "outro" else 0.25
        return 1 - p(t, self.T - d, d)


# ---------------- background, header, subtitles ----------------

def background(ctx, tg):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc(BG1)[:3]); g.add_color_stop_rgb(1, *hexc(BG2)[:3])
    ctx.set_source(g); ctx.paint()
    gx = 540 + 260 * math.sin(tg * 0.25)
    rg = cairo.RadialGradient(gx, 520, 0, gx, 520, 700)
    rg.add_color_stop_rgba(0, *hexc(GOLD)[:3], 0.10); rg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(rg); ctx.paint()
    ctx.set_source_rgba(1, 1, 1, 0.035)
    for yy in range(60, H, 60):
        for xx in range(30, W, 60):
            ctx.arc(xx, yy, 2, 0, 2 * math.pi); ctx.fill()


def header(ctx, s, a):
    s = s.upper()
    size = 30
    while size > 20 and tw(ctx, s, size) + len(s) * 2.5 > 800:
        size -= 1
    w = tw(ctx, s, size) + 2.5 * (len(s) - 1)
    x0 = 540 - (w + 34) / 2
    ctx.arc(x0 + 9, 241, 9, 0, 2 * math.pi); fill(ctx, GOLD, a)
    text(ctx, s, x0 + 34, 252, size, MUTED, "l", True, a, spacing=2.5)


def subtitle(ctx, tm, t):
    ta = t - LEAD
    parts = tm["parts"]; cur = None
    for i, (s, e, sub) in enumerate(parts):
        end = parts[i + 1][0] if i + 1 < len(parts) else e + TAIL
        if s - 0.05 <= ta < end:
            cur = (s, sub)
    if cur is None or not cur[1]:
        return
    s, sub = cur
    a = eo(p(ta, s - 0.05, 0.15))
    size = 50
    lines = wrap(ctx, sub, size, 900)
    if len(lines) > 2:
        size = 44; lines = wrap(ctx, sub, size, 920)
    font(ctx, size)
    w = max(ctx.text_extents(l).x_advance for l in lines)
    lh = int(size * 1.28)
    bh = lh * len(lines) + 34
    by = 1500 - bh / 2 + (1 - a) * 12
    rrect(ctx, 540 - w / 2 - 34, by, w + 68, bh, 24); fill(ctx, "#000000", 0.55 * a)
    for i, l in enumerate(lines):
        text(ctx, l, 540, by + 17 + lh * i + size * 0.94, size, WHITE, "c", True, a)


def sun(ctx, cx, cy, r, rot, a=1.0, rays=40):
    if r <= 0:
        return
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot)
    for i in range(rays):
        ctx.save(); ctx.rotate(2 * math.pi * i / rays)
        ctx.move_to(r * 1.12, -r * 0.05); ctx.line_to(r * 1.62, 0); ctx.line_to(r * 1.12, r * 0.05)
        ctx.close_path(); fill(ctx, GOLD, a); ctx.restore()
    ctx.arc(0, 0, r, 0, 2 * math.pi); fill(ctx, GOLD, a)
    ctx.restore()


def titles(ctx, sc, t, a, y=470):
    q = eo(p(t, 0, 0.4)) * a
    if sc.get("title"):
        s = sc["title"]; size = fit(ctx, s, 56, 960)
        text(ctx, s, 540, y, size, WHITE, "c", True, q)
    if sc.get("subtitle"):
        text(ctx, sc["subtitle"], 540, y + 60, 36, MUTED, "c", False, q)


def pill(ctx, s, cx, cy, k, a, color=GOLD, fg=DARK, size=36):
    if k <= 0:
        return
    w = tw(ctx, s, size) + 70
    ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k)
    rrect(ctx, -w / 2, -size * 0.9, w, size * 1.8, size * 0.9); fill(ctx, color, a)
    text(ctx, s, 0, size * 0.36, size, fg, "c", True, a)
    ctx.restore()


# ---------------- scenes ----------------

def s_title(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eob(p(t, 0.1, 0.7))
    sun(ctx, 540, 720, 115 * k, t * 0.35, a)
    for i, (s, colr, y) in enumerate([(sc.get("title1", ""), GOLD, 1060), (sc.get("title2", ""), WHITE, 1180)]):
        if not s:
            continue
        q = eo(p(t, 0.35 + 0.18 * i, 0.6))
        size = fit(ctx, s, 116, 980)
        ctx.save(); ctx.translate(0, (1 - q) * 60)
        text(ctx, s, 540, y, size, colr, "c", True, q * a)
        ctx.restore()
    if sc.get("chip"):
        q = eo(p(t, 0.9, 0.5)); lbl = sc["chip"].upper()
        w = tw(ctx, lbl, 34) + 2.5 * len(lbl)
        rrect(ctx, 540 - w / 2 - 30, 1235, w + 60, 70, 35)
        ctx.set_source_rgba(*hexc(MUTED, 0.6 * q * a)); ctx.set_line_width(2); ctx.stroke()
        text(ctx, lbl, 540, 1283, 34, MUTED, "c", True, q * a, spacing=2.5)


def s_counter(ctx, t, c):
    sc = c.sc; a = c.out(t)
    q = eo(p(t, 0.1, 0.4)) * a
    if sc.get("label"):
        text(ctx, sc["label"], 540, 520, 46, MUTED, "c", False, q)
    v = float(sc["value"]); dec = int(sc.get("decimals", 0))
    k = eo(p(t, 0.3, float(sc.get("count_seconds", 2.4))))
    s = sc.get("prefix", "") + num(v * k, dec) + sc.get("suffix", "")
    final = sc.get("prefix", "") + num(v, dec) + sc.get("suffix", "")
    size = fit(ctx, final, 150, 980)
    text(ctx, s, 540, 700, size, sc.get("color", WHITE), "c", True, q)
    if sc.get("caption"):
        cs = fit(ctx, sc["caption"], 42, 960, False)
        text(ctx, sc["caption"], 540, 790, cs, MUTED, "c", False, q)
    card = sc.get("card")
    if card:
        tg = c.at(card.get("at_part", 1), 1.5)
        g = eob(p(t, tg, 0.6)); ga = eo(p(t, tg, 0.4)) * a
        ctx.save(); ctx.translate(540, 1080); ctx.scale(0.85 + 0.15 * g, 0.85 + 0.15 * g)
        rrect(ctx, -420, -150, 840, 300, 36); fill(ctx, CARD, 0.95 * ga)
        arrow = card.get("arrow", "up")
        cc = col(card.get("color", "gold"))
        tx = -420 + 60
        if arrow in ("up", "down"):
            if arrow == "up":
                ctx.move_to(-320, -10); ctx.line_to(-270, -80); ctx.line_to(-220, -10)
                ctx.close_path(); fill(ctx, cc, ga); rrect(ctx, -288, -20, 36, 80, 6); fill(ctx, cc, ga)
            else:
                ctx.move_to(-320, 10); ctx.line_to(-270, 80); ctx.line_to(-220, 10)
                ctx.close_path(); fill(ctx, cc, ga); rrect(ctx, -288, -60, 36, 80, 6); fill(ctx, cc, ga)
            tx = -170
        big = card.get("big", ""); bs = fit(ctx, big, 92, 420 - tx - 30)
        text(ctx, big, tx, 10, bs, cc, "l", True, ga)
        if card.get("small"):
            ss = fit(ctx, card["small"], 40, 420 - tx - 30, False)
            text(ctx, card["small"], tx, 75, ss, MUTED, "l", False, ga)
        ctx.restore()
    pl = sc.get("pill")
    if pl:
        tp = c.at(pl.get("at_part", 2), 2.5)
        pill(ctx, pl["text"], 540, 1300, eob(p(t, tp, 0.5)), eo(p(t, tp, 0.3)) * a,
             col(pl.get("color", "gold")), DARK, 60)


def s_donut(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, sc, t, a)
    segs = sc["segments"]; tot = sum(float(s["value"]) for s in segs)
    cx, cy, R, th = 540, 905, 245, 86
    sweep = eo(p(t, 0.3, 2.0)) * 360
    act_map = sc.get("active")  # list: active segment per part
    k = c.active(t)
    act = act_map[min(k, len(act_map) - 1)] if act_map else None
    ctx.set_line_width(th)
    ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.05 * a); ctx.stroke()
    acc = 0
    for i, sg in enumerate(segs):
        v = float(sg["value"]) / tot * 360
        st = acc; en = min(acc + v, sweep); acc += v
        if en <= st:
            continue
        on = (act is None) or i == act
        ctx.set_line_width(th + (16 if i == act else 0))
        ctx.arc(cx, cy, R + (14 if i == act else 0), math.radians(-90 + st + 1.2), math.radians(-90 + en - 1.2))
        ctx.set_source_rgba(*hexc(col(sg.get("color"), i), (1.0 if on else 0.55) * a)); ctx.stroke()
    ca = eo(p(t, 1.0, 0.4)) * a
    ci = act if act is not None else 0
    sg = segs[ci]
    big = sg.get("center", sg.get("text", f"{round(float(sg['value']))}%"))
    text(ctx, big, cx, cy + 20, fit(ctx, big, 130, 360), col(sg.get("color"), ci), "c", True, ca)
    lines = wrap(ctx, sg.get("center_label", sg["label"]).lower(), 34, 300, False)[:2]
    for j, l in enumerate(lines):
        text(ctx, l, cx, cy + 80 + 40 * j, 34, MUTED, "c", False, ca)
    for i, sg in enumerate(segs):
        la = eo(p(t, 1.2 + 0.15 * i, 0.4)) * a
        y = 1262 + i * 60 if len(segs) <= 3 else 1250 + i * 46
        fs = 38 if len(segs) <= 3 else 32
        rrect(ctx, 190, y - fs * 0.8, fs * 0.9, fs * 0.9, 8); fill(ctx, col(sg.get("color"), i), la)
        hi = (i == act)
        text(ctx, sg["label"], 246, y, fit(ctx, sg["label"], fs, 520, hi), WHITE if hi else MUTED, "l", hi, la)
        text(ctx, sg.get("text", num(float(sg["value"]), 1) + "%"), 890, y, fs, WHITE if hi else MUTED, "r", True, la)


def s_bars(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, sc, t, a)
    rows = sc["rows"]; n = len(rows)
    mx = float(sc.get("max", max(abs(float(r["value"])) for r in rows)))
    x0, maxw = 140, 660
    step = min(145, 720 // max(n, 1))
    y0 = 640
    for i, r in enumerate(rows):
        y = y0 + i * step
        st = 0.3 + 0.25 * i if r.get("at_part") is None else c.at(r["at_part"])
        la = eo(p(t, st, 0.4)) * a
        cc = col(r.get("color"), i)
        text(ctx, r["label"], x0, y, fit(ctx, r["label"], 40, 800, bool(r.get("bold"))), WHITE, "l", bool(r.get("bold")), la)
        g = eo(p(t, st + 0.1, 1.0))
        v = float(r["value"])
        w = max(8, maxw * abs(v) / mx * g)
        bh = min(56, step - 70)
        rrect(ctx, x0, y + 24, maxw, bh, 14); ctx.set_source_rgba(1, 1, 1, 0.05 * la); ctx.fill()
        rrect(ctx, x0, y + 24, w, bh, 14); fill(ctx, cc, la)
        lab = r.get("text", num(v, int(sc.get("decimals", 0))) + sc.get("unit", ""))
        text(ctx, lab, x0 + w + 20, y + 24 + bh * 0.78, 40, cc, "l", True, la * p(t, st + 0.4, 0.3))


def s_dotgrid(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, dict(title=sc.get("title")), t, a)
    if sc.get("pill"):
        pill(ctx, sc["pill"], 540, 540, eob(p(t, 0.2, 0.5)), eo(p(t, 0.2, 0.3)) * a)
    groups = sc["groups"]
    counts = [int(round(float(g["value"]))) for g in groups]
    diff = 100 - sum(counts)
    counts[counts.index(max(counts))] += diff
    cols = []
    for i, (g, n) in enumerate(zip(groups, counts)):
        cols += [col(g.get("color"), i)] * n
    cell, r = 64, 24
    gx, gy = 540 - cell * 5 + cell / 2, 640
    st0 = c.at(sc.get("at_part", 0)) if sc.get("at_part") is not None else 0.4
    for k in range(100):
        row, cl = divmod(k, 10)
        x, y = gx + cl * cell, gy + row * cell
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.06 * a); ctx.fill()
        q = p(t, st0 + k * 0.022, 0.3)
        if q > 0:
            ctx.arc(x, y, r * eob(q), 0, 2 * math.pi); fill(ctx, cols[k], a)
    for i, g in enumerate(groups[:4]):
        la = eo(p(t, st0 + 0.3 + 0.2 * i, 0.4)) * a
        x = 110 if i % 2 == 0 else 570
        y = 1325 + (i // 2) * 58
        ctx.arc(x + 14, y - 14, 14, 0, 2 * math.pi); fill(ctx, col(g.get("color"), i), la)
        text(ctx, g["label"], x + 42, y, fit(ctx, g["label"], 36, 250, False), MUTED, "l", False, la)
        text(ctx, g.get("text", num(float(g["value"]), 1) + "%"), x + 400, y, 36, WHITE, "r", True, la)


def s_scale(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, dict(title=sc.get("title")), t, a)
    mn, mx = float(sc.get("min", 0)), float(sc.get("max", 100)); unit = sc.get("unit", "%")
    main = next((m for m in sc["markers"] if m.get("main")), sc["markers"][0])
    tmain = c.at(main.get("at_part", 1))
    m = eo(p(t, tmain, 1.6))
    dec = int(sc.get("decimals", 1))
    big = num(mn + (float(main["value"]) - mn) * m, dec) + unit
    text(ctx, big, 540, 680, 170, col(main.get("color", "gold")), "c", True, eo(p(t, 0.2, 0.4)) * a)
    if sc.get("caption"):
        text(ctx, sc["caption"], 540, 765, fit(ctx, sc["caption"], 42, 960, False), MUTED, "c", False, eo(p(t, 0.4, 0.4)) * a)
    x0, x1, ay = 120, 960, 1060

    def X(v):
        return x0 + (x1 - x0) * (float(v) - mn) / (mx - mn)
    aa = eo(p(t, 0.3, 0.5)) * a
    z = sc.get("zone")
    if z:
        za = eo(p(t, c.at(z.get("at_part", 2)) - 0.1, 0.5)) * a
        zc = col(z.get("color", "red"))
        rrect(ctx, X(z["from"]), ay - 70, X(z["to"]) - X(z["from"]), 140, 12); fill(ctx, zc, 0.22 * za)
        zx = clamp((X(z["from"]) + X(z["to"])) / 2, 200, 880)
        text(ctx, z.get("label", ""), zx, ay - 95, 32, zc, "c", True, za)
        text(ctx, z.get("label2", ""), zx, ay - 135, 32, zc, "c", True, za)
    ctx.set_line_width(6); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, ay); ctx.line_to(x1, ay); ctx.set_source_rgba(*hexc(MUTED, 0.6 * aa)); ctx.stroke()
    ticks = sc.get("ticks") or [mn + (mx - mn) * i / 4 for i in range(5)]
    for v in ticks:
        ctx.set_line_width(3); ctx.move_to(X(v), ay - 14); ctx.line_to(X(v), ay + 14)
        ctx.set_source_rgba(*hexc(MUTED, 0.6 * aa)); ctx.stroke()
        text(ctx, num(float(v), 0 if float(v).is_integer() else 1) + unit, X(v), ay + 60, 28, MUTED, "c", False, aa)
    others = [mk for mk in sc["markers"] if mk is not main]
    for j, mk in enumerate(others):
        ca = eo(p(t, c.at(mk.get("at_part", 3)), 0.5)) * a
        ctx.arc(X(mk["value"]), ay, 14, 0, 2 * math.pi); fill(ctx, "#B9C4D6", ca)
        lab = mk["label"]
        lw = tw(ctx, lab, 30, False)
        lx = clamp(X(mk["value"]) - 30, 40, 1040 - lw)
        text(ctx, lab, lx, ay - 38 - (j % 2) * 0, 30, "#B9C4D6", "l", False, ca)
    xv = X(mn + (float(main["value"]) - mn) * m)
    mc = col(main.get("color", "gold"))
    ctx.arc(xv, ay, 24, 0, 2 * math.pi); fill(ctx, mc, aa)
    ctx.arc(xv, ay, 34 + 6 * math.sin(t * 5), 0, 2 * math.pi); ctx.set_line_width(4)
    ctx.set_source_rgba(*hexc(mc, 0.5 * aa)); ctx.stroke()
    text(ctx, main["label"], clamp(xv, 160, 920), ay + 125, 36, mc, "c", True, aa)
    if sc.get("footnote"):
        fa = eo(p(t, c.at(others[0].get("at_part", 3)) if others else 1.0, 0.5)) * a
        text(ctx, sc["footnote"], 540, 1320, fit(ctx, sc["footnote"], 30, 960, False), MUTED, "c", False, fa)


def s_list(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, sc, t, a)
    items = sc["items"]; n = len(items)
    top = 600 if sc.get("subtitle") else 570
    avail = 1380 - top
    gap = 22
    ch = min(200, (avail - gap * (n - 1)) / n)
    for i, it in enumerate(items):
        st = c.at(it["at_part"]) if it.get("at_part") is not None else 0.4 + 0.3 * i
        q = eo(p(t, st, 0.45)); la = q * a
        if la <= 0.001:
            continue
        y = top + i * (ch + gap)
        cc = col(it.get("color"), i)
        ctx.save(); ctx.translate((1 - q) * 80, 0)
        rrect(ctx, 80, y, 920, ch, 28); fill(ctx, CARD, 0.95 * la)
        badge = it.get("badge", str(i + 1))
        ctx.arc(150, y + ch / 2, 36, 0, 2 * math.pi); fill(ctx, cc, la)
        text(ctx, badge, 150, y + ch / 2 + 14, fit(ctx, badge, 40, 60), DARK, "c", True, la)
        head = it.get("head", ""); body = it.get("text", "")
        hs = 42 if ch >= 150 else 36
        if head and body:
            hl = wrap(ctx, head, hs, 760)[:1]
            bl = wrap(ctx, body, 32, 760, False, False)[: max(1, int((ch - hs - 40) // 40))]
            blockh = hs + 10 + 40 * len(bl)
            yy = y + (ch - blockh) / 2 + hs * 0.85
            text(ctx, hl[0], 215, yy, fit(ctx, hl[0], hs, 760), WHITE, "l", True, la)
            for j, l in enumerate(bl):
                text(ctx, l, 215, yy + 50 + 40 * j, 32, MUTED, "l", False, la)
        else:
            ls = wrap(ctx, head or body, hs, 760)[:3]
            yy = y + ch / 2 - (len(ls) - 1) * hs * 0.6 + hs * 0.35
            for j, l in enumerate(ls):
                text(ctx, l, 215, yy + j * hs * 1.2, hs, WHITE, "l", True, la)
        ctx.restore()


def s_fact(ctx, t, c):
    sc = c.sc; a = c.out(t)
    if sc.get("kicker"):
        pill(ctx, sc["kicker"].upper(), 540, 470, eob(p(t, 0.1, 0.5)), eo(p(t, 0.1, 0.3)) * a, GOLD, DARK, 32)
    y = 620
    if sc.get("big"):
        tb = c.at(sc.get("big_at_part")) if sc.get("big_at_part") is not None else 0.3
        k = eob(p(t, tb, 0.6)); ba = eo(p(t, tb, 0.3)) * a
        bsz = fit(ctx, sc["big"], 190, 960)
        ctx.save(); ctx.translate(540, y + 120); ctx.scale(k, k)
        text(ctx, sc["big"], 0, 0, bsz, col(sc.get("big_color", "gold")), "c", True, ba)
        ctx.restore()
        y += 250
    hl = sc.get("headline", "")
    hsz = 70 if len(hl) < 40 else 60
    lines = wrap(ctx, hl, hsz, 940, True, False)[:5]
    th = c.at(sc.get("headline_at_part", 0)) if sc.get("headline_at_part") is not None else 0.4
    wi = 0
    for li, l in enumerate(lines):
        words = l.split(" ")
        font(ctx, hsz)
        lw = ctx.text_extents(l).x_advance
        x = 540 - lw / 2
        for wd in words:
            q = eo(p(t, th + wi * 0.07, 0.35)); wi += 1
            ww = tw(ctx, wd + " ", hsz)
            hcol = col(sc.get("accent", "gold")) if wd.strip(".,:!?«»") in sc.get("highlight", []) else WHITE
            ctx.save(); ctx.translate(0, (1 - q) * 30)
            text(ctx, wd, x, y + li * hsz * 1.18, hsz, hcol, "l", True, q * a)
            ctx.restore()
            x += ww
    y += len(lines) * hsz * 1.18 + 40
    if sc.get("body"):
        tb = c.at(sc.get("body_at_part", 1)) if len(c.tm["parts"]) > 1 else 1.0
        ba = eo(p(t, tb, 0.5)) * a
        for j, l in enumerate(wrap(ctx, sc["body"], 40, 900, False, False)[:5]):
            text(ctx, l, 540, y + j * 54, 40, MUTED, "c", False, ba)


def s_word(ctx, t, c):
    sc = c.sc; a = c.out(t)
    if sc.get("index"):
        pill(ctx, sc["index"], 540, 470, eob(p(t, 0.05, 0.5)), eo(p(t, 0.05, 0.3)) * a, CARD, MUTED, 34)
    q = eob(p(t, 0.15, 0.6)); qa = eo(p(t, 0.15, 0.3)) * a
    wsz = fit(ctx, sc["word"], 150, 960)
    ctx.save(); ctx.translate(540, 720); ctx.scale(q, q)
    text(ctx, sc["word"], 0, 0, wsz, GOLD, "c", True, qa)
    ctx.restore()
    if sc.get("transcription"):
        text(ctx, sc["transcription"], 540, 810, 44, MUTED, "c", False, eo(p(t, 0.5, 0.4)) * a)
    tt = c.at(sc.get("translation_at_part", 1)) if len(c.tm["parts"]) > 1 else 0.8
    ta = eo(p(t, tt, 0.4)) * a
    rrect(ctx, 140, 900, 800, 2, 1); fill(ctx, MUTED, 0.3 * ta)
    tr = sc.get("translation", "")
    text(ctx, tr, 540, 1010, fit(ctx, tr, 72, 940), WHITE, "c", True, ta)
    if sc.get("example"):
        te = c.at(sc.get("example_at_part", 2)) if len(c.tm["parts"]) > 2 else 1.5
        ea = eo(p(t, te, 0.4)) * a
        lines = wrap(ctx, sc["example"], 40, 800, True, False)[:2]
        trl = wrap(ctx, sc.get("example_tr", ""), 34, 800, False, False)[:2] if sc.get("example_tr") else []
        rrect(ctx, 100, 1090, 880, 60 + 52 * len(lines) + (10 + 44 * len(trl) if trl else 0), 28); fill(ctx, CARD, 0.95 * ea)
        for j, l in enumerate(lines):
            text(ctx, l, 540, 1165 + j * 52, 40, WHITE, "c", True, ea)
        if sc.get("example_tr"):
            for j, l in enumerate(wrap(ctx, sc["example_tr"], 34, 800, False, False)[:2]):
                text(ctx, l, 540, 1165 + len(lines) * 52 + 10 + j * 44, 34, MUTED, "c", False, ea)


def s_timeline(ctx, t, c):
    sc = c.sc; a = c.out(t)
    titles(ctx, sc, t, a)
    items = sc["items"]; n = len(items)
    top = 620; step = min(170, 740 / max(n, 1))
    lx = 250
    last = top + step * (n - 1)
    grow = eo(p(t, 0.3, 1.5))
    ctx.set_line_width(6); ctx.move_to(lx, top); ctx.line_to(lx, top + (last - top) * grow)
    ctx.set_source_rgba(*hexc(MUTED, 0.35 * a)); ctx.stroke()
    for i, it in enumerate(items):
        st = c.at(it["at_part"]) if it.get("at_part") is not None else 0.4 + 0.4 * i
        q = eo(p(t, st, 0.45)); la = q * a
        y = top + i * step
        cc = col(it.get("color"), i)
        ctx.arc(lx, y, 18 * eob(p(t, st, 0.4)) if q > 0 else 0.01, 0, 2 * math.pi); fill(ctx, cc, la)
        ctx.save(); ctx.translate((1 - q) * 50, 0)
        text(ctx, it["year"], lx - 40, y + 14, fit(ctx, it["year"], 40, 190), cc, "r", True, la)
        ls = wrap(ctx, it["text"], 38, 720, False, False)[:2]
        for j, l in enumerate(ls):
            text(ctx, l, lx + 45, y + 13 + j * 46 - (len(ls) - 1) * 23, 38, WHITE, "l", j == 0 and it.get("bold", False), la)
        ctx.restore()


def s_outro(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eob(p(t, 0.1, 0.6))
    sun(ctx, 540, 620, 80 * k, t * 0.35, a)
    q = eo(p(t, 0.3, 0.5))
    cta = sc.get("cta", "Подписывайтесь")
    text(ctx, cta, 540, 920, fit(ctx, cta, 96, 980), WHITE, "c", True, q * a)
    if sc.get("sub"):
        text(ctx, sc["sub"], 540, 995, fit(ctx, sc["sub"], 44, 960, False), MUTED, "c", False, q * a)
    src = sc.get("source_lines", [])
    if src:
        ca = eo(p(t, 0.6, 0.5)) * a
        rrect(ctx, 140, 1110, 800, 230, 32); fill(ctx, CARD, 0.95 * ca)
        text(ctx, sc.get("source_title", "Источник"), 540, 1172, 32, MUTED, "c", False, ca, spacing=1)
        text(ctx, src[0], 540, 1240, fit(ctx, src[0], 54, 740), WHITE, "c", True, ca)
        if len(src) > 1:
            text(ctx, src[1], 540, 1298, fit(ctx, src[1], 32, 740, False), MUTED, "c", False, ca)


SCENES = dict(title=s_title, counter=s_counter, donut=s_donut, bars=s_bars, dotgrid=s_dotgrid,
              scale=s_scale, list=s_list, fact=s_fact, word=s_word, timeline=s_timeline, outro=s_outro)
NO_HEADER = {"title", "outro"}


def scene_dur(sc, tm):
    tail = OUTRO_TAIL if sc["type"] == "outro" else TAIL
    return round((LEAD + tm["dur"] + tail) * FPS) / FPS


def draw(ep, idx, t, timing, offs):
    sc = ep["scenes"][idx]; tm = timing[idx]; T = scene_dur(sc, tm)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    background(ctx, offs[idx] + t)
    c = Ctx(sc, tm, T)
    if sc["type"] not in NO_HEADER and ep.get("header"):
        header(ctx, ep["header"], (eo(p(t, 0, 0.3)) if idx == 1 else 1.0) * c.out(t))
    SCENES[sc["type"]](ctx, t, c)
    subtitle(ctx, tm, t)
    a_in = eo(p(t, 0, 0.2))
    if a_in < 1:
        ctx.set_source_rgba(*hexc(BG2)[:3], 1 - a_in); ctx.paint()
    return surf


def render_scene(ep, idx, timing, offs, outdir):
    sc = ep["scenes"][idx]; T = scene_dur(sc, timing[idx]); n = round(T * FPS)
    tmp = os.path.join(outdir, f"scene{idx:02d}.part.mp4")
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                             "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(bytes(draw(ep, idx, i / FPS, timing, offs).get_data()))
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed on scene {idx}")
    os.replace(tmp, os.path.join(outdir, f"scene{idx:02d}.mp4"))
