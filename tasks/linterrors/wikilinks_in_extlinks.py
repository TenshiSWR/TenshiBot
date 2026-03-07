import regex


def fix_wikilinks_in_extlinks(page: str, text: str) -> str:
    _ = text
    while True:
        _ = regex.sub(r"((?<!\[)\[(?!\[)[^ \]]+[^\]]*)\[\[((?:(?!(?:\]\]|\|)).)*)\]\](.*\])", r"\1\2\3", text)
        if _ == text:
            break
        else:
            text = _
    return text
