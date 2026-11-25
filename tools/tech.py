"""Tech-theme scenes (episode "theme": "tech"): hook, problem, keys, phone, laptop, cta.
Uses E.* helpers; colours are read from engine globals at draw time so the theme applies.
"""
import math
import cairo
import engine as E
from engine import p, eo, eob, clamp, text, wrap, fit, tw, rrect, fill, hexc, font

CYAN, VIOLET, PINK, WHITE = "#38BDF8", "#8B5CF6", "#F43F5E", "#F5F7FF"


def glow(ctx, cx, cy, r, color, a):
    rg = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    rg.add_color_stop_rgba(0, *hexc(color)[:3], a); rg.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(rg); ctx.arc(cx, cy, r, 0, 2 * math.pi); ctx.fill()


def stroke(ctx, color, a, w):
    ctx.set_source_rgba(*hexc(color, max(0.0, min(1.0, a)))); ctx.set_line_width(w); ctx.stroke()


# ---------------- icons (line style, s = size in px) ----------------

def icon(ctx, kind, cx, cy, s, color=CYAN, a=1.0):
    ctx.save(); ctx.translate(cx, cy)
    lw = max(4, s * 0.06)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    h = s / 2
    if kind == "laptop":
        rrect(ctx, -h * 0.8, -h * 0.65, h * 1.6, h * 1.05, s * 0.06); stroke(ctx, color, a, lw)
        ctx.move_to(-h, h * 0.55); ctx.line_to(h, h * 0.55); stroke(ctx, color, a, lw)
    elif kind == "phone":
        rrect(ctx, -h * 0.5, -h * 0.95, h, h * 1.9, s * 0.12); stroke(ctx, color, a, lw)
        ctx.move_to(-h * 0.15, h * 0.72); ctx.line_to(h * 0.15, h * 0.72); stroke(ctx, color, a, lw)
    elif kind == "globe":
        ctx.arc(0, 0, h * 0.9, 0, 2 * math.pi); stroke(ctx, color, a, lw)
        ctx.save(); ctx.scale(0.42, 1); ctx.arc(0, 0, h * 0.9, 0, 2 * math.pi); ctx.restore(); stroke(ctx, color, a, lw)
        ctx.move_to(-h * 0.9, 0); ctx.line_to(h * 0.9, 0); stroke(ctx, color, a, lw)
    elif kind == "keyboard":
        rrect(ctx, -h, -h * 0.55, s, h * 1.1, s * 0.08); stroke(ctx, color, a, lw)
        for r in range(2):
            for k in range(5):
                ctx.rectangle(-h * 0.78 + k * h * 0.36, -h * 0.3 + r * h * 0.3, h * 0.18, h * 0.14)
        ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
        ctx.move_to(-h * 0.45, h * 0.32); ctx.line_to(h * 0.45, h * 0.32); stroke(ctx, color, a, lw)
    elif kind == "ai":
        for (x, y, r) in [(-h * 0.2, h * 0.1, h * 0.7), (h * 0.55, -h * 0.55, h * 0.32)]:
            ctx.move_to(x, y - r)
            ctx.curve_to(x + r * 0.15, y - r * 0.15, x + r * 0.15, y - r * 0.15, x + r, y)
            ctx.curve_to(x + r * 0.15, y + r * 0.15, x + r * 0.15, y + r * 0.15, x, y + r)
            ctx.curve_to(x - r * 0.15, y + r * 0.15, x - r * 0.15, y + r * 0.15, x - r, y)
            ctx.curve_to(x - r * 0.15, y - r * 0.15, x - r * 0.15, y - r * 0.15, x, y - r)
            ctx.close_path(); ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
    elif kind == "warning":
        ctx.move_to(0, -h * 0.9); ctx.line_to(h * 0.95, h * 0.75); ctx.line_to(-h * 0.95, h * 0.75); ctx.close_path()
        stroke(ctx, color, a, lw)
        ctx.move_to(0, -h * 0.3); ctx.line_to(0, h * 0.2); stroke(ctx, color, a, lw)
        ctx.arc(0, h * 0.45, lw * 0.6, 0, 2 * math.pi); ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
    elif kind == "bell":
        ctx.move_to(-h * 0.7, h * 0.45); ctx.curve_to(-h * 0.55, h * 0.2, -h * 0.6, -h * 0.75, 0, -h * 0.75)
        ctx.curve_to(h * 0.6, -h * 0.75, h * 0.55, h * 0.2, h * 0.7, h * 0.45); ctx.close_path(); stroke(ctx, color, a, lw)
        ctx.arc(0, h * 0.62, h * 0.14, 0, math.pi); stroke(ctx, color, a, lw)
    elif kind == "check":
        ctx.move_to(-h * 0.55, 0); ctx.line_to(-h * 0.12, h * 0.42); ctx.line_to(h * 0.6, -h * 0.4); stroke(ctx, color, a, lw * 1.3)
    elif kind == "lock":
        rrect(ctx, -h * 0.65, -h * 0.1, h * 1.3, h * 0.95, s * 0.06); stroke(ctx, color, a, lw)
        ctx.arc(0, -h * 0.1, h * 0.42, math.pi, 0); stroke(ctx, color, a, lw)
    elif kind == "battery":
        rrect(ctx, -h * 0.85, -h * 0.4, h * 1.55, h * 0.8, s * 0.06); stroke(ctx, color, a, lw)
        ctx.rectangle(h * 0.75, -h * 0.15, h * 0.12, h * 0.3); ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
        rrect(ctx, -h * 0.7, -h * 0.25, h * 0.7, h * 0.5, 4); ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
    elif kind == "wifi":
        for i, r in enumerate([0.9, 0.6, 0.3]):
            ctx.arc(0, h * 0.45, h * r, -math.pi * 0.75, -math.pi * 0.25); stroke(ctx, color, a, lw)
        ctx.arc(0, h * 0.45, lw * 0.7, 0, 2 * math.pi); ctx.set_source_rgba(*hexc(color, a)); ctx.fill()
    ctx.restore()


