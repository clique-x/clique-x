"""Generates the animated SVG assets for the clique-x GitHub profile.
Real 3D: shapes are rotated + perspective-projected in Python for every frame,
then played back with SMIL <animate> on path `d` (works inside GitHub READMEs)."""
import math, os, random, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(OUT, exist_ok=True)

TEAL, DEEP, CORAL, MINT, SNOW = "#0E6B76", "#0B2E33", "#EE5A3C", "#5FD3C6", "#F4FBFA"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- 3D helpers
def project(p, theta, pitch, cx, cy, scale, dist=4.0):
    x, y, z = p
    ct, st = math.cos(theta), math.sin(theta)
    x1, z1 = x * ct + z * st, -x * st + z * ct
    cp, sp = math.cos(pitch), math.sin(pitch)
    y2, z2 = y * cp - z1 * sp, y * sp + z1 * cp
    f = dist / (dist + z2)
    return cx + x1 * scale * f, cy - y2 * scale * f


def path_frames(polylines, frames, pitch, cx, cy, scale, dist=4.0, tilt=0.0, dec=1):
    """polylines: list of lists of 3D points. returns list of `d` strings, one per frame."""
    out = []
    for i in range(frames + 1):
        th = 2 * math.pi * i / frames + tilt
        parts = []
        for line in polylines:
            pts = [project(p, th, pitch, cx, cy, scale, dist) for p in line]
            parts.append("M" + "L".join(f"{x:.{dec}f} {y:.{dec}f}" for x, y in pts))
        out.append("".join(parts))
    return out


def anim_path(polylines, frames, dur, pitch, cx, cy, scale, attrs, dist=4.0, dec=1):
    ds = path_frames(polylines, frames, pitch, cx, cy, scale, dist, dec=dec)
    return (f'<path d="{ds[0]}" {attrs}>'
            f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{";".join(ds)}"/>'
            f'</path>')


def ring(r, n, y=0.0, axis="y", c=(0, 0, 0)):
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        if axis == "y":
            pts.append((c[0] + r * math.cos(a), y, c[2] + r * math.sin(a)))
        elif axis == "z":
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a), y))
        else:
            pts.append((y, c[1] + r * math.cos(a), c[2] + r * math.sin(a)))
    return pts


# ---------------------------------------------------------------- shapes
def terrain(n):
    def h(x, z):
        v = 1.05 * math.exp(-(x * x + z * z) * 2.4)
        v += 0.55 * math.exp(-((x - 0.55) ** 2 + (z + 0.35) ** 2) * 7)
        v += 0.45 * math.exp(-((x + 0.5) ** 2 + (z - 0.45) ** 2) * 8)
        v += 0.04 * math.sin(x * 9 + z * 4) * math.cos(z * 7)
        return v * 0.95 - 0.35
    g = [[(-1 + 2 * i / (n - 1), 0, -1 + 2 * j / (n - 1)) for j in range(n)] for i in range(n)]
    g = [[(x, h(x, z), z) for (x, _, z) in row] for row in g]
    rows = [row for row in g]
    cols = [[g[i][j] for i in range(n)] for j in range(n)]
    return rows + cols


