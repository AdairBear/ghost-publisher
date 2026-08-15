#!/usr/bin/env python3
"""Trident share-card (OG image) generator.

Tiers: field | shortform | signal | digest. Only the category pill takes the
tier colour; trident, wordmark, N-degree marker and rule stay brand gold
#D4A84A. Outputs a 2400x1260 PNG (1.9:1, the Open Graph shape).

Font stacks are ordered best-first. Inter / Twist Sans are listed ahead of the
fallbacks so the render upgrades automatically once those are installed —
no code change needed. See `check_fonts()` for what is actually resolvable.
"""

from __future__ import annotations

import argparse
import subprocess

import cairosvg

W, H = 1200, 630
INK, WHITE, GREY, LABEL, MOTTO = "#07090C", "#F5F6F7", "#A8AEB8", "#7C828D", "#6b7079"
BRAND = "#D4A84A"

# Lowest baseline the sub-headline may occupy before it collides with the
# footer row (site URL / motto) at y=580.
SUB_BOTTOM = 545

# Best-first font stacks. Real display faces lead; installed fallbacks follow.
# "Twist Sans" must carry its space: that is the font's real family name, and
# cairo's font selection matches families literally. `fc-match TwistSans` DOES
# resolve (fontconfig ignores spaces), which makes the wrong spelling look
# correct from the shell while cairosvg silently renders the default face.
TITLE_FONT = "Twist Sans, Inter, Liberation Sans, Helvetica Neue, Helvetica, sans-serif"
BODY_FONT = "Inter Variable, Inter, Liberation Sans, Helvetica Neue, sans-serif"
MONO_FONT = "JetBrains Mono, Menlo, monospace"
ITALIC_FONT = "Inter Variable, Inter, Helvetica Neue, sans-serif"

TIERS = {
    "field": ("FIELD NOTES", "#D4A84A"),
    "shortform": ("SHORT FORM NOTE", "#5AB0C4"),
    "signal": ("SIGNAL", "#3EAE5E"),
    "digest": ("DIGEST", "#A78BFA"),
    # Not a content tier — the site's front door. Rendered without an issue
    # number so it never reads as a numbered piece in the series.
    "intro": ("INTRODUCTION", "#D4A84A"),
}
DEFAULT_KICK = {
    "field": "BUILDING ALONE WITH AI",
    "shortform": "SHORT FORM NOTE",
    "signal": "ONE ARTIFACT, ONE TAKE",
    "digest": "TRADING + AUTOMATION",
    "intro": "START HERE",
}