def icon_badge(ctx, kind, cx, cy, s, color, a, t):
    if a <= 0:
        return
    glow(ctx, cx, cy, s * 1.3, color, 0.35 * a)
    ctx.arc(cx, cy, s * 0.62, 0, 2 * math.pi); fill(ctx, "#0E1638", 0.9 * a)
    ctx.arc(cx, cy, s * 0.62, 0, 2 * math.pi); stroke(ctx, color, 0.8 * a, 4)
    ctx.arc(cx, cy, s * (0.72 + 0.04 * math.sin(t * 4)), 0, 2 * math.pi); stroke(ctx, color, 0.25 * a, 3)
    icon(ctx, kind, cx, cy, s * 0.62, color, a)


def rich_line(ctx, line, cx, y, size, hl, a, scale=1.0, hcol=None, base=None):
    """Centered line, words in hl drawn in accent colour."""
    hcol = hcol or CYAN
    base = base or WHITE
    font(ctx, size)
    w = ctx.text_extents(line).x_advance
    x = cx - w / 2
    ctx.save(); ctx.translate(cx, y - size * 0.35); ctx.scale(scale, scale); ctx.translate(-cx, -(y - size * 0.35))
    for wd in line.split(" "):
        key = wd.strip(".,:!?«»\"()").lower()
        c = hcol if key in hl else base
        text(ctx, wd, x, y, size, c, "l", True, a)
        x += tw(ctx, wd + " ", size)
    ctx.restore()


def chip(ctx, s, cx, cy, a, color=None, size=32):
    if a <= 0 or not s:
        return
    color = color or CYAN
    w = tw(ctx, s, size) + 60
    rrect(ctx, cx - w / 2, cy - size * 0.9, w, size * 1.8, size * 0.9); fill(ctx, color, 0.14 * a)
    rrect(ctx, cx - w / 2, cy - size * 0.9, w, size * 1.8, size * 0.9); stroke(ctx, color, 0.8 * a, 2)
    text(ctx, s, cx, cy + size * 0.36, size, color, "c", True, a)


# ---------------- scenes ----------------

