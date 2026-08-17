#!/usr/bin/env python3
"""Trident share-card (OG image) generator.

Tiers: field | shortform | signal | digest. Only the category pill takes the
tier colour; trident, wordmark, N-degree marker and rule stay brand gold
#D4A84A. Outputs a 2400x1260 PNG (1.9:1, the Open Graph shape).

Font stacks are ordered best-first. Inter / FC Twist are listed ahead of the
fallbacks so the render upgrades automatically once those are installed —
no code change needed. See `check_fonts()` for what is actually resolvable.
"""

from __future__ import annotations

import argparse
import re
import subprocess

import cairosvg

W, H = 1200, 630
INK, WHITE, GREY, LABEL, MOTTO = "#07090C", "#F5F6F7", "#A8AEB8", "#7C828D", "#6b7079"
BRAND = "#D4A84A"

# Lowest baseline the sub-headline may occupy before it collides with the
# footer row (site URL / motto) at y=580.
SUB_BOTTOM = 545

# Best-first font stacks. Real display faces lead; installed fallbacks follow.
# The brand face is registered as "FC Twist [Non-commercial]" — brackets and
# all. Cairo matches family names literally, so the shorter "FC Twist" silently
# renders the default face instead. Quoted because brackets are not valid in an
# unquoted CSS family name. Verified by render hash, not by fc-match: the
# brackets and hyphen are fontconfig *pattern* syntax, so `fc-match` reports
# Verdana for this family even though cairosvg resolves it correctly.
TITLE_FONT = (
    "'FC Twist [Non-commercial]', Inter, Liberation Sans, "
    "Helvetica Neue, Helvetica, sans-serif"
)
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


