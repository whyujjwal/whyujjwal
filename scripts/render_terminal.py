#!/usr/bin/env python3
"""Render assets/terminal.svg: the animated terminal at the top of the profile README.

    python3 scripts/render_terminal.py

No dependencies. Edit the CONTENT section below and re-run.

How it stays sharp everywhere:
  * Every text run is placed on an explicit character grid and given a textLength,
    so columns line up no matter which monospace font the viewer's browser picks.
  * The logo is pixel art drawn with <rect>s, not ASCII, so it can't misalign.
  * Pure CSS animation (no JS, which GitHub strips anyway). Every element's resting
    state is its final state, so viewers with animations off, or with
    prefers-reduced-motion, see the finished screen.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"

# ---------------------------------------------------------------- geometry
W = 880          # canvas width
FS = 14          # font size
CW = 8.4         # character advance (0.6em, standard for monospace)
LH = 20          # line height
X0 = 28          # left padding
TOP = 36         # title bar height
Y0 = TOP + 30    # baseline of row 0
P = 11           # logo pixel size

FONT = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"

# ---------------------------------------------------------------- palette (GitHub dark)
BG, BAR, BORDER = "#0d1117", "#161b22", "#30363d"
COLORS = {
    "fg": "#c9d1d9", "d": "#8b949e", "w": "#f0f6fc",
    "g": "#3fb950", "lg": "#7ee787", "b": "#58a6ff", "lb": "#79c0ff",
    "p": "#d2a8ff", "y": "#d29922", "r": "#ff7b72", "c": "#39c5cf",
    "nv": "#76b900",  # NVIDIA green
}

# ---------------------------------------------------------------- CONTENT
HOST = ("ujjwal", "github")

NEOFETCH = [  # (key, value); a value can also be a list of (text, classes) parts
    ("OS", "BITS Pilani B.E."),
    ("Host", "New Delhi, India"),
    ("Role", "AI Agent & Automation Engineer"),
    ("Kernel", "Python, Go, TypeScript"),
    ("Agents", "LangChain, MCP, RAG"),
    ("Memory", "ChromaDB, Pinecone, Weaviate"),
    ("Infra", "Docker, Kubernetes, AWS, GCP"),
    ("Uptime", "shipping since 2023"),
    ("Mode", "production (demo mode: off)"),
]


def plain(v):
    return v if isinstance(v, str) else "".join(text for text, _ in v)

FINAL_CMD = "man ujjwal"

# Pixel-art agent. a=body h=highlight s=screen e=eye m=mouth o=antenna light d=feet
LOGO = [
    ".......o.......",
    ".......a.......",
    "..hhhhhhhhhhh..",
    ".aaaaaaaaaaaaa.",
    "aaasssssssssaaa",
    "aaa" + "seesssees" + "aaa",
    "aaa" + "seesssees" + "aaa",
    ".aa" + "sssssssss" + "aa.",
    ".aa" + "ssmmmmmss" + "aa.",
    ".aa" + "sssssssss" + "aa.",
    ".aaaaaaaaaaaaa.",
    "..aaaaaaaaaaa..",
    "....dd...dd....",
    "...dddd.dddd...",
]
LOGO_COLORS = {"a": "#58a6ff", "h": "#a5d6ff", "s": "#0b2545", "e": "#7ee787",
               "m": "#7ee787", "o": "#ff7b72", "d": "#1f6feb"}

TERMINAL_COLORS = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"]

# ---------------------------------------------------------------- rendering helpers
out = []          # SVG body elements
keyframes = []    # per-element keyframes (cursor moves)


def baseline(row):
    return Y0 + row * LH


def text_run(x, y, text, cls):
    """One run of text pinned to the character grid."""
    lead = len(text) - len(text.lstrip(" "))
    core = text.strip(" ")
    if not core:
        return ""
    x += lead * CW
    tl = f' textLength="{len(core) * CW:.1f}" lengthAdjust="spacing"' if len(core) > 1 else ""
    classes = " ".join(cls.split())
    return f'<text x="{x:.1f}" y="{y}" class="{classes}"{tl}>{escape(core)}</text>'


def line(row, parts, delay=None, x=X0):
    """A row made of (text, classes) parts, appearing at `delay` seconds."""
    y, col, runs = baseline(row), 0, []
    for text, cls in parts:
        runs.append(text_run(x + col * CW, y, text, cls))
        col += len(text)
    body = "".join(runs)
    out.append(f'<g class="a" style="animation-delay:{delay:.2f}s">{body}</g>' if delay is not None else body)
    return col


def prompt(user, host):
    return [(user, "g B"), ("@", "w"), (host, "b B"), (":", "w"), ("~", "p B"), ("$ ", "w")]


def type_out(row, start_col, text, t_prompt, t_start, step, final=False):
    """Typewriter: one <text> per char + a block cursor that tracks it. Returns end time."""
    y = baseline(row)
    for i, ch in enumerate(text):
        if ch != " ":
            out.append(f'<text x="{X0 + (start_col + i) * CW:.1f}" y="{y}" class="fg c" '
                       f'style="animation-delay:{t_start + (i + 1) * step:.2f}s">{escape(ch)}</text>')
    t_end = t_start + len(text) * step
    cx, cy = X0 + start_col * CW, y - FS + 2
    n = len(text)
    name = f"mv{len(keyframes)}"
    keyframes.append(f"@keyframes {name}{{from{{transform:translateX(0)}}to{{transform:translateX({n * CW:.1f}px)}}}}")
    if final:
        # moves while typing, then stays and blinks forever
        style = (f"animation:{name} {n * step:.2f}s steps({n}) {t_start:.2f}s both,"
                 f"fade 1ms linear {t_prompt:.2f}s both,"
                 f"blink 1.1s linear {t_end:.2f}s infinite")
        out.append(f'<rect class="cur" x="{cx:.1f}" y="{cy}" width="{CW:.1f}" height="{FS + 2}" '
                   f'style="{style};transform:translateX({n * CW:.1f}px)"/>')
    else:
        # visible only from the prompt until a beat after typing ends
        style = (f"animation:{name} {n * step:.2f}s steps({n}) {t_start:.2f}s both,"
                 f"on {t_end + 0.25 - t_prompt:.2f}s linear {t_prompt:.2f}s")
        out.append(f'<rect class="cur pc" x="{cx:.1f}" y="{cy}" width="{CW:.1f}" height="{FS + 2}" style="{style}"/>')
    return t_end


def logo(x, y, t0):
    """Pixel art, revealed top to bottom like a scanline; eyes blink, antenna pulses."""
    eyes, antenna = [], []
    for r, row in enumerate(LOGO):
        rects, c = [], 0
        while c < len(row):
            ch = row[c]
            base = "s" if ch == "e" else ch  # eyes sit on top of the screen
            if base in ".o":
                if ch == "o":
                    antenna.append((c, r))
                c += 1
                continue
            start = c
            while c < len(row) and ("s" if row[c] == "e" else row[c]) == base:
                if row[c] == "e":
                    eyes.append((c, r))
                c += 1
            rects.append(f'<rect x="{x + start * P}" y="{y + r * P}" width="{(c - start) * P}" '
                         f'height="{P}" fill="{LOGO_COLORS[base]}"/>')
        out.append(f'<g class="a" style="animation-delay:{t0 + r * 0.04:.2f}s">{"".join(rects)}</g>')
    t_done = t0 + len(LOGO) * 0.04
    eye_rects = "".join(f'<rect x="{x + c * P}" y="{y + r * P}" width="{P}" height="{P}" fill="{LOGO_COLORS["e"]}"/>'
                        for c, r in eyes)
    out.append(f'<g style="animation:fade 1ms linear {t_done:.2f}s both,wink 5s linear {t_done + 1:.2f}s infinite">'
               f'{eye_rects}</g>')
    ant = "".join(f'<rect x="{x + c * P}" y="{y + r * P}" width="{P}" height="{P}" fill="{LOGO_COLORS["o"]}"/>'
                  for c, r in antenna)
    out.append(f'<g style="animation:fade 1ms linear {t0:.2f}s both,pulse 1.6s ease-in-out {t_done:.2f}s infinite">'
               f'{ant}</g>')


# ---------------------------------------------------------------- timeline
row, t = 0, 0.3

# ujjwal@github:~$ neofetch
col = line(row, prompt(*HOST), t)
t = type_out(row, col, "neofetch", t, t + 0.4, 0.08)

# neofetch output
row += 2
t += 0.35
neo_top = baseline(row) - FS
neo_rows = 2 + len(NEOFETCH) + 1
logo_h = len(LOGO) * P
logo(X0 + 6, neo_top + (neo_rows * LH - logo_h) // 2 - 4, t)

ix = X0 + 6 + len(LOGO[0]) * P + 40  # info column x
user_host = f"{HOST[0]}@{HOST[1]}"
line(row, [(HOST[0], "g B"), ("@", "w"), (HOST[1], "b B")], t, x=ix)
line(row + 1, [("-" * len(user_host), "fg")], t + 0.06, x=ix)
key_w = max(len(k) for k, _ in NEOFETCH) + 2
for i, (k, v) in enumerate(NEOFETCH):
    value = [(v, "fg")] if isinstance(v, str) else v
    line(row + 2 + i, [(f"{k}:", "lb B"), (" " * (key_w - len(k) - 1), "fg"), *value], t + 0.12 + i * 0.07, x=ix)
blocks_row = row + 2 + len(NEOFETCH)
by = baseline(blocks_row) - FS + 4
blocks = "".join(f'<rect x="{ix + i * 3 * CW:.1f}" y="{by}" width="{3 * CW:.1f}" height="{FS + 2}" fill="{c}"/>'
                 for i, c in enumerate(TERMINAL_COLORS))
t_blocks = t + 0.12 + len(NEOFETCH) * 0.07
out.append(f'<g class="a" style="animation-delay:{t_blocks:.2f}s">{blocks}</g>')

# ujjwal@github:~$ man ujjwal█
row = blocks_row + 2
t = t_blocks + 0.6
col = line(row, prompt(*HOST), t)
type_out(row, col, FINAL_CMD, t, t + 0.4, 0.075, final=True)

H = baseline(row) + 22

# ---------------------------------------------------------------- assemble
css = f"""
text{{font-family:{FONT};font-size:{FS}px;fill:{COLORS['fg']};white-space:pre}}
{''.join(f'.{k}{{fill:{v}}}' for k, v in COLORS.items())}
.B{{font-weight:700}}
.title{{font-size:13px;fill:{COLORS['d']}}}
.cur{{fill:{COLORS['fg']};opacity:.85}}
.pc{{opacity:0}}
.a{{animation:fade .14s ease-out both}}
.c{{animation:fade 1ms linear both}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes on{{from,to{{opacity:.85}}}}
@keyframes blink{{0%,49%{{opacity:.85}}50%,100%{{opacity:0}}}}
@keyframes wink{{0%,91%,97%,100%{{opacity:1}}94%{{opacity:0}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
{''.join(keyframes)}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" xml:space="preserve" role="img" aria-labelledby="t d">
<title id="t">ujjwal@github: terminal</title>
<desc id="d">{escape("A terminal running neofetch. " + '; '.join(f'{k}: {plain(v)}' for k, v in NEOFETCH))}.</desc>
<style><![CDATA[{css}]]></style>
<defs><clipPath id="win"><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10"/></clipPath></defs>
<g clip-path="url(#win)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect width="{W}" height="{TOP}" fill="{BAR}"/>
<line x1="0" y1="{TOP}" x2="{W}" y2="{TOP}" stroke="{BORDER}"/>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{BORDER}"/>
<circle cx="20" cy="18" r="6" fill="#ff5f57"/><circle cx="40" cy="18" r="6" fill="#febc2e"/><circle cx="60" cy="18" r="6" fill="#28c840"/>
<text x="{W / 2}" y="23" text-anchor="middle" class="title">{HOST[0]}@{HOST[1]}: ~</text>
<g shape-rendering="crispEdges">
{chr(10).join(out)}
</g>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg)
print(f"wrote {OUT.relative_to(Path.cwd()) if OUT.is_relative_to(Path.cwd()) else OUT} ({W}x{H}, {len(svg) / 1024:.1f} KB)")
