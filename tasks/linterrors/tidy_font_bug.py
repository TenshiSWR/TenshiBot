import regex


def fix_tidy_font_bug(page: str, text: str) -> str:
    _ = text
    while True:
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[([^|:]+)\|([^|]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", text)
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[([^|:]+)\]\](<\/(?:font|span)>)", r"[[\2|\1\2\3]]", _)
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[((?:Commons|Help|Help[ _]talk|MediaWiki|MediaWiki[ _]talk|Meta|Meta[ _]talk|Module|Module[ _]talk|Project|Project[ _]talk|Talk|Template|Template[ _]talk|User|User[ _]talk|Wik(?:i(?:books|data|functions|news|pedia|quote|source|versity|voyage)|tionary)):[^|]+)\|([^|]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", _)
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[((?:Commons|Help|Help[ _]talk|MediaWiki|MediaWiki[ _]talk|Meta|Meta[ _]talk|Module|Module[ _]talk|Project|Project[ _]talk|Talk|Template|Template[ _]talk|User|User[ _]talk|Wik(?:i(?:books|data|functions|news|pedia|quote|source|versity|voyage)|tionary)):[^|\]]+)\]\](<\/(?:font|span)>)", r"[[\2|\1\2\3]]", _)
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[(:(?:Category|File):[^|:]+)\|([^|\]]*)\]\](<\/(?:font|span)>)", r"[[\2|\1\3\4]]", _)
        _ = regex.sub(r"(<(?:font|span)[^>]*>)\[\[:((?:Category|File):[^|\]]+)\]\](<\/(?:font|span)>)", r"[[:\2|\1\2\3]]", _)
        if _ == text:
            break
        else:
            text = _
    return text
