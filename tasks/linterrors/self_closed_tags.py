import regex


def fix_self_closed_tags(page: str, text: str):
    return regex.sub(r"<((?:(?!(?:br|hr|includeonly|noinclude|nowiki|ref|references|syntaxhighlight))[^\/>])+)[^>]*>((?:(?!<\/\1>|br|nowiki|references|syntaxhighlight).)*?)<\1 *\/>", r"<\1>\2</\1>", text, flags=regex.DOTALL)
