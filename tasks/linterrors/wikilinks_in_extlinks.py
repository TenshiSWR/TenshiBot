import regex


def fix_wikilinks_in_extlinks(page: str, text: str) -> str:
    return regex.sub(r"((?<!\[)\[(?!\[)[^ ]+.*)\[\[([^|]*)\]\](.*\])", r"\1\2\3", text)
