import re


def normalize_placeholders(s: str) -> str:
    replacements = [
        ("${displayText}", "{n}"), ("{{displayText}}", "{n}"), ("$displayText", "{n}"),
        ("{displayText}", "{n}"), ("{{count}}", "{n}"), ("{count}", "{n}"),
        ("{{number}}", "{n}"), ("{{n}}", "{n}"),
        ("${qpyscolor}", "{c}"), ("{{qpyscolor}}", "{c}"), ("$qpyscolor", "{c}"),
        ("{qpyscolor}", "{c}"), ("{{bubbleColor}}", "{c}"), ("{{c}}", "{c}"),
        ("${qpwzcolor}", "{t}"), ("{{qpwzcolor}}", "{t}"), ("$qpwzcolor", "{t}"),
        ("{qpwzcolor}", "{t}"), ("{{textColor}}", "{t}"), ("{{color}}", "{t}"),
        ("{color}", "{t}"), ("{{t}}", "{t}"),
    ]
    out = s or ""
    for src, dst in replacements:
        out = out.replace(src, dst)
    return out


def fill_svg(tpl: str, color: str = "", text_color: str = "", n: int = 12) -> str:
    out = normalize_placeholders(tpl)
    return out


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _set_font_family(svg: str, font_family: str) -> str:
    """Add or replace font-family on every <text> tag."""
    def _patch(m: "re.Match") -> str:
        tag = m.group(0)
        if re.search(r'font-family\s*=\s*"[^"]*"', tag):
            tag = re.sub(r'font-family\s*=\s*"[^"]*"', f'font-family="{font_family}"', tag)
        elif re.search(r"font-family\s*=\s*'[^']*'", tag):
            tag = re.sub(r"font-family\s*=\s*'[^']*'", f"font-family='{font_family}'", tag)
        else:
            tag = tag.replace(">", f' font-family="{font_family}">', 1)
        return tag

    return re.sub(r"<text\b[^>]*>", _patch, svg)


_COLOR_VALUE_RE = re.compile(r"^#[0-9a-fA-F]{3,8}$|^rgba?\(", re.IGNORECASE)


def _first_text_fill(svg: str) -> str:
    """First hardcoded fill color on a <text> element (mirrors frontend autoMapColors)."""
    m = re.search(r'<text\b[^>]*?\bfill\s*=\s*["\']([^"\']+)["\']', svg, re.IGNORECASE)
    if m and _COLOR_VALUE_RE.match(m.group(1)):
        return m.group(1)
    return ""


def _first_shape_color(svg: str, exclude: str) -> str:
    """First hardcoded fill/stroke color other than `exclude`."""
    for m in re.finditer(
        r"(?:fill|stroke)\s*=\s*[\"'](#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))[\"']",
        svg,
        re.IGNORECASE,
    ):
        if m.group(1) != exclude:
            return m.group(1)
    return ""


def apply_customizations(
    svg: str,
    color: str = "",
    text_color: str = "",
    text: str = "",
    font_family: str = "",
) -> str:
    """Fill user-customized values into the template.

    Only non-empty values are applied; unset items keep their {c}/{t}/{n}
    placeholders for downstream replacement.

    Templates without {c}/{t} placeholders (hardcoded colors like
    fill="#030000") are mapped heuristically, mirroring the frontend
    autoMapColors(): <text> fill -> text_color, first other fill/stroke
    -> color (all occurrences of that value are replaced).
    """
    out = normalize_placeholders(svg)
    has_c = "{c}" in out
    has_t = "{t}" in out
    text_fill = "" if has_t else _first_text_fill(out)
    if text_color:
        out = out.replace("{t}", text_color)
        if not has_t and text_fill:
            out = out.replace(text_fill, text_color)
    if color:
        out = out.replace("{c}", color)
        if not has_c:
            exclude = (text_color or text_fill) if text_fill else ""
            bc = _first_shape_color(out, exclude)
            if bc:
                out = out.replace(bc, color)
    if text:
        out = out.replace("{n}", _xml_escape(text))
    if font_family:
        out = _set_font_family(out, _xml_escape(font_family))
    return out