def s_hook(ctx, t, c):
    sc = c.sc; a = c.out(t)
    hl = [w.lower() for w in sc.get("highlight", [])]
    if sc.get("icon"):
        k = eob(p(t, 0.0, 0.5))
        icon_badge(ctx, sc["icon"], 540, 560, 230 * k, CYAN, eo(p(t, 0, 0.3)) * a, t)
    lines = sc.get("lines") or wrap(ctx, sc.get("text", ""), 100, 960, True, False)
    n = len(lines)
    size = min(fit(ctx, max(lines, key=len), 112, 960), 112 if n <= 2 else 96)
    y0 = 860 - (n - 1) * size * 0.6 + (40 if sc.get("icon") else -120)
    shake = 7 * math.sin(t * 60) * (1 - p(t, 0.15, 0.3)) if t < 0.45 else 0
    ctx.save(); ctx.translate(shake, 0)
    for i, l in enumerate(lines):
        st = 0.08 + 0.13 * i
        q = p(t, st, 0.32)
        sc_k = 1.35 - 0.35 * eob(q)
        rich_line(ctx, l, 540, y0 + i * size * 1.18, size, hl, eo(q) * a, sc_k)
    ctx.restore()
    chip(ctx, sc.get("chip"), 540, y0 + n * size * 1.18 + 70, eo(p(t, 0.5, 0.3)) * a)


def s_problem(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eob(p(t, 0.05, 0.5))
    icon_badge(ctx, sc.get("icon", "warning"), 540, 600, 220 * k, sc.get("color", PINK), eo(p(t, 0, 0.3)) * a, t)
    hl = [w.lower() for w in sc.get("highlight", [])]
    lines = wrap(ctx, sc.get("headline", ""), 70, 940, True, False)[:3]
    for i, l in enumerate(lines):
        q = eo(p(t, 0.2 + 0.1 * i, 0.4))
        ctx.save(); ctx.translate(0, (1 - q) * 30)
        rich_line(ctx, l, 540, 900 + i * 84, 70, hl, q * a, hcol=sc.get("color", PINK))
        ctx.restore()
    if sc.get("body"):
        tb = c.at(sc.get("body_at_part", 1)) if len(c.tm["parts"]) > 1 else 0.8
        ba = eo(p(t, tb, 0.4)) * a
        for j, l in enumerate(wrap(ctx, sc["body"], 40, 900, False, False)[:3]):
            text(ctx, l, 540, 900 + len(lines) * 84 + 50 + j * 54, 40, E.MUTED, "c", False, ba)


def keycap(ctx, label, cx, cy, h, pressed, a):
    size = h * 0.34 if len(label) > 2 else h * 0.42
    w = max(h, tw(ctx, label, size) + h * 0.55)
    dy = h * 0.06 * pressed
    x, y = cx - w / 2, cy - h / 2
    if pressed > 0:
        glow(ctx, cx, cy, w * 0.9, CYAN, 0.35 * pressed * a)
    rrect(ctx, x, y + h * 0.1, w, h, h * 0.18); fill(ctx, "#050A1E", 0.9 * a)          # depth
    rrect(ctx, x, y + dy, w, h, h * 0.18)
    g = cairo.LinearGradient(0, y, 0, y + h)
    top = "#1E2A5C" if pressed < 0.5 else "#16306A"
    g.add_color_stop_rgba(0, *hexc(top)[:3], a); g.add_color_stop_rgba(1, *hexc("#121A40")[:3], a)
    ctx.set_source(g); ctx.fill()
    rrect(ctx, x, y + dy, w, h, h * 0.18)
    stroke(ctx, CYAN if pressed > 0.3 else "#3B4A85", (0.4 + 0.6 * pressed) * a, 3)
    text(ctx, label, cx, cy + dy + size * 0.36, size, WHITE if pressed < 0.3 else CYAN, "c", True, a)
    return w


def keys_row(ctx, keys, cx, cy, h, t, start, a, step=0.28, sep="+"):
    gap = h * 0.45
    font(ctx, h * 0.4)
    widths = [max(h, tw(ctx, k, h * (0.34 if len(k) > 2 else 0.42)) + h * 0.55) for k in keys]
    total = sum(widths) + gap * (len(keys) - 1)
    sc = min(1.0, 980 / total)
    ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc)
    x = -total / 2
    for i, (k, w) in enumerate(zip(keys, widths)):
        appear = eob(p(t, start - 0.5 + 0.08 * i, 0.35))
        pr = eo(p(t, start + step * i, 0.15))
        ctx.save(); ctx.translate(x + w / 2, 0); ctx.scale(appear, appear)
        keycap(ctx, k, 0, 0, h, pr, a)
        ctx.restore()
        if i < len(keys) - 1 and sep:
            text(ctx, sep, x + w + gap / 2, h * 0.16, h * 0.42, E.MUTED, "c", True, a * appear)
        x += w + gap
    ctx.restore()


