"""Build the Blueprint theme for T3 Code: theme.json + SVG layers."""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
INK = "#d6ebff"      # chalk-white line
FAINT = "#8fb8e0"    # construction line
PENCIL = "#ffd166"   # markup yellow
T = 32               # plot cycle seconds
MONO = "ui-monospace,Menlo,monospace"


def f(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pct(x):
    s = f"{x:.1f}".rstrip("0").rstrip(".")
    return s + "%"


def circle(cx, cy, r, **attrs):
    a = "".join(f" {k.replace('_', '-')}='{v}'" for k, v in attrs.items())
    return f"<circle cx='{f(cx)}' cy='{f(cy)}' r='{f(r)}'{a}/>"


# ---------------------------------------------------------------- gears
def gear_path(cx, cy, n, ro, rr, phase):
    p = 2 * math.pi / n
    pts = []
    for i in range(n):
        t = phase + i * p
        for frac, r in ((0, rr), (0.35, rr), (0.5, ro), (0.85, ro)):
            a = t + frac * p
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def tick_keyframes(name, step_deg, ticks, sign):
    """One eased tick per second; loops after `ticks` (gear is symmetric there)."""
    stops = []
    for k in range(ticks):
        a = k / ticks * 100
        b = (k + 0.3) / ticks * 100
        stops.append(f"{pct(a)}{{rotate:{f(sign*k*step_deg)}deg}}")
        stops.append(f"{pct(b)}{{rotate:{f(sign*(k+1)*step_deg)}deg}}")
    stops.append(f"to{{rotate:{f(sign*ticks*step_deg)}deg}}")
    return f"@keyframes {name}{{" + "".join(stops) + "}"


def gears_svg():
    nb, ns = 16, 10
    rob, rrb = 130, 112
    rpb = (rob + rrb) / 2
    rps = rpb * ns / nb
    ros, rrs = rps + 9, rps - 9
    bx, by = 150, 150
    phi = math.radians(35)
    cd = rpb + rps
    sx, sy = bx + cd * math.cos(phi), by + cd * math.sin(phi)
    pb, ps = 2 * math.pi / nb, 2 * math.pi / ns
    off_b = phi - 0.175 * pb
    off_s = phi + math.pi - 0.675 * ps
    big = gear_path(bx, by, nb, rob, rrb, off_b)
    small = gear_path(sx, sy, ns, ros, rrs, off_s)
    holes = "".join(  # 8 holes -> big gear repeats every 45deg = 12 ticks of 3.75deg
        circle(bx + 78 * math.cos(off_b + k * math.pi / 4), by + 78 * math.sin(off_b + k * math.pi / 4), 13)
        for k in range(8))
    css = (
        "path,circle{fill:none}"
        f".i{{stroke:{INK};stroke-width:3;stroke-opacity:.38}}"
        f".c{{stroke:{FAINT};stroke-width:1.6;stroke-opacity:.3;stroke-dasharray:14 3 2 3}}"
        f".b{{transform-origin:{bx}px {by}px;animation:gb 12s cubic-bezier(.3,.6,.2,1) infinite}}"
        f".s{{transform-origin:{f(sx)}px {f(sy)}px;animation:gs 6s cubic-bezier(.3,.6,.2,1) infinite}}"
        + tick_keyframes("gb", 3.75, 12, -1) + tick_keyframes("gs", 6, 6, 1)
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    body = (
        f"<g class='i b'><path d='{big}'/>{circle(bx, by, 44)}{circle(bx, by, 20)}{holes}</g>"
        f"<g class='i s'><path d='{small}'/>{circle(sx, sy, 30)}{circle(sx, sy, 13)}</g>"
        f"<g class='c'>{circle(bx, by, rpb)}{circle(sx, sy, rps)}"
        f"<path d='M{bx-160} {by}H{bx+160}M{bx} {by-160}V{by+160}M{f(sx-100)} {f(sy)}H{f(sx+100)}M{f(sx)} {f(sy-100)}V{f(sy+100)}M{bx} {by}L{f(sx)} {f(sy)}'/></g>"
    )
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 440 400'><style>{css}</style>{body}</svg>"


# ---------------------------------------------------------------- plotted part
def circle_pts(cx, cy, r, n=12):
    return [(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * k / n), cy + r * math.sin(-math.pi / 2 + 2 * math.pi * k / n)) for k in range(n + 1)]


def poly_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def hatch_zigzag(x0, y0, x1, y1, step):
    """Boustrophedon 45deg hatch inside rect, as one continuous pen path."""
    segs = []
    w, h = x1 - x0, y1 - y0
    for c in range(int(step), int(w + h), int(step)):
        # line x - x0 + (y1 - y) = c  (rising to the right)
        a = (x0 + max(0, c - h), y1 - min(c, h))
        b = (x0 + min(c, w), y1 - max(0, c - w))
        a = (a[0], y1 - (c - (a[0] - x0)))
        b = (b[0], y1 - (c - (b[0] - x0)))
        segs.append((a, b) if len(segs) % 2 == 0 else (b, a))
    pts = []
    for s in segs:
        pts += [s[0], s[1]]
    return pts


def part_svg(static=False):
    outline = [(60, 300), (60, 130), (130, 60), (300, 60), (300, 140), (460, 140), (460, 300), (60, 300)]
    h1, h2 = (180, 180, 34), (400, 222, 22)
    park = (530, 330)  # maps to bottom-right of the portrait sheet
    hatch = hatch_zigzag(300, 140, 460, 300, 20)
    # ordered pen strokes: (name, pen points, svg path d)
    strokes = [
        ("o", outline, "M" + "L".join(f"{x} {y}" for x, y in outline)),
        ("c1", circle_pts(*h1), "M180 146a34 34 0 1 1 0 68a34 34 0 1 1 0-68"),
        ("c2", circle_pts(*h2), "M400 200a22 22 0 1 1 0 44a22 22 0 1 1 0-44"),
        ("br", [(300, 140), (304, 180), (296, 220), (304, 260), (300, 300)], "M300 140q8 20 0 40t0 40 0 40 0 40"),
        ("h", hatch, "M" + "L".join(f"{f(x)} {f(y)}" for x, y in hatch)),
        ("e1", [(60, 306), (60, 342)], "M60 306V342"),
        ("d1", [(60, 334), (460, 334)], "M60 334H460"),
        ("e2", [(460, 342), (460, 306)], "M460 342V306"),
        ("e3", [(466, 300), (504, 300)], "M466 300H504"),
        ("d2", [(496, 300), (496, 140)], "M496 300V140"),
        ("e4", [(504, 140), (466, 140)], "M504 140H466"),
        ("e5", [(124, 60), (20, 60)], "M124 60H20"),
        ("d3", [(28, 60), (28, 300)], "M28 60V300"),
        ("e6", [(20, 300), (54, 300)], "M20 300H54"),
        ("l", [(118, 288), (118, 248), (156, 204)], "M118 288V248L156 204"),
        ("l2", [(384, 206), (346, 124), (346, 88)], "M384 206L346 124V88"),
    ]
    START, END, TRAVEL = 3.0, 76.0, 3.0  # travel is 3x faster than drawing
    pos = park
    total = 0
    for _, pts, _ in strokes:
        total += math.dist(pos, pts[0]) / TRAVEL + poly_len(pts)
        pos = pts[-1]
    total += math.dist(pos, park) / TRAVEL
    rate = (END - START) / total
    t = START
    frames = [(0, park), (START, park)]
    windows = {}
    pos = park
    for name, pts, _ in strokes:
        t += math.dist(pos, pts[0]) / TRAVEL * rate
        frames.append((t, pts[0]))
        a = t
        for i in range(1, len(pts)):
            t += math.dist(pts[i - 1], pts[i]) * rate
            frames.append((t, pts[i]))
        windows[name] = (a, t)
        pos = pts[-1]
    t += math.dist(pos, park) / TRAVEL * rate
    frames.append((t, park))
    kf, last = [], None
    for p, (x, y) in frames:
        key = pct(p)
        if key != last:
            kf.append(f"{key}{{translate:{round(x)}px {round(y)}px}}")
        last = key
    kf.append(f"to{{translate:{park[0]}px {park[1]}px}}")
    pen_kf = "@keyframes pen{" + "".join(kf) + "}"
    stroke_css = "".join(
        f".{n}{{animation-name:{n}}}@keyframes {n}{{{pct(a)}{{stroke-dashoffset:1}}{pct(b)},90%{{stroke-dashoffset:0;opacity:1}}97%,to{{stroke-dashoffset:0;opacity:0}}}}"
        for n, (a, b) in windows.items())
    work_end = t
    css = (
        "path,circle{fill:none}"
        f".i{{stroke:{INK};stroke-width:1.5;stroke-opacity:.8;stroke-linejoin:round}}"
        f".f{{stroke:{FAINT};stroke-width:.8;stroke-opacity:.55}}"
        f".h{{stroke:{FAINT};stroke-width:.9;stroke-opacity:.7}}"
        f"text{{fill:{INK};fill-opacity:.7;font:19px {MONO};letter-spacing:.04em}}"
        f".s{{stroke-dasharray:1;stroke-dashoffset:1;animation:{T}s linear infinite}}" + stroke_css
        + f".x{{opacity:0;animation:tx {T}s linear infinite}}"
        f"@keyframes tx{{{pct(windows['l2'][1])}{{opacity:0}}{pct(windows['l2'][1]+3)},90%{{opacity:1}}97%,to{{opacity:0}}}}"
        + f".p{{animation:pen {T}s linear infinite}}" + pen_kf
        + f".k{{stroke:{PENCIL};stroke-width:1.2}}.r{{stroke:{PENCIL};stroke-width:.6;stroke-opacity:.16}}"
        # busy indicators only while the pen is working
        f".w{{opacity:0;animation:w {T}s step-end infinite,lamp 1.2s ease-in-out infinite}}"
        f"@keyframes w{{{pct(START)}{{opacity:1}}{pct(work_end)}{{opacity:0}}}}"
        "@keyframes lamp{50%{fill-opacity:.2}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}.s{stroke-dashoffset:0}.x{opacity:1}.p{translate:530px 330px}}"
    )
    outline_d = strokes[0][2]
    drawn = "".join(
        f"<path class='{'h' if n == 'h' else ('i' if n in ('o', 'c1', 'c2', 'br') else 'f')} s {n}' pathLength='1' d='{d}'"
        + (" mask='url(#m)'" if n == "h" else "") + "/>"
        for n, _, d in strokes)
    body = (
        f"<defs><path id='a' d='M0 0l9-3v6z' style='fill:{INK};fill-opacity:.8'/>"
        f"<mask id='m'><path d='M300 140h160v160H300z' style='fill:%23fff'/><circle cx='400' cy='222' r='23' style='fill:%23000'/></mask></defs>"
        # pencil underlay (always present)
        "<g transform='matrix(0 1 -1 0 360 0)'>"  # drawn landscape, shown portrait
        f"<path class='f' stroke-dasharray='3 4' d='{outline_d}'/>"
        f"<path class='f' stroke-dasharray='10 3 2 3' d='M140 180h80M180 140v80M370 222h60M400 192v60'/>"
        + drawn
        + f"<g class='x'><use href='#a' x='60' y='334'/><use href='#a' transform='translate(460 334) rotate(180)'/>"
        f"<use href='#a' transform='translate(496 140) rotate(90)'/><use href='#a' transform='translate(496 300) rotate(-90)'/><use href='#a' transform='translate(28 60) rotate(90)'/><use href='#a' transform='translate(28 300) rotate(-90)'/></g>"
        f"<g class='p'><path class='r' d='M-40 0H40M0-40V40'/>"
        f"<path class='k' d='M-12 0h7M5 0h7M0-12v7M0 5v7'/><circle class='k' r='4'/>"
        f"<circle class='w' r='3' style='fill:{PENCIL}'/></g></g>"
        "<g class='x'><text x='20' y='276' transform='rotate(-90 20 276)'>400</text>"
        "<text x='122' y='520'>160</text><text x='164' y='20'>240</text>"
        "<text x='74' y='112'>Ø68</text><use href='#a' transform='translate(156 156) rotate(225)'/><text x='240' y='340'>Ø44</text><use href='#a' transform='translate(154 384) rotate(-45)'/></g>"
        "<text x='60' y='552'>DETAIL A · 2:1</text>"
    )
    if static:  # the finished sheet: no pen, no keyframes
        css = css[:css.index(".s{")]
        i = body.index("<g class='p'>")
        body = body[:i] + "</g>" + body[body.index("</g></g>", i) + 8:]
        body = re.sub(r"class='(\w) s \w+' pathLength='1'", r"class='\1'", body)
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 360 560'><style>{css}</style>{body}</svg>"


# ---------------------------------------------------------------- title block
def title_svg():
    revs = "B"
    n = len(revs)
    css = (
        f"path{{fill:none;stroke:{INK};stroke-opacity:.45;stroke-width:1}}"
        f"text{{fill:{INK};fill-opacity:.6;font:10px {MONO};letter-spacing:.1em}}"
        f".b{{fill-opacity:.72;font-size:13px;font-weight:500;letter-spacing:.02em}}.y{{fill:{PENCIL};fill-opacity:.9}}"
    )
    body = (
        "<path d='M.5 .5h279v95H.5zM.5 36.5h279M.5 66.5h279M90.5 36.5v59M170.5 36.5v30M220.5 36.5v30'/>"
        "<text x='9' y='14'>TITLE</text><text class='b' x='9' y='30'>T3 CODE · GENERAL ARRANGEMENT</text>"
        "<text x='9' y='49'>DRN</text><text class='b' x='9' y='62'>AGENT</text>"
        "<text x='99' y='49'>CHK</text><text class='b' x='99' y='62'>YOU</text>"
        "<text x='179' y='49'>SCALE</text><text class='b' x='179' y='62'>1:1</text>"
        "<text x='229' y='49'>REV</text>"
        + "".join(f"<text class='b y' x='229' y='62'>{c}</text>" for i, c in enumerate(revs))
        + "<text x='9' y='79'>DWG NO.</text><text class='b' x='9' y='92'>T3-0042</text>"
        "<text x='99' y='79'>SHEET</text><text class='b' x='99' y='92'>01 OF 01</text>"
    )
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 281 97'><style>{css}</style>{body}</svg>"


def data_uri(svg):
    svg = svg.replace("%23", "\0")  # pre-encoded hashes inside the mask
    out = svg.replace("%", "%25").replace("#", "%23").replace('"', "'").replace("<", "%3C").replace("\0", "%23")
    return "url(\"data:image/svg+xml," + out + "\")"


# ---------------------------------------------------------------- theme
colors = {
    "canvas": "#0b3260", "chrome": "#082a50", "toolbar": "#0b3260", "toolbarForeground": "#e8f3ff",
    "toolbarBorder": "#24568a", "toolbarControl": "#0f3c6e", "toolbarControlForeground": "#e8f3ff",
    "toolbarControlHover": "#164a82", "surface": "#0d3766", "surfaceRaised": "#114073",
    "surfaceOverlay": "#134779", "text": "#eef6ff", "textMuted": "#a6c3e0", "border": "#2b5d91",
    "input": "#4f86bd", "focus": "#ffd166", "accent": "#ffd166", "accentForeground": "#1d1a10",
    "secondary": "#12437a", "secondaryForeground": "#e8f3ff", "muted": "#0f3a69",
    "mutedForeground": "#93b4d6", "placeholder": "#7fa2c7", "secondaryLabel": "#93b4d6",
    "iconMuted": "#93b4d6", "error": "#ff8585", "errorForeground": "#ffb0b0", "errorSurface": "#3b1d33",
    "warning": "#ffb347", "warningForeground": "#ffd08a", "warningSurface": "#4a3414",
    "update": "#7fe3ff", "updateForeground": "#e6fbff", "updateSurface": "#0f4a6e",
    "accentSurface": "#1c4f7a", "accentSurfaceForeground": "#ffeab0", "messageSurface": "#134a80",
    "messageForeground": "#f2f8ff", "messageAction": "#ffd166", "messageActionForeground": "#1d1a10",
    "messageActionHover": "#ffe08f", "codeBackground": "#082545", "codeForeground": "#e3f0ff",
    "searchMatchBackground": "#6b5a1e", "searchMatchForeground": "#fff8e1",
    "searchMatchActiveBackground": "#ffd166", "searchMatchActiveForeground": "#1d1a10",
    "sidebar": "#082646", "sidebarForeground": "#e3efff", "sidebarMutedForeground": "#8fb0d3",
    "sidebarControlSurface": "#0e3663", "sidebarRowHover": "#0e3866", "sidebarRowActive": "#124174",
    "sidebarRowSelected": "#154a82", "sidebarBorder": "#1f4c7c", "terminalBackground": "#071f3b",
    "terminalForeground": "#e3efff", "terminalCursor": "#ffd166", "terminalSelection": "#1e4f84",
    "terminalScrollbar": "#1f4c7c", "terminalScrollbarHover": "#2d6299",
}

Y = "#ffd166"
W = "rgba(214,235,255,"
CW = "var(--chat-content-max-width,46rem)"
G = f"(100% - {CW})/2"  # one gutter beside the reading column


def gutter_size(threshold, maxw):
    """Shrinks with the gutter and vanishes when the gutter is narrower than `threshold`."""
    return f"min({maxw}px,clamp(0px,({G} - {threshold}px)*1000,{G} - 40px)) auto"


grid = (
    f"linear-gradient({W}.09) 1px,transparent 1px) 10px 10px/80px 80px,"
    f"linear-gradient(90deg,{W}.09) 1px,transparent 1px) 10px 10px/80px 80px,"
    f"linear-gradient({W}.035) 1px,transparent 1px) 10px 10px/16px 16px,"
    f"linear-gradient(90deg,{W}.035) 1px,transparent 1px) 10px 10px/16px 16px"
)
corner = (  # yellow registration ticks in two corners
    f"linear-gradient({Y},{Y}) left top/9px 1px no-repeat,linear-gradient({Y},{Y}) left top/1px 9px no-repeat,"
    f"linear-gradient({Y},{Y}) right bottom/9px 1px no-repeat,linear-gradient({Y},{Y}) right bottom/1px 9px no-repeat"
)
# a turn is running: T3 renders the working row only while isWorking; fall back to the open thread's busy flag
BUSY = ('body:has([data-timeline-row-kind="working"])', 'body:has([data-thread-item] [aria-busy="true"][aria-current]:not([aria-current="false"]))')


def busy(sel):
    return ",".join(f"{b} {sel}" for b in BUSY)


GRID_IMAGES = ",".join(f"linear-gradient({d}{W}{o}) 1px,transparent 1px)" for o in (".09", ".035") for d in ("", "90deg,"))
SB_GRID = f"linear-gradient({W}.03) 1px,transparent 1px),linear-gradient(90deg,{W}.03) 1px,transparent 1px)"
SB_GRID_L = SB_GRID.replace("1px),linear", "1px) 0 0/16px 16px,linear") + " 0 0/16px 16px"
DIM = "linear-gradient(rgba(8,38,70,.3),rgba(8,38,70,.3))"
SB_POS = "50% calc(100% - 60px)"
css = (
    # the finished sheet (idle) and the live plotter (working), shared by the gutter and the narrow fallback
    ":root{--bp-s:" + data_uri(part_svg(True)) + ";--bp-a:" + data_uri(part_svg()) + f";--bp-c:{corner}}}"
    "[data-workspace-area=\"conversation\"]{background:"
    f"var(--bp-s) left 12px top 64px/{gutter_size(216, 380)} no-repeat,"
    "radial-gradient(ellipse at 50% 40%,transparent 40%,rgba(3,18,38,.55)),"
    + grid + ",#0d3a69!important}"
    + busy('[data-workspace-area="conversation"]') + "{background-image:var(--bp-a),radial-gradient(ellipse at 50% 40%,transparent 40%,rgba(3,18,38,.55))," + GRID_IMAGES + "!important}"
    # sheet border + docked title block, layered over the reading-column scrim
    f"[data-workspace-area=\"conversation\"] .messages-timeline-scroll{{background:" + data_uri(title_svg()) + f" right 10px bottom 10px/min(281px,clamp(0px,({G} - 200px)*1000,{G} - 32px)) auto no-repeat,"
    + ",".join(f"linear-gradient({W}.2),{W}.2)) {p} no-repeat" for p in ("10px 10px/calc(100% - 20px) 1px", "10px calc(100% - 10px)/calc(100% - 20px) 1px", "10px 10px/1px calc(100% - 20px)", "calc(100% - 10px) 10px/1px calc(100% - 20px)"))
    + f",linear-gradient(90deg,transparent calc(50% - {CW}/2 - 112px),rgba(10,44,82,.9) calc(50% - {CW}/2 - 16px),rgba(10,44,82,.9) calc(50% + {CW}/2 + 16px),transparent calc(50% + {CW}/2 + 112px))!important}}"
    # header = the plotter's gantry rail; the carriage drops in and shuttles only while a turn runs, then retracts where it stopped
    f"[data-chat-header]{{background-color:rgba(9,40,74,.95)!important;background-image:linear-gradient({Y},{Y}),linear-gradient({Y},{Y})!important;background-repeat:no-repeat!important;background-size:0 2px,2px 0!important;background-position:100% 100%,calc(100% - 13px) 100%;border-bottom:1px dashed rgba(214,235,255,.22)!important;transition:background-size .4s;animation:bp-car 8s cubic-bezier(.45,0,.55,1) infinite alternate paused}}"
    + busy("[data-chat-header]") + "{animation-play-state:running;background-size:28px 2px,2px 7px!important}"
    "@keyframes bp-car{to{background-position:0 100%,13px 100%}}"
    # a pencil dash marches under "Working…" and, softer, under every busy thread in the sidebar
    "[data-timeline-row-kind=\"working\"],[data-thread-item] [aria-busy=\"true\"]{background-image:linear-gradient(90deg,rgba(255,209,102,var(--a,.75)) 50%,transparent 0)!important;background-size:14px 1px!important;background-repeat:repeat-x!important;background-position:0 100%;animation:bp-march var(--d,1.4s) steps(7) infinite}"
    "[data-thread-item] [aria-busy=\"true\"]{--a:.45;--d:2.8s}"
    "@keyframes bp-march{to{background-position:14px 100%}}"
    f"[data-slot=\"sidebar-inner\"]{{background:{SB_GRID_L},#082646!important}}"
    # narrow windows: no gutter, so the sheet docks at the foot of the sidebar instead
    f"@media (max-width:1459px){{[data-slot=\"sidebar-inner\"]{{background:{DIM} {SB_POS}/150px 233px no-repeat,var(--bp-s) {SB_POS}/150px 233px no-repeat,{SB_GRID_L},#082646!important}}"
    + busy('[data-slot="sidebar-inner"]') + f"{{background-image:{DIM},var(--bp-a),{SB_GRID}!important}}}}"
    f"[data-thread-item]{{background-image:linear-gradient({Y},{Y});background-repeat:no-repeat;background-position:10px calc(100% - 2px);background-size:0 1px;transition:background-size .45s cubic-bezier(.2,.7,.2,1)}}"
    "[data-thread-item]:hover{background-size:calc(100% - 20px) 1px}"
    f"[data-thread-item] [aria-current]:not([aria-current=\"false\"]){{box-shadow:inset 2px 0 {Y}}}"
    "[data-thread-item] [role=\"button\"]{border-radius:2px!important}[data-thread-item]:has([aria-busy=\"true\"]){background-size:0 1px!important}"
    "[data-user-message-bubble]{background:var(--bp-c),rgba(18,70,124,.92)!important;border:1px solid rgba(214,235,255,.4)!important;border-radius:2px!important}"
    "[data-slot=\"composer-host\"]{background:var(--bp-c),rgba(8,36,68,.96)!important;border:1px solid rgba(214,235,255,.42)!important;border-radius:3px!important;transition:border-color .2s,box-shadow .3s,background-size .3s cubic-bezier(.2,.7,.2,1)}"
    "[data-slot=\"composer-host\"]:focus-within{border-color:rgba(214,235,255,.8)!important;box-shadow:0 0 0 3px rgba(214,235,255,.1);background-size:22px 1px,1px 22px,22px 1px,1px 22px,auto!important}"
    ".chat-markdown-codeblock{background:rgba(6,30,58,.94)!important;border:1px dashed rgba(143,184,224,.4)!important;border-radius:2px!important}"
    ".chat-markdown :not(pre)>code{color:#cdeeff;background:rgba(127,227,255,.1);padding:.05em .3em;border-radius:2px}"
    f".chat-markdown :is(h1,h2,h3){{font-family:{MONO};letter-spacing:.06em;text-transform:uppercase}}.chat-markdown :is(h1,h2,h3) code{{text-transform:none}}"
    ".chat-markdown :is(h1,h2){border-bottom:1px solid rgba(214,235,255,.22);padding-bottom:.2em}"
    ".chat-markdown a{color:#7fe3ff!important;text-decoration-style:dashed;text-underline-offset:3px}"
    "::selection{background:rgba(255,209,102,.32)}"
    "[data-slot=\"dialog-popup\"],[data-slot=\"popover-popup\"],[data-slot=\"menu-popup\"]{border-radius:3px!important;border:1px solid #4f86bd!important}"
    "[data-slot=\"tooltip-popup\"],[data-slot=\"button\"],[data-slot=\"input\"],[data-slot=\"select-trigger\"]{border-radius:3px!important}"
    "::-webkit-scrollbar-thumb,[data-slot=\"scroll-area-thumb\"]{background:rgba(214,235,255,.2)!important;border-radius:0!important}"
    "::-webkit-scrollbar-thumb:hover{background:rgba(255,209,102,.5)!important}"
    "@media (prefers-reduced-motion:reduce){[data-thread-item],[data-thread-item] [aria-busy],[data-timeline-row-kind],[data-slot=\"composer-host\"],[data-chat-header]{transition:none!important;animation:none!important}}"
)

theme = {"version": 1, "name": "Blueprint", "appearance": "dark", "accent": "#ffd166", "canvas": "#0b3260",
         "colors": colors, "css": css}

with open(os.path.join(HERE, "..", "blueprint.json"), "w") as fh:
    json.dump(theme, fh, ensure_ascii=False)
print("css chars:", len(css))
for n, s in (("title", title_svg()), ("part", part_svg()), ("gears", gears_svg())):
    os.makedirs(os.path.join(HERE, "..", "assets", "svg"), exist_ok=True)
    with open(os.path.join(HERE, "..", "assets", "svg", f"{n}.svg"), "w") as fh:
        fh.write(s.replace("%23", "#"))
    print(n, len(data_uri(s)))