def esc(s: str) -> str:
    """XML-escape a string for safe interpolation into SVG text.

    Args:
        s: Raw text.

    Returns:
        The text with &, < and > escaped.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text: str, max_px: float, char_px: float) -> list[str]:
    """Greedily wrap text to an approximate pixel width.

    Args:
        text: The text to wrap.
        max_px: Maximum line width in pixels.
        char_px: Estimated advance width of one character in pixels.

    Returns:
        The wrapped lines.
    """
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) * char_px <= max_px or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def trident(c: str, sw: int = 7) -> str:
    """Render the trident glyph as an SVG fragment.

    Args:
        c: Stroke and fill colour.
        sw: Stroke width.

    Returns:
        An SVG `<g>` fragment, unpositioned.
    """
    return (
        f'<g stroke="{c}" stroke-width="{sw}" stroke-linecap="round" fill="none">'
        '<path d="M22 54 H78"/><path d="M24 54 V31"/><path d="M50 54 V23"/>'
        '<path d="M76 54 V31"/><path d="M50 54 V126"/></g>'
        f'<g fill="{c}"><path d="M24 30 l-6 10 h12 z"/><path d="M50 22 l-6 10 h12 z"/>'
        '<path d="M76 30 l-6 10 h12 z"/><path d="M50 127 l-9 -12 9 -7 9 7 z"/></g>'
    )


def pill_width(
    t: str, fs: int = 13, ls: float = 2.6, padx: int = 20, dot: int = 8, gap: int = 12
) -> float:
    """Estimate the rendered width of the category pill.

    Args:
        t: Pill label text.
        fs: Font size in pixels.
        ls: Letter spacing in pixels.
        padx: Horizontal padding on each side.
        dot: Diameter of the leading dot.
        gap: Gap between dot and text.

    Returns:
        The pill width in pixels.
    """
    return len(t) * fs * 0.62 + (len(t) - 1) * ls + dot + gap + 2 * padx


def build_svg(
    tier: str,
    num: str | None,
    kick: str,
    title: str,
    sub: str,
    pill: str | None = None,
) -> str:
    """Build the share card as an SVG document.

    Args:
        tier: One of `field`, `shortform`, `signal`, `digest`, `intro`.
        num: Issue number shown after the degree sign. Pass an empty string
            (or None) for an unnumbered card — the `N°` marker is dropped and
            the kicker stands alone. Used by the `intro` front-door card, which
            is not part of the numbered series.
        kick: Kicker text following the issue number.
        title: Card headline.
        sub: Sub-headline / excerpt.
        pill: Override for the category pill label.

    Returns:
        The complete SVG document as a string.

    Raises:
        KeyError: `tier` is not a known tier.
    """
    pill_label, c = TIERS[tier]
    if pill:
        pill_label = pill

    # An unnumbered card drops the "N° xx /" marker entirely and promotes the
    # kicker into the brand colour, so the eyebrow line still carries weight.
    kicker_svg = (
        f'<tspan fill="{BRAND}" font-weight="600">N&#176; {esc(num)}</tspan> / {esc(kick)}'
        if num
        else f'<tspan fill="{BRAND}" font-weight="600">{esc(kick)}</tspan>'
    )

    ts = 86 if len(title) <= 22 else 80 if len(title) <= 34 else 72
    tl = wrap(title, 890, ts * 0.53)
    while len(tl) > 3 and ts > 60:
        ts -= 6
        tl = wrap(title, 890, ts * 0.53)

    sl = wrap(sub, 800, 25 * 0.5)[:3]
    lh = ts * 1.05
    ty0 = {1: 398, 2: 360, 3: 330}.get(len(tl), 330)
    # A tall title pushes the sub-headline down; drop any line that would
    # collide with the footer row at y=580 rather than overprinting it.
    sy0_probe = ty0 + (len(tl) - 1) * lh + 58
    fits = 0 if sy0_probe > SUB_BOTTOM else int((SUB_BOTTOM - sy0_probe) // 34) + 1
    sl = sl[:fits]

    pw = pill_width(pill_label)
    px0 = (W - 72) - pw
    dot_cx = px0 + 24
    ptext_x = px0 + 40

    tsvg = "".join(
        f'<text x="72" y="{ty0 + i * lh:.0f}" font-family="{TITLE_FONT}" '
        f'font-weight="bold" font-size="{ts}" letter-spacing="-0.9" '
        f'fill="{WHITE}">{esc(line)}</text>'
        for i, line in enumerate(tl)
    )
    sy0 = ty0 + (len(tl) - 1) * lh + 58
    ssvg = "".join(
        f'<text x="72" y="{sy0 + i * 34:.0f}" font-family="{BODY_FONT}" font-size="25" fill="{GREY}">{esc(line)}</text>'
        for i, line in enumerate(sl)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><radialGradient id="bg" cx="12%" cy="0%" r="130%"><stop offset="0%" stop-color="#12161d"/><stop offset="42%" stop-color="#0a0d12"/><stop offset="100%" stop-color="{INK}"/></radialGradient></defs>
<rect width="{W}" height="{H}" rx="26" fill="{INK}"/><rect width="{W}" height="{H}" rx="26" fill="url(#bg)"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="26" fill="none" stroke="#ffffff" stroke-opacity="0.10"/>
<g transform="translate(1030,60) scale(3.3)" opacity="0.06">{trident(BRAND, 7)}</g>
<g transform="translate(70,58) scale(0.56)">{trident(BRAND, 8)}</g>
<text x="140" y="98" font-family="{MONO_FONT}" font-size="22" letter-spacing="7.2" fill="{WHITE}">THOMAS ADAIR</text>
<rect x="{px0:.0f}" y="70" width="{pw:.0f}" height="38" rx="19" fill="none" stroke="{c}" stroke-opacity="0.45"/>
<circle cx="{dot_cx:.0f}" cy="89" r="4" fill="{c}"/>
<text x="{ptext_x:.0f}" y="94" font-family="{MONO_FONT}" font-size="13" font-weight="600" letter-spacing="2.6" fill="{c}">{esc(pill_label)}</text>
<text x="72" y="238" font-family="{MONO_FONT}" font-size="16" letter-spacing="3.0" fill="{LABEL}">{kicker_svg}</text>
<rect x="72" y="258" width="96" height="3" fill="{BRAND}"/>
{tsvg}
{ssvg}
<text x="72" y="580" font-family="{MONO_FONT}" font-size="16" letter-spacing="1.0" fill="{LABEL}">thomasadair.ghost.io</text>
<text x="{W - 72}" y="580" text-anchor="end" font-family="{ITALIC_FONT}" font-style="italic" font-size="16" fill="{MOTTO}">Rigor should not be a privilege.</text>
</svg>'''


def render_png(svg: str, out_path: str) -> None:
    """Rasterise an SVG card to a 2400x1260 PNG.

    Args:
        svg: The SVG document.
        out_path: Destination PNG path.
    """
    cairosvg.svg2png(
        bytestring=svg.encode(),
        write_to=out_path,
        output_width=2400,
        output_height=1260,
    )


def check_fonts() -> dict[str, bool]:
    """Report which named display faces fontconfig can actually resolve.

    Purely diagnostic — the SVG font stacks degrade on their own.

    Returns:
        Mapping of family name to whether it is installed.
    """
    wanted = ["Inter", "Twist Sans", "JetBrains Mono", "Liberation Sans"]
    found = {}
    for family in wanted:
        try:
            out = subprocess.run(
                ["fc-list", "-q", family],
                capture_output=True,
                timeout=10,
                check=False,
            )
            found[family] = out.returncode == 0
        except (OSError, subprocess.SubprocessError):
            found[family] = False
    return found


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ["tier", "num", "kick", "title", "sub", "out"]:
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--pill", default=None)
    a = ap.parse_args()

    svg = build_svg(a.tier, a.num, a.kick, a.title, a.sub, a.pill)
    render_png(svg, a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