# Brand mark geometry, lifted verbatim from the launch asset
# trident-launch-2026-08-15/trident_mark_amber.svg so it cannot drift from the
# source file. The gold is swapped for the caller's colour at render time; the
# shadow (#9E7228), highlight (#F5E9C2) and outline (#6E4E14) tones model the
# mark's form rather than theme it, so they stay fixed.
_MARK_GOLD = "#D4A84A"
_MARK_PATHS = (
    '<path d="M56,117 L72,117 C71,135 70,150 69,158 L59,158 C58,150 57,135 56,117 Z" fill="#D4A84A" stroke="#6E4E14" stroke-width="1.4" stroke-linejoin="round"/>'
    '<path d="M60,121 L64.5,121 L63,155 L61,155 Z" fill="#F5E9C2"/>'
    '<path d="M64,119 L69,158 L64,158 Z" fill="#9E7228" opacity="0.55"/>'
    '<path d="M54,156 L74,156 L75,165 L53,165 Z" fill="#D4A84A" stroke="#6E4E14" stroke-width="1.4" stroke-linejoin="round"/>'
    '<path d="M53,165 C53,165 75,165 75,165 C77,177 69,183 64,183 C59,183 51,177 53,165 Z" fill="#D4A84A" stroke="#6E4E14" stroke-width="1.4" stroke-linejoin="round"/>'
    '<path d="M64,165 L75,165 C77,177 69,183 64,183 Z" fill="#9E7228" opacity="0.5"/>'
    '<path d="M57,167 C57,173 60,179 64,180 C61,178 59,173 59,167 Z" fill="#F5E9C2"/>'
    '<path fill="#D4A84A" d="M80.01 116.64c0 1.08-.67 2.04-1.68 2.43c-2 .77-6.05 1.77-13.61 1.77c-7.75 0-11.98-1.05-14.03-1.83c-1-.38-1.65-1.35-1.65-2.42v-15.23h30.98v15.28z"/>'
    '<path fill="none" stroke="#D4A84A" stroke-linecap="round" stroke-miterlimit="10" stroke-width="7" d="M80.01 116.64s-2.56 4.2-15.3 4.2s-15.68-4.25-15.68-4.25"/>'
    '<path fill="#9E7228" d="m52.53 104.8l-3.5 1.43v1.6s3.67 1.24 14.97 1.24s16.01-1.3 16.01-1.3v-3.53z"/>'
    '<path fill="#D4A84A" d="m107.27 40.85l9.75.62c.61.04 1.06-.57.84-1.15L105.04 6.89c-.33-.86-1.53-.92-1.93-.09c-2.24 4.56-7.19 15.64-7.68 25.03c-1.54 14.93 4.18 20.17 6.65 30.12c3.45 13.95-9.19 20.91-24.3 23.15c-1.71.25-3.27-1.03-3.38-2.75l-5.61-49.16l7.14 1.92c.67.18 1.26-.48 1.01-1.13L64.98 3.63A1.06 1.06 0 0 0 64 3c-.62 0-.91.46-.98.63L51.08 33.97a.848.848 0 0 0 1.01 1.13l7.14-1.92l-5.61 49.16c-.11 1.72-1.67 3.01-3.38 2.75c-15.11-2.24-27.76-9.2-24.3-23.15C28.4 52 34.17 46.9 32.59 31.82c-.49-9.39-5.44-20.46-7.68-25.03c-.41-.83-1.6-.77-1.93.09L10.14 40.33c-.22.58.23 1.19.84 1.15l9.75-.62C19.7 46.6 7.21 57.77 7.21 75.27c0 15.6 17.67 31.87 56.79 31.87s56.79-16.28 56.79-31.87c0-17.5-14.83-24.47-13.52-34.42"/>'
    '<path fill="#9E7228" d="m10.17 40.33l12.82-6.36c.52 1.92-2.23 6.88-2.23 6.88l-9.75.62s-.46.04-.76-.25c-.29-.29-.08-.89-.08-.89"/>'
    '<path fill="#F5E9C2" d="M62.29 11.55c.23-.59 1.1-.45 1.13.18c.09 1.94.15 4.57-.05 6.5c-.62 5.85-4.45 8.99-6.58 10.31c-.48.29-1.05-.19-.85-.72zm42.17 3.84c.01-3.62-.53-5.01-1.86-2.11c-1.76 3.85-3.3 10.12-3.99 15.35c-.44 3.34 1.81.76 3.06-1.65c1.14-2.17 2.78-5.79 2.79-11.59m-81.33-1.2c.12-.48.82-.46.91.02c.72 3.55 1.08 8.37-1.59 13.9c-1.83 3.79-5.14 6.17-7.07 7.31a.466.466 0 0 1-.64-.64c1.1-1.88 3.06-5.48 4.91-10.06c1.78-4.39 2.91-8.31 3.48-10.53"/>'
    '<path fill="#9E7228" d="M59.1 34.4s1.1-5.48 1.1-5.71c0-.19-6.84 4.55-9.02 6.07c.19.27.53.43.9.33zm55.83 57.17c2.01-2.48 3.47-5.12 4.43-7.81a25.5 25.5 0 0 0 1.44-8.49c0-17.5-12.16-27.95-13.52-34.41h.03l9.74.62c.61.03 1.04-.58.83-1.15L102.6 30.02c-2.23 8.36 1.14 16.42 4.83 24.11c8.85 18.76 5.5 26.7-4.62 33.39c-8.17 5.4-24.07 9.34-33.44 9.12c-2.53-.06 2.24-5.91 6.38-12.02c-.75-.5-1.27-1.31-1.34-2.28L68.8 33.18l7.14 1.92c.67.18 1.26-.48 1.01-1.13l-10.26-7.4c-.67-.48-1.6-.01-1.61.81L64 107.14c25.06 0 43.65-6.68 50.93-15.57"/>'
    '<path fill="#9E7228" d="M68.86 33.97s-1.06-5.05-1.06-5.28c0-.19 6.84 4.55 9.02 6.07c-.19.27-.53.43-.9.33zM9.56 84.91c5.91 12.16 23.58 22.23 54.44 22.23c0 0-4.87-8.01-11.93-8.01s-23.23-.95-33.2-8.41c-3.04-2.28-5.38-4.8-7.11-7.07c-.91-1.18-2.85-.09-2.2 1.26"/>'
    '<path fill="#F5E9C2" d="M13.36 72.2c-1.43-10.97 8.77-21.51 8.77-21.51c.73-.99 2.27-.15 1.85 1c0 0-7.15 10.93-4.95 20.96c2.1 9.58 11.57 13.88 11.57 13.88c1.02.6.24 2.22-.89 1.88c-5.49-1.62-15.14-6.95-16.35-16.21m36.52 44.37c-.65 1.33.32 2.86 3.17 3.67c2.19.62 5.25 1.07 5.43-1.09c.08-1-1.06-1.81-5.22-2.83c-.78-.19-2.78-.97-3.38.25"/>'
    '<path fill="#9E7228" d="M49.09 113.63c1.17.71 6.66 3.71 15.63 3.71c9.97 0 15.3-4.46 15.3-4.46v-11.52l-6.29 2.88s-.19 2.76-.19 6.86s-9.3 4.08-10.51 4.08c-11.53 0-13.99-4.46-14-4.46l.02 2.87c0 .01.02.03.04.04"/>'
    '<path fill="#9E7228" d="M74.41 115.78s3.31-.91 4.73 1.09c1.9 2.68.32 4.61.32 4.61s4.92-2.23 4.05-5.49c-.82-3.09-3.5-3.1-3.5-3.1l-5.03 1.62z"/>'
)


def trident(c: str) -> str:
    """Render the trident brand mark as an SVG fragment.

    The mark is normalised into the same bounding box the old placeholder
    glyph occupied — 64x112, centred on x=50 with its top at y=22 — so both
    call sites keep their existing size and position on the card. The inner
    group carries the source asset's own 0.88 horizontal squash.

    Args:
        c: The gold to draw the mark in. Per the locked card spec this is
            always `BRAND`; the tier colour never reaches the trident.

    Returns:
        An SVG `<g>` fragment, unpositioned.
    """
    return (
        '<g transform="translate(50,22) scale(0.62222) translate(-64,-3)">'
        '<g transform="translate(64,0) scale(0.88,1) translate(-64,0)">'
        f"{_MARK_PATHS.replace(_MARK_GOLD, c)}"
        "</g></g>"
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
<g transform="translate(1030,60) scale(3.3)" opacity="0.06">{trident(BRAND)}</g>
<g transform="translate(70,58) scale(0.56)">{trident(BRAND)}</g>
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
    wanted = ["Inter", "FC Twist [Non-commercial]", "JetBrains Mono", "Liberation Sans"]
    found = {}
    for family in wanted:
        # `-` `[` `]` `:` `,` are fontconfig *pattern* metacharacters. An
        # unescaped family containing them (e.g. "FC Twist [Non-commercial]")
        # parses as a malformed pattern and reports NOT FOUND for a font that
        # is installed and rendering fine — a false alarm, so escape them.
        pattern = re.sub(r"([-\[\]:,\\])", r"\\\1", family)
        try:
            out = subprocess.run(
                ["fc-list", "-q", pattern],
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