def box(w, h, d):
    v = [(sx * w, sy * h, sz * d) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    e = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    return [[v[a], v[b]] for a, b in e]


def phone():
    lines = box(0.5, 0.95, 0.06)
    s = [(-0.42, -0.85, 0.061), (0.42, -0.85, 0.061), (0.42, 0.85, 0.061), (-0.42, 0.85, 0.061), (-0.42, -0.85, 0.061)]
    lines.append(s)  # screen
    cam = [(x, y, -0.065) for x, y, _ in ring(0.13, 16, 0, "z", (0.22, 0.68, 0))]
    cam2 = [(x, y, -0.065) for x, y, _ in ring(0.07, 12, 0, "z", (0.22, 0.68, 0))]
    lines += [cam, cam2]
    return lines


def globe():
    lines = [ring(math.cos(la) * 0.95, 28, math.sin(la) * 0.95) for la in (-1.0, -0.5, 0, 0.5, 1.0)]
    for k in range(6):
        a = math.pi * k / 6
        pts = []
        for t in range(29):
            b = 2 * math.pi * t / 28
            pts.append((0.95 * math.cos(b) * math.cos(a), 0.95 * math.sin(b), 0.95 * math.cos(b) * math.sin(a)))
        lines.append(pts)
    return lines


def pipe():
    lines, n = [], 18
    for x in (-0.95, 0.95):
        lines.append(ring(0.42, n, x, "x"))
        lines.append(ring(0.30, n, x, "x"))
    for k in range(0, n, 3):
        a = 2 * math.pi * k / n
        lines.append([(-0.95, 0.42 * math.cos(a), 0.42 * math.sin(a)), (0.95, 0.42 * math.cos(a), 0.42 * math.sin(a))])
    return lines


def torus(R=0.65, r=0.26, nu=14, nv=10):
    lines = []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        lines.append([((R + r * math.cos(v)) * math.cos(u), r * math.sin(v), (R + r * math.cos(v)) * math.sin(u))
                      for v in [2 * math.pi * k / 16 for k in range(17)]])
    for j in range(0, nv, 2):
        v = 2 * math.pi * j / nv
        lines.append([((R + r * math.cos(v)) * math.cos(u), r * math.sin(v), (R + r * math.cos(v)) * math.sin(u))
                      for u in [2 * math.pi * k / 28 for k in range(29)]])
    return lines


def icosa():
    p = (1 + 5 ** 0.5) / 2
    v = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p), (0, -1, -p), (0, 1, -p),
         (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    s = 1 / math.sqrt(1 + p * p)
    v = [(a * s, b * s, c * s) for a, b, c in v]
    e = set()
    for i in range(12):
        for j in range(i + 1, 12):
            if abs(sum((v[i][k] - v[j][k]) ** 2 for k in range(3)) - (2 * s) ** 2) < 1e-6:
                e.add((i, j))
    return [[v[a], v[b]] for a, b in e]


# ---------------------------------------------------------------- shared defs
def stars(w, h, n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.choice([0.6, 0.8, 1, 1.3])
        d, b = rnd.uniform(2, 5), rnd.uniform(0, 4)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff">'
                   f'<animate attributeName="opacity" values="0.15;1;0.15" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(out)


# ---------------------------------------------------------------- HERO
def hero():
    W, H = 1200, 440
    mtn = anim_path(terrain(12), 48, 18, 0.42, 870, 262, 212,
                    'fill="none" stroke="url(#mg)" stroke-width="1.4" stroke-linejoin="round" filter="url(#glow)"',
                    dist=4.2)
    ring_ = anim_path([ring(1.45, 48, -0.42)], 24, 18, 0.42, 870, 262, 212,
                      'fill="none" stroke="#5FD3C6" stroke-opacity=".35" stroke-width="1" stroke-dasharray="4 8"', dist=4.2)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#04161A"/><stop offset=".65" stop-color="{DEEP}"/><stop offset="1" stop-color="#0D3B41"/></linearGradient>
 <linearGradient id="mg" x1="0" y1="60" x2="0" y2="400" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{SNOW}"/><stop offset=".28" stop-color="{CORAL}"/><stop offset=".6" stop-color="{MINT}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>
 <linearGradient id="ng" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{SNOW}"/><stop offset=".45" stop-color="{MINT}"/><stop offset=".55" stop-color="{CORAL}"/><stop offset="1" stop-color="{SNOW}"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="6s" repeatCount="indefinite"/></linearGradient>
 <radialGradient id="sun"><stop offset="0" stop-color="#FFD9A8"/><stop offset=".5" stop-color="{CORAL}" stop-opacity=".9"/><stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></radialGradient>
 <radialGradient id="halo" cx=".75" cy=".6" r=".5"><stop offset="0" stop-color="{TEAL}" stop-opacity=".55"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>
 <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <clipPath id="r"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<g clip-path="url(#r)">
 <rect width="{W}" height="{H}" fill="url(#bg)"/>
 <rect width="{W}" height="{H}" fill="url(#halo)"/>
 {stars(W, 300, 70, 7)}
 <g><circle r="46" fill="url(#sun)"/><animateMotion dur="18s" repeatCount="indefinite" path="M690 300 Q905 -60 1120 300"/></g>
 {ring_}
 {mtn}
 <g font-family="{MONO}" font-size="11" fill="{MINT}" opacity=".55">
  <text x="1160" y="404" text-anchor="end">30.0°N 78.1°E · HARIDWAR · REAL 3D, RENDERED IN SVG</text>
 </g>
 <g font-family="{SANS}">
  <text x="70" y="112" font-family="{MONO}" font-size="16" fill="{CORAL}" letter-spacing="4">&gt; HELLO, WORLD_
   <animate attributeName="opacity" values="1;.35;1" dur="2.4s" repeatCount="indefinite"/></text>
  <text x="66" y="200" font-size="86" font-weight="800" fill="url(#ng)" letter-spacing="-2">Shashank</text>
  <text x="70" y="246" font-size="24" font-weight="600" fill="{SNOW}">Full-stack &amp; 3D web builder</text>
  <text x="70" y="280" font-size="18" fill="{MINT}">@clique-x · Earthclique Technologies</text>
  <g font-family="{MONO}" font-size="14">
   <rect x="70" y="316" width="154" height="34" rx="17" fill="none" stroke="{CORAL}"/><text x="147" y="338" text-anchor="middle" fill="{CORAL}">Next.js · R3F</text>
   <rect x="236" y="316" width="132" height="34" rx="17" fill="none" stroke="{MINT}"/><text x="302" y="338" text-anchor="middle" fill="{MINT}">GSAP motion</text>
   <rect x="380" y="316" width="156" height="34" rx="17" fill="none" stroke="{SNOW}" stroke-opacity=".6"/><text x="458" y="338" text-anchor="middle" fill="{SNOW}">Flutter · SaaS</text>
  </g>
 </g>
 <rect y="-40" width="{W}" height="40" fill="{MINT}" opacity=".05"><animate attributeName="y" values="-40;{H}" dur="5s" repeatCount="indefinite"/></rect>
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="22" fill="none" stroke="{MINT}" stroke-opacity=".25"/>
</svg>'''
    return svg


# ---------------------------------------------------------------- TERMINAL
def terminal():
    W = 1200
    lines = [
        ("p", "whoami"),
        ("o", "shashank @ clique-x · builds things people scroll slowly through"),
        ("p", "cat stack.txt"),
        ("o", "Next.js 16 · React 19 · TypeScript · Three.js / R3F · GSAP · Lenis · Tailwind"),
        ("o", "Flutter · Medusa · Fastify · Drizzle · Postgres · Razorpay · PHP · SuperCollider"),
        ("p", "ls ./shipped | wc -l"),
        ("o", "20 repos · storefronts · SaaS · booking engines · ERP · 3D web · generative music"),
        ("p", "echo $MOTTO"),
        ("c", '"Tune it until scrolling feels like a short film."'),
    ]
    top, lh = 78, 34
    H = top + lh * len(lines) + 50
    total = 16.0
    body = []
    t = 0.4
    for i, (kind, txt) in enumerate(lines):
        y = top + i * lh
        prefix = "~/earthclique $ " if kind == "p" else ""
        full = prefix + txt
        wpx = len(full) * 10.9 + 20
        dt = 0.9 if kind == "p" else 0.35
        k1, k2 = t / total, min((t + dt) / total, 0.97)
        color = {"p": SNOW, "o": MINT, "c": CORAL}[kind]
        body.append(f'<clipPath id="c{i}"><rect x="40" y="{y-24}" height="34" width="0">'
                    f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" '
                    f'keyTimes="0;{k1:.3f};{k2:.3f};1" values="0;0;{wpx:.0f};{wpx:.0f}"/></rect></clipPath>')
        if kind == "p":
            body.append(f'<text x="44" y="{y}" clip-path="url(#c{i})"><tspan fill="{CORAL}">~/earthclique</tspan>'
                        f'<tspan fill="{MINT}"> $ </tspan><tspan fill="{SNOW}">{esc(txt)}</tspan></text>')
        else:
            body.append(f'<text x="44" y="{y}" fill="{color}" clip-path="url(#c{i})">{esc(txt)}</text>')
        t += dt + (0.5 if kind == "p" else 0.25)
    cy = top + lh * len(lines)
    body.append(f'<text x="44" y="{cy}"><tspan fill="{CORAL}">~/earthclique</tspan><tspan fill="{MINT}"> $ </tspan>'
                f'<tspan fill="{SNOW}">▋<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="#071C20" stroke="{TEAL}"/>
<rect x=".5" y=".5" width="{W-1}" height="44" rx="18" fill="{DEEP}"/><rect x=".5" y="30" width="{W-1}" height="15" fill="{DEEP}"/>
<circle cx="30" cy="23" r="7" fill="{CORAL}"/><circle cx="54" cy="23" r="7" fill="#F2B84B"/><circle cx="78" cy="23" r="7" fill="{MINT}"/>
<text x="{W/2}" y="28" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{SNOW}" opacity=".6">clique-x — zsh — haridwar</text>
<g font-family="{MONO}" font-size="18">{"".join(body)}</g>
</svg>'''


# ---------------------------------------------------------------- PROJECT CARDS
def card(num, tag, title, sub, desc, pills, shape, accent, pitch=0.35, scale=86, dur=10):
    W, H = 600, 270
    shp = anim_path(shape, 40, dur, pitch, 490, 128, scale,
                    f'fill="none" stroke="{accent}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" filter="url(#g)"',
                    dist=4.5)
    px, pill_svg = 32, []
    for p in pills:
        w = len(p) * 8.2 + 26
        pill_svg.append(f'<rect x="{px}" y="214" width="{w:.0f}" height="28" rx="14" fill="{accent}" fill-opacity=".12" stroke="{accent}" stroke-opacity=".6"/>'
                        f'<text x="{px + w/2:.0f}" y="233" text-anchor="middle">{esc(p)}</text>')
        px += w + 8
    dl = "".join(f'<tspan x="32" dy="{0 if i == 0 else 22}">{esc(l)}</tspan>' for i, l in enumerate(desc))
    per = 2 * (W - 2 + H - 2)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
 <linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0A2529"/><stop offset="1" stop-color="#04161A"/></linearGradient>
 <radialGradient id="h" cx=".82" cy=".45" r=".42"><stop offset="0" stop-color="{accent}" stop-opacity=".28"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
 <filter id="g" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.6" result="x"/><feMerge><feMergeNode in="x"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="url(#b)"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="url(#h)"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="none" stroke="{TEAL}" stroke-opacity=".7"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="none" stroke="{accent}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="140 {per}">
 <animate attributeName="stroke-dashoffset" values="0;-{per+140}" dur="7s" repeatCount="indefinite"/></rect>
{shp}
<g font-family="{MONO}" font-size="12" fill="{accent}" letter-spacing="2"><text x="32" y="44">{num} / {esc(tag)}</text>
 <circle cx="{32 + (len(num) + 3 + len(tag)) * 9.2 + 8:.0f}" cy="40" r="4" fill="{accent}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle></g>
<text x="32" y="88" font-family="{SANS}" font-size="32" font-weight="800" fill="{SNOW}">{esc(title)}</text>
<text x="32" y="116" font-family="{SANS}" font-size="16" font-weight="600" fill="{accent}">{esc(sub)}</text>
<text x="32" y="152" font-family="{SANS}" font-size="15" fill="#C9E4E1">{dl}</text>
<g font-family="{MONO}" font-size="13" fill="{SNOW}">{"".join(pill_svg)}</g>
</svg>'''


CARDS = {
    "casecraft": ("01", "LIVE", "CaseCraft", "3D phone-case storefront",
                  ["Pick your phone, spin every case in 3D,", "check out with UPI, cards or COD."],
                  ["Next.js", "Three.js", "Medusa", "Razorpay"], phone(), CORAL, 0.3, 88),
    "earthclique": ("02", "BRAND SITE", "earthclique.in", "A Himalayan peak inside the logo",
                    ["Procedural 3D peak you can drag. The sun", "follows real time of day in Haridwar."],
                    ["Next.js 16", "R3F", "GSAP", "Lenis"], terrain(8), MINT, 0.5, 92),
    "amc": ("03", "PLATFORM", "Earthclique AMC", "On-demand IT & CCTV engineers",
            ["Raise a ticket, nearby verified engineers'", "phones ring. OTP start, proof-of-fix close."],
            ["Flutter", "Next.js", "TypeScript", "Kotlin"], globe(), "#F2B84B", 0.35, 82),
    "swastik": ("04", "INDUSTRIAL", "Swastik Metal", "Stainless steel, served online",
                ["Official site for a stainless steel", "stockist and supplier. Built in TypeScript."],
                ["Next.js", "TypeScript", "Tailwind"], pipe(), "#9FC3C9", 0.45, 92),
    "codamusica": ("05", "EXPERIMENT", "CodaMusica", "Music made with code",
                   ["Infinite, never-repeating algorithmic", "scores, live-coded in SuperCollider."],
                   ["SuperCollider", "Python"], torus(), "#C79BFF", 0.6, 92),
    "next": ("06", "OPEN SLOT", "Your idea, next.", "Have something to build?",
             ["Storefronts, SaaS, 3D sites, booking", "engines. Ping Earthclique, let's ship."],
             ["earthclique.in", "→"], icosa(), CORAL, 0.4, 84),
}


# ---------------------------------------------------------------- VAULT
def vault():
    W, H = 1200, 330
    tiles = [("Trading academy LMS", "funnels · Razorpay"), ("Mountain-stay booking", "engine + admin panel"),
             ("Dental clinic SaaS", "WhatsApp-native"), ("Vertical ERP", "for Indian SMBs"),
             ("Immigration platform", "Postgres · Drizzle"), ("Earthy e-com engine", "auth · orders · blog"),
             ("3D links page", "WebGL micro-site"), ("AI agent + chat UI", "templates & tooling")]
    out = []
    tw, th, gx, gy, x0, y0 = 270, 92, 20, 18, 30, 110
    for i, (a, b) in enumerate(tiles):
        r, c = divmod(i, 4)
        x, y = x0 + c * (tw + gx), y0 + r * (th + gy)
        d = i * 0.35
        out.append(f'''<g transform="translate({x} {y})">
<rect width="{tw}" height="{th}" rx="14" fill="#0A2529" stroke="{TEAL}"/>
<rect width="{tw}" height="{th}" rx="14" fill="none" stroke="{MINT}" stroke-width="1.5" opacity="0"><animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;.1;.2;.35;1" dur="5.6s" begin="{d:.2f}s" repeatCount="indefinite"/></rect>
<g transform="translate(22 28)" fill="none" stroke="{CORAL}" stroke-width="2"><rect x="0" y="12" width="24" height="20" rx="4"/><path d="M5 12V7a7 7 0 0 1 14 0v5"/></g>
<text x="62" y="42" font-family="{SANS}" font-size="17" font-weight="700" fill="{SNOW}">{esc(a)}</text>
<text x="62" y="66" font-family="{MONO}" font-size="13" fill="{MINT}">{esc(b)}</text>
</g>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="#04161A" stroke="{TEAL}" stroke-opacity=".6"/>
<text x="30" y="52" font-family="{SANS}" font-size="26" font-weight="800" fill="{SNOW}">The private vault</text>
<text x="30" y="80" font-family="{MONO}" font-size="14" fill="{MINT}">14 client builds behind closed doors · ask for a walkthrough</text>
<text x="{W-30}" y="60" text-anchor="end" font-family="{MONO}" font-size="40" font-weight="700" fill="{CORAL}">14<tspan font-size="16" fill="{SNOW}" dx="6">private repos</tspan></text>
{"".join(out)}
</svg>'''


# ---------------------------------------------------------------- SECTION HEADERS + FOOTER
def header(label, kicker):
    W, H = 1200, 70
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="{CORAL}"/><stop offset=".5" stop-color="{MINT}"/><stop offset="1" stop-color="{MINT}" stop-opacity="0"/></linearGradient></defs>
<text x="0" y="22" font-family="{MONO}" font-size="13" fill="{CORAL}" letter-spacing="3">{esc(kicker)}</text>
<text x="0" y="56" font-family="{SANS}" font-size="30" font-weight="800" fill="{MINT}">{esc(label)}</text>
<rect x="{len(label) * 17 + 24:.0f}" y="44" height="3" width="0" fill="url(#l)"><animate attributeName="width" values="0;{W - len(label) * 17 - 30:.0f};{W - len(label) * 17 - 30:.0f}" keyTimes="0;.4;1" dur="4s" repeatCount="indefinite"/></rect>
</svg>'''


def footer():
    W, H = 1200, 170

    def wave(amp, off, y):
        pts = [f"M0 {H}", f"L0 {y}"]
        for x in range(0, W * 2 + 1, 40):
            pts.append(f"L{x} {y + amp * math.sin(x / 120 + off):.1f}")
        pts.append(f"L{W*2} {H}Z")
        return "".join(pts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<clipPath id="r"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="#04161A"/>
<path d="{wave(10, 0, 92)}" fill="{TEAL}" opacity=".5"><animateTransform attributeName="transform" type="translate" values="0 0;-754 0" dur="9s" repeatCount="indefinite"/></path>
<path d="{wave(14, 2, 108)}" fill="{DEEP}"><animateTransform attributeName="transform" type="translate" values="-754 0;0 0" dur="12s" repeatCount="indefinite"/></path>
<path d="{wave(8, 4, 128)}" fill="{MINT}" opacity=".22"><animateTransform attributeName="transform" type="translate" values="0 0;-754 0" dur="7s" repeatCount="indefinite"/></path>
<text x="{W/2}" y="54" text-anchor="middle" font-family="{SANS}" font-size="24" font-weight="800" fill="{SNOW}">Built in the foothills of the Himalayas</text>
<text x="{W/2}" y="152" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{SNOW}">earthclique.in · Haridwar, Uttarakhand · thanks for scrolling</text>
</g></svg>'''


files = {"hero.svg": hero(), "terminal.svg": terminal(), "vault.svg": vault(), "footer.svg": footer(),
         "h-work.svg": header("Featured work", "// 01 — PUBLIC BUILDS"),
         "h-stack.svg": header("Tools of the trade", "// 02 — STACK"),
         "h-graph.svg": header("Contributions, in 3D", "// 03 — ACTIVITY")}
for k, v in CARDS.items():
    files[f"card-{k}.svg"] = card(*v)
for name, svg in files.items():
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{name:22s} {len(svg)/1024:7.1f} KB")
