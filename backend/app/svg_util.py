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
    """
    out = normalize_placeholders(svg)
    if color:
        out = out.replace("{c}", color)
    if text_color:
        out = out.replace("{t}", text_color)
    if text:
        out = out.replace("{n}", _xml_escape(text))
    if font_family:
        out = _set_font_family(out, _xml_escape(font_family))
    return out
