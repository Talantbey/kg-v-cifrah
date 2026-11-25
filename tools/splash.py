"""«Splash» theme (episode "theme": "splash"): bright sky-blue water look — light gradient, water ribbons and a
wavy water line, droplets and bubbles, real-photo garnish (mint, raspberries, blueberries, lime, ice) floating
around the edges, and a splash burst around the hero fruit. Scenes are the fruit scenes from fruits.py.
"""
import math, random
import cairo
import engine as E
from engine import p, eo, eob, hexc
import fruits as F

_R = random.Random(42)
DROPS = [(_R.uniform(0, 1080), _R.uniform(0, 1920), _R.uniform(5, 24), _R.uniform(6, 28), _R.uniform(0, 6.28)) for _ in range(46)]
BUBBLES = [(_R.uniform(0, 1080), _R.uniform(0, 400), _R.uniform(3, 10), _R.uniform(30, 80)) for _ in range(40)]
BURST = [(_R.uniform(0, 2 * math.pi), _R.uniform(0.45, 1.0), _R.uniform(5, 20), _R.uniform(0, 6.28)) for _ in range(44)]


def drop(ctx, x, y, r, a):
    if a <= 0.01 or r <= 0.5:
        return
    g = cairo.RadialGradient(x - r * 0.25, y - r * 0.3, r * 0.05, x, y, r)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.10 * a); g.add_color_stop_rgba(0.75, 0.85, 0.95, 1, 0.25 * a)
    g.add_color_stop_rgba(1, 0.55, 0.78, 0.95, 0.55 * a)
    ctx.new_sub_path(); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source(g); ctx.fill()
    ctx.new_sub_path(); ctx.arc(x, y, r, 0.2, 1.9); ctx.set_source_rgba(0.1, 0.35, 0.6, 0.35 * a)
    ctx.set_line_width(max(1, r * 0.12)); ctx.stroke()
    ctx.save(); ctx.translate(x - r * 0.35, y - r * 0.4); ctx.rotate(-0.6); ctx.scale(r * 0.28, r * 0.15)
    ctx.new_sub_path(); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(1, 1, 1, 0.95 * a); ctx.fill()


def ribbons(ctx, cx, cy, R, t, a, n=7, seed=1):
    """Translucent water sheets flaring out from a centre — reads as a splash crown."""
    rnd = random.Random(seed)
    for i in range(n):
        ang = -math.pi / 2 + (i - (n - 1) / 2) * (math.pi * 1.5 / n) + 0.08 * math.sin(t * 0.9 + i)
        L = R * rnd.uniform(0.75, 1.15) * (1 + 0.04 * math.sin(t * 1.3 + i * 2))
        wdt = R * rnd.uniform(0.18, 0.3)
        ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang)
        ctx.move_to(0, -wdt * 0.2)
        ctx.curve_to(L * 0.3, -wdt * 1.2, L * 0.7, -wdt * 0.9 + 25 * math.sin(t + i), L, -wdt * 0.15)
        ctx.curve_to(L * 0.95, wdt * 0.1, L * 0.6, wdt * 0.5, 0, wdt * 0.2)
        ctx.close_path()
        g = cairo.LinearGradient(0, -wdt, 0, wdt)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.9 * a); g.add_color_stop_rgba(0.45, 0.62, 0.86, 1, 0.5 * a)
        g.add_color_stop_rgba(1, 0.3, 0.65, 0.92, 0.35 * a)
        ctx.set_source(g); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.95 * a); ctx.set_line_width(4); ctx.stroke()
        # inner highlight streak
        ctx.move_to(L * 0.15, -wdt * 0.35); ctx.curve_to(L * 0.4, -wdt * 0.85, L * 0.7, -wdt * 0.6, L * 0.9, -wdt * 0.2)
        ctx.set_source_rgba(1, 1, 1, 0.7 * a); ctx.set_line_width(3); ctx.stroke()
        ctx.restore()
        drop(ctx, cx + math.cos(ang) * L * 1.06, cy + math.sin(ang) * L * 1.06, wdt * 0.32, a)


def water_line(ctx, y0, t, a=1.0):
    ctx.move_to(0, E.H)
    ctx.line_to(0, y0)
    for x in range(0, E.W + 41, 40):
        ctx.line_to(x, y0 + 16 * math.sin(x / 120 + t * 1.6) + 9 * math.sin(x / 47 - t * 2.1))
    ctx.line_to(E.W, E.H); ctx.close_path()
    g = cairo.LinearGradient(0, y0 - 20, 0, E.H)
    g.add_color_stop_rgba(0, 0.55, 0.82, 0.98, 0.55 * a); g.add_color_stop_rgba(1, 0.05, 0.35, 0.62, 0.85 * a)
    ctx.set_source(g); ctx.fill()
    ctx.move_to(0, y0)
    for x in range(0, E.W + 41, 40):
        ctx.line_to(x, y0 + 16 * math.sin(x / 120 + t * 1.6) + 9 * math.sin(x / 47 - t * 2.1))
    ctx.set_source_rgba(1, 1, 1, 0.8 * a); ctx.set_line_width(4); ctx.stroke()


