import regex


def fix_wikilinks_in_extlinks(page: str, text: str) -> str:
    _ = text
    while True:
        _ = regex.sub(r"((?<!\[)\[(?!\[)[^ \]]+[^\]]*)\[\[((?:(?!(?:\]\]|\|)).)*)\]\](.*\])", r"\1\2\3", text)
        _ = regex.sub(r"(\[https?:\/\/[^\{\]]+?)(\{\{[Dd]ead(?:(?:(?!(?:\{\{(?![^\}]*?\}\})|\}\})).)*?)\}\}(?:\{\{cbignore\|bot=medic\}\})?)(.*?(?<!(?:\[\[.*|<nowiki>|\]\]))\](?![^\n]*<\/nowiki>))", r"\1\3\2", _)
        if _ == text:
            break
        else:
            text = _
    return text