def s_keys(ctx, t, c):
    sc = c.sc; a = c.out(t)
    if sc.get("title"):
        text(ctx, sc["title"], 540, 470, fit(ctx, sc["title"], 58, 960), WHITE, "c", True, eo(p(t, 0, 0.35)) * a)
    chip(ctx, sc.get("chip"), 540, 560, eo(p(t, 0.1, 0.35)) * a)
    start = c.at(sc["at_part"]) if sc.get("at_part") is not None else 0.6
    keys_row(ctx, sc["keys"], 540, 850, 190, t, start, a, step=sc.get("step", 0.28), sep=sc.get("sep", "+"))
    if sc.get("result"):
        tr = start + 0.3 * len(sc["keys"]) + 0.2
        if sc.get("result_at_part") is not None:
            tr = c.at(sc["result_at_part"])
        q = eo(p(t, tr, 0.4)); ra = q * a
        lines = wrap(ctx, sc["result"], 42, 760, True, False)[:3]
        bh = 70 + 54 * len(lines)
        ctx.save(); ctx.translate(0, (1 - q) * 40)
        rrect(ctx, 90, 1080, 900, bh, 30); fill(ctx, E.CARD, 0.95 * ra)
        rrect(ctx, 90, 1080, 900, bh, 30); stroke(ctx, CYAN, 0.35 * ra, 2)
        ctx.arc(170, 1080 + bh / 2, 38, 0, 2 * math.pi); fill(ctx, CYAN, 0.18 * ra)
        icon(ctx, "check", 170, 1080 + bh / 2, 60, CYAN, ra)
        for j, l in enumerate(lines):
            text(ctx, l, 240, 1080 + bh / 2 - (len(lines) - 1) * 27 + 15 + j * 54, 42, WHITE, "l", True, ra)
        ctx.restore()


# ---- UI screens shared by phone and laptop ----

def screen_times(c, screens):
    starts = []
    for k, s in enumerate(screens):
        if s.get("at_part") is not None:
            starts.append(c.at(s["at_part"]))
        else:
            starts.append(0.2 if k == 0 else starts[-1] + 1.6)
    return starts


def toggle(ctx, x, y, on, a, sc=1.0):
    w, h = 76 * sc, 44 * sc
    rrect(ctx, x - w, y - h / 2, w, h, h / 2)
    ctx.set_source_rgba(*hexc("#3B4A85" if on < 0.5 else "#22C55E", a)); ctx.fill()
    kx = x - w + h / 2 + (w - h) * on
    ctx.arc(kx, y, h * 0.4, 0, 2 * math.pi); fill(ctx, "#FFFFFF", a)


