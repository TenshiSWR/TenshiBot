import regex


def fix_self_closed_tags(page: str, text: str):
    return regex.sub(r"<((?:(?!(?:br|references))[^\/>])+)[^>]*>((?:(?!<\/\1>).)*?)<\1 *\/>", r"<\1>\2</\1>", text, flags=regex.DOTALL)
