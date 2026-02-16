import regex


def fix_tidy_font_bug(page: str, text: str) -> str:
    text = regex.sub(r"(<[^>]+>)\[\[([^|]+)\|(.*)\]\](<\/[^>]+>)", r"[[\2|\1\3\4]]", text)
    text = regex.sub(r"(<[^>]+>)\[\[([^|]+)\]\](<\/[^>]+>)", r"[[\2|\1\2\3]]", text)
    return text