def draw_ui(ctx, scr, x, y, w, h, t, t_tap, a, small=False, back=False):
    """Draw one settings-like screen in rect; tap ripple on row scr['tap'] at t_tap."""
    fs = 26 if small else 36
    rh = 62 if small else 96
    pad = 22 if small else 26
    ty = y + (52 if small else 120)
    if back:
        ctx.move_to(x + pad + 12, ty - fs * 0.75); ctx.line_to(x + pad, ty - fs * 0.35); ctx.line_to(x + pad + 12, ty + fs * 0.05)
        stroke(ctx, CYAN, a, 4)
    title = scr.get("title", "")
    text(ctx, title, x + pad + (30 if back else 0), ty, fit(ctx, title, fs + 8, w - 2 * pad - 40), WHITE, "l", True, a)
    ry = ty + (24 if small else 40)
    tap = scr.get("tap")
    for i, row in enumerate(scr.get("rows", [])):
        if isinstance(row, str):
            row = {"label": row}
        yy = ry + i * (rh + (8 if small else 14))
        if yy + rh > y + h - 10:
            break
        q = eo(p(t, 0.05 * i, 0.3))
        hit = (i == tap)
        pr = p(t, t_tap, 0.25) if hit else 0
        rrect(ctx, x + pad, yy, w - 2 * pad, rh, rh * 0.22)
        fill(ctx, "#1A2552" if not hit else ("#1A2552" if pr <= 0 else "#1E3A7A"), 0.95 * a * q)
        if hit and pr > 0:
            rrect(ctx, x + pad, yy, w - 2 * pad, rh, rh * 0.22); stroke(ctx, CYAN, a * min(1, pr * 2), 3)
        lx = x + pad + (20 if small else 28)
        if row.get("icon"):
            icon(ctx, row["icon"], lx + fs * 0.6, yy + rh / 2, fs * 1.2, CYAN, a * q)
            lx += fs * 1.6
        label = row["label"]
        lab_max = w - 2 * pad - (lx - x - pad) - (150 if row.get("value") or row.get("toggle") is not None else 60)
        lsz = fit(ctx, label, fs, lab_max, hit)
        if lsz < fs * 0.82:
            two = wrap(ctx, label, int(fs * 0.8), lab_max, hit, True)[:2]
            if len(two) == 2:
                z = int(fs * 0.8)
                for j, l2 in enumerate(two):
                    text(ctx, l2, lx, yy + rh / 2 - z * 0.62 + z * 0.36 + j * z * 1.2, fit(ctx, l2, z, lab_max, hit), WHITE, "l", hit, a * q)
            else:
                text(ctx, label, lx, yy + rh / 2 + fs * 0.36, lsz, WHITE, "l", hit, a * q)
        else:
            text(ctx, label, lx, yy + rh / 2 + fs * 0.36, lsz, WHITE, "l", hit, a * q)
        rx = x + w - pad - (18 if small else 26)
        if row.get("toggle") is not None:
            on = float(row["toggle"])
            if hit and row.get("toggle_to") is not None:
                on = on + (float(row["toggle_to"]) - on) * eo(p(t, t_tap + 0.1, 0.3))
            toggle(ctx, rx, yy + rh / 2, on, a * q, 0.75 if small else 1.0)
        else:
            if row.get("value"):
                vs = fs - 6
                text(ctx, row["value"], rx - 30, yy + rh / 2 + vs * 0.36, fit(ctx, row["value"], vs, 220, False), E.MUTED, "r", False, a * q)
            ctx.move_to(rx - 10, yy + rh / 2 - 10); ctx.line_to(rx, yy + rh / 2); ctx.line_to(rx - 10, yy + rh / 2 + 10)
            stroke(ctx, E.MUTED, 0.8 * a * q, 3)
        if hit and 0 < p(t, t_tap, 0.6) < 1:
            r = (20 + 140 * eo(p(t, t_tap, 0.6))) * (0.6 if small else 1)
            cx = x + w * 0.62
            ctx.arc(cx, yy + rh / 2, r, 0, 2 * math.pi)
            fill(ctx, "#FFFFFF", 0.35 * (1 - p(t, t_tap, 0.6)) * a)
            ctx.arc(cx, yy + rh / 2, 16 * (0.6 if small else 1), 0, 2 * math.pi); fill(ctx, "#FFFFFF", 0.55 * (1 - p(t, t_tap + 0.3, 0.3)) * a)


def run_screens(ctx, c, screens, x, y, w, h, t, a, small=False):
    starts = screen_times(c, screens)
    ctx.save(); rrect(ctx, x, y, w, h, 8 if small else 40); ctx.clip()
    for k, scr in enumerate(screens):
        st = starts[k]; nxt = starts[k + 1] if k + 1 < len(screens) else 1e9
        if t < st - 0.01 and k > 0:
            continue
        if t > nxt + 0.4:
            continue
        slide_in = eo(p(t, st, 0.35)) if k > 0 else 1.0
        slide_out = eo(p(t, nxt, 0.35)) if nxt < 1e9 else 0.0
        dx = (1 - slide_in) * w - slide_out * w * 0.3
        if scr.get("tap_at_part") is not None:
            t_tap = c.at(scr["tap_at_part"])
        elif nxt < 1e9:
            t_tap = nxt - 0.65
        else:
            t_tap = st + 0.9
        ctx.save(); ctx.translate(dx, 0)
        rrect(ctx, x, y, w, h, 0); fill(ctx, "#0D1433", 1.0 * a)
        draw_ui(ctx, scr, x, y, w, h, t - st, t_tap - st, a * (1 - 0.5 * slide_out), small, back=k > 0)
        ctx.restore()
    ctx.restore()


