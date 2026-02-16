import regex


def fix_multi_colon_escape(page: str, text: str) -> str:
    return regex.sub(r"\[\[:(:.*)\]\]", r"[[\1]]", text)
