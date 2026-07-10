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
    out = out.replace("{n}", str(n))
    out = out.replace("{c}", color or "")
    out = out.replace("{t}", text_color or "")
    return out