def toast(ctx, s, cx, cy, maxw, q, a, size=34):
    if q <= 0:
        return
    lines = wrap(ctx, s, size, maxw - 120, True, False)[:2]
    w = min(maxw, max(tw(ctx, l, size) for l in lines) + 130)
    h = 40 + size * 1.25 * len(lines)
    ctx.save(); ctx.translate(0, (1 - q) * 40)
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, 22); fill(ctx, "#F5F7FF", 0.96 * q * a)
    ctx.arc(cx - w / 2 + 50, cy, 20, 0, 2 * math.pi); fill(ctx, "#22C55E", q * a)
    icon(ctx, "check", cx - w / 2 + 50, cy, 30, "#FFFFFF", q * a)
    for j, l in enumerate(lines):
        text(ctx, l, cx - w / 2 + 90, cy - (len(lines) - 1) * size * 0.62 + size * 0.36 + j * size * 1.25, size, "#0B1220", "l", True, q * a)
    ctx.restore()


def s_phone(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eo(p(t, 0, 0.45))
    pw, ph = 540, 1050
    x, y = 540 - pw / 2, 322 + (1 - k) * 120
    glow(ctx, 540, y + ph / 2, 620, VIOLET, 0.22 * a)
    rrect(ctx, x - 16, y - 16, pw + 32, ph + 32, 84); fill(ctx, "#070B1C", a)
    rrect(ctx, x - 16, y - 16, pw + 32, ph + 32, 84); stroke(ctx, "#5B6BB0", 0.8 * a, 3)
    sx, sy, sw, sh = x, y, pw, ph
    ctx.save(); rrect(ctx, sx, sy, sw, sh, 68); ctx.clip()
    run_screens(ctx, c, sc["screens"], sx, sy + 70, sw, sh - 70, t, a)
    rrect(ctx, sx, sy, sw, 70, 0); fill(ctx, "#0D1433", a)
    text(ctx, "9:41", sx + 70, sy + 50, 28, WHITE, "l", True, a)
    icon(ctx, "wifi", sx + sw - 120, sy + 40, 34, WHITE, a); icon(ctx, "battery", sx + sw - 70, sy + 42, 40, WHITE, a)
    rrect(ctx, 540 - 70, sy + 18, 140, 36, 18); fill(ctx, "#000000", a)  # island
    if sc.get("toast"):
        tq = eob(p(t, c.at(sc["toast"].get("at_part", len(c.tm["parts"]) - 1)) + float(sc["toast"].get("delay", 0)), 0.5))
        toast(ctx, sc["toast"]["text"], 540, sy + sh - 150, sw - 40, clamp(tq, 0, 1.2), a, 30)
    ctx.restore()


def s_laptop(ctx, t, c):
    sc = c.sc; a = c.out(t)
    if sc.get("title"):
        text(ctx, sc["title"], 540, 405, fit(ctx, sc["title"], 52, 960), WHITE, "c", True, eo(p(t, 0, 0.35)) * a)
    chip(ctx, sc.get("chip"), 540, 318, eo(p(t, 0.1, 0.3)) * a, size=28)
    k = eo(p(t, 0, 0.45))
    oy = (1 - k) * 80
    X0, Y0, LW, LH = 90, 480 + oy, 900, 570
    glow(ctx, 540, Y0 + LH / 2, 700, CYAN, 0.14 * a)
    rrect(ctx, X0, Y0, LW, LH, 26); fill(ctx, "#070B1C", a)
    rrect(ctx, X0, Y0, LW, LH, 26); stroke(ctx, "#5B6BB0", 0.8 * a, 3)
    ctx.move_to(X0 - 50, Y0 + LH + 6); ctx.line_to(X0 + LW + 50, Y0 + LH + 6)
    ctx.line_to(X0 + LW + 20, Y0 + LH + 46); ctx.line_to(X0 - 20, Y0 + LH + 46); ctx.close_path()
    g = cairo.LinearGradient(0, Y0 + LH, 0, Y0 + LH + 46)
    g.add_color_stop_rgba(0, *hexc("#3A4680")[:3], a); g.add_color_stop_rgba(1, *hexc("#141B3D")[:3], a)
    ctx.set_source(g); ctx.fill()
    rrect(ctx, 540 - 80, Y0 + LH + 6, 160, 12, 6); fill(ctx, "#0B1030", a)
    sx, sy, sw, sh = X0 + 20, Y0 + 20, LW - 40, LH - 40
    ctx.save(); rrect(ctx, sx, sy, sw, sh, 8); ctx.clip()
    rrect(ctx, sx, sy, sw, sh, 0); fill(ctx, "#0D1433", a)
    # window chrome
    rrect(ctx, sx, sy, sw, 44, 0); fill(ctx, "#151E47", a)
    for i, cc in enumerate(["#F43F5E", "#FBBF24", "#22C55E"]):
        ctx.arc(sx + 26 + i * 26, sy + 22, 8, 0, 2 * math.pi); fill(ctx, cc, a)
    top = sy + 44
    if sc.get("address"):
        rrect(ctx, sx + 110, sy + 8, sw - 140, 28, 14); fill(ctx, "#0B1030", a)
        icon(ctx, "lock", sx + 132, sy + 22, 18, E.MUTED, a)
        text(ctx, sc["address"], sx + 150, sy + 30, 20, E.MUTED, "l", False, a)
    if sc.get("screens"):
        run_screens(ctx, c, sc["screens"], sx, top, sw, sh - 44, t, a, small=True)
    if sc.get("snip"):
        ts = c.at(sc["snip"].get("at_part", 1))
        q = p(t, ts, 0.25)
        if q > 0:
            rrect(ctx, sx, top, sw, sh - 44, 0); fill(ctx, "#000000", 0.45 * q * a)
            g2 = eo(p(t, ts + 0.25, 0.8))
            rx0, ry0 = sx + sw * 0.18, top + (sh - 44) * 0.2
            rw, rh = sw * 0.5 * g2, (sh - 44) * 0.5 * g2
            if rw > 2:
                ctx.set_dash([14, 10]); rrect(ctx, rx0, ry0, rw, rh, 4); stroke(ctx, "#FFFFFF", a, 3); ctx.set_dash([])
            ctx.move_to(rx0 + rw, ry0 + rh); ctx.line_to(rx0 + rw + 14, ry0 + rh + 30); ctx.line_to(rx0 + rw + 22, ry0 + rh + 18)
            ctx.line_to(rx0 + rw + 36, ry0 + rh + 22); ctx.close_path(); fill(ctx, "#FFFFFF", q * a)
    if sc.get("toast"):
        tq = eob(p(t, c.at(sc["toast"].get("at_part", len(c.tm["parts"]) - 1)) + float(sc["toast"].get("delay", 0)), 0.5))
        toast(ctx, sc["toast"]["text"], sx + sw - 330, sy + sh - 70, 620, clamp(tq, 0, 1.2), a, 26)
    ctx.restore()
    if sc.get("keys"):
        start = c.at(sc.get("keys_at_part", 0)) + 0.35
        keys_row(ctx, sc["keys"], 540, 1250 + oy * 0.3, 120, t, start, a)


def s_cta(ctx, t, c):
    sc = c.sc; a = c.out(t)
    k = eob(p(t, 0.05, 0.5))
    ang = 0.25 * math.sin(t * 9) * (1 - p(t, 0.4, 1.2))
    ctx.save(); ctx.translate(540, 620); ctx.rotate(ang); ctx.translate(-540, -620)
    icon_badge(ctx, "bell", 540, 620, 230 * k, VIOLET, eo(p(t, 0, 0.3)) * a, t)
    ctx.restore()
    q = eo(p(t, 0.25, 0.4))
    cta = sc.get("cta", "Подпишись")
    text(ctx, cta, 540, 900, fit(ctx, cta, 104, 980), WHITE, "c", True, q * a)
    if sc.get("sub"):
        text(ctx, sc["sub"], 540, 980, fit(ctx, sc["sub"], 44, 960, False), E.MUTED, "c", False, q * a)
    if sc.get("save"):
        chip(ctx, sc["save"], 540, 1110, eo(p(t, 0.6, 0.4)) * a, VIOLET, 34)
    if sc.get("source"):
        text(ctx, sc["source"], 540, 1250, fit(ctx, sc["source"], 28, 960, False), E.MUTED, "c", False, eo(p(t, 0.8, 0.4)) * a)


E.SCENES.update(hook=s_hook, problem=s_problem, keys=s_keys, phone=s_phone, laptop=s_laptop, cta=s_cta)
