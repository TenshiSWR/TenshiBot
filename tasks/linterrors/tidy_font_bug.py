import regex


def fix_tidy_font_bug(page: str, text: str) -> str:
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[([^|:]+)\|([^|]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", text)
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[([^|:]+)\]\](<\/(?:font|span)>)", r"[[\2|\1\2\3]]", text)
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[((?:Commons|Help|Help talk|MediaWiki|MediaWiki talk|Meta|Meta talk|Module|Module talk|Project|Project talk|Talk|Template|Template talk|User|User talk|Wik(?:i(?:books|data|functions|news|pedia|quote|source|versity|voyage)|tionary)):[^|]+)\|([^|]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", text)
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[((?:Commons|Help|Help talk|MediaWiki|MediaWiki talk|Meta|Meta talk|Module|Module talk|Project|Project talk|Talk|Template|Template talk|User|User talk|Wik(?:i(?:books|data|functions|news|pedia|quote|source|versity|voyage)|tionary)):[^|\]]+)\]\](<\/(?:font|span)>)", r"[[\2|\1\2\3]]", text)
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[(:(?:Category|File):[^|:]+)\|([^|\]]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", text)
    text = regex.sub(r"(<(?:font|span)[^>]*>)\[\[:((?:Category|File):[^|\]]+)\]\](<\/(?:font|span)>)", r"[[:\2|\1\2\3]]", text)
    return text