def background_splash(ctx, tg):
    g = cairo.LinearGradient(0, 0, 0, E.H)
    g.add_color_stop_rgb(0, *hexc("#F7FCFF")[:3]); g.add_color_stop_rgb(0.5, *hexc("#CDEBFA")[:3])
    g.add_color_stop_rgb(1, *hexc("#3D93CC")[:3])
    ctx.set_source(g); ctx.paint()
    for (cx, cy, r, a) in [(540 + 260 * math.sin(tg * 0.25), 380, 700, 0.55), (200 - 120 * math.sin(tg * 0.2), 1100, 520, 0.25)]:
        rg = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        rg.add_color_stop_rgba(0, 1, 1, 1, a); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(rg); ctx.paint()
    # caustic light bands
    for i in range(4):
        x = (i * 330 + tg * 25) % 1500 - 200
        ctx.save(); ctx.translate(x, 0); ctx.rotate(0.22)
        lg = cairo.LinearGradient(-60, 0, 60, 0)
        lg.add_color_stop_rgba(0, 1, 1, 1, 0); lg.add_color_stop_rgba(0.5, 1, 1, 1, 0.13); lg.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.rectangle(-60, -200, 120, 2600); ctx.set_source(lg); ctx.fill(); ctx.restore()
    water_line(ctx, 1640, tg)
    for (x, y, r, sp) in BUBBLES:
        yy = 1920 - ((y + tg * sp) % 320)
        ctx.new_sub_path(); ctx.arc(x + 6 * math.sin(tg * 2 + x), yy, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.45); ctx.set_line_width(1.5); ctx.stroke()
    for (x, y, r, sp, ph) in DROPS:
        yy = (y + tg * sp) % 1980 - 30
        drop(ctx, x + 10 * math.sin(tg * 0.7 + ph), yy, r, 0.75)


E.BG_HOOKS["splash"] = background_splash

# edge garnish slots: (x, y, size, rotation) — partly off-screen, behind content
SLOTS = [(30, 330, 260, -0.5), (1060, 470, 230, 0.4), (10, 1200, 280, 0.25), (1065, 1330, 300, -0.3),
         (1000, 250, 170, 0.1), (60, 760, 190, -0.2)]


def garnish_items(ep):
    main = F.main_kind(ep)
    items = [k for k in F.GARNISH if F.photo_surface(k) is not None]
    if main and F.photo_surface(main) is not None:
        items = [main] + items
    return items


def burst(ctx, cx, cy, R, t, t0, a):
    for (ang, spd, r, ph) in BURST:
        k = eo(p(t, t0, 1.1))
        d = R * spd * (0.15 + 0.85 * k)
        x = cx + math.cos(ang) * d + 8 * math.sin(t * 1.4 + ph)
        y = cy + math.sin(ang) * d * 0.9 + 8 * math.cos(t * 1.1 + ph) + 40 * k * k * spd
        drop(ctx, x, y, r * (0.6 + 0.4 * k), a * (0.4 + 0.6 * k) if t >= t0 else 0)


def deco_splash(ctx, ep, idx, t, T):
    sc = ep["scenes"][idx]
    typ = sc.get("type")
    q = eo(p(t, 0.0, 0.6)) * (1 - p(t, T - 0.2, 0.2))
    items = garnish_items(ep) if F.photos_on() else []
    if typ == "fruit":
        ribbons(ctx, 540, 900, 560, t, eo(p(t, 0.1, 0.6)), n=11, seed=3)
        burst(ctx, 540, 880, 520, t, 0.15, q)
        ring = [(-340, -150, 190, -0.4), (340, -170, 180, 0.5), (-350, 230, 210, 0.2), (345, 250, 220, -0.3)]
        for j, (dx, dy, s, rot) in enumerate(ring):
            if j + 1 >= len(items):
                break
            k = eo(p(t, 0.2 + 0.05 * j, 0.9))
            x = 540 + dx * (0.3 + 0.7 * k) + 8 * math.sin(t * 1.5 + j)
            y = 880 + dy * (0.3 + 0.7 * k) + 10 * math.cos(t * 1.2 + j)
            ctx.save(); ctx.translate(x, y); ctx.rotate(rot + 0.15 * math.sin(t * 0.8 + j))
            F.draw_photo(ctx, items[j + 1], 0, 0, s, q)
            ctx.restore()
        return
    if typ == "finale":
        ribbons(ctx, 540, 660, 360, t, q, n=7, seed=5)
        burst(ctx, 540, 650, 420, t, 0.05, q)
    if sc.get("deco") is False:
        return
    rnd = random.Random(idx * 7 + 1)
    order = list(range(len(SLOTS))); rnd.shuffle(order)
    n = 4 if typ != "finale" else 3
    for j, si in enumerate(order[:n]):
        if not items:
            break
        x, y, s, rot = SLOTS[si]
        kind = items[(idx + j) % len(items)]
        side = -1 if x < 540 else 1
        k = eo(p(t, 0.05 * j, 0.7))
        xx = x + side * (1 - k) * 160 + 6 * math.sin(t * 1.3 + j)
        yy = y + 10 * math.sin(t * 1.1 + j * 2)
        ctx.save(); ctx.translate(xx, yy); ctx.rotate(rot + 0.1 * math.sin(t * 0.7 + j))
        F.draw_photo(ctx, kind, 0, 0, s, q * 0.95)
        ctx.restore()


E.DECO_HOOKS["splash"] = deco_splash
