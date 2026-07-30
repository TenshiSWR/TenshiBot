import regex


def fix_missing_end_tag(page: str, text: str):
    text = regex.sub(r"^( *)(?<!')('')(?!')((?:(?!'{2,}).)*?)\n(?<!')\2(?!')", r"\1\2\3\2", text, flags=regex.MULTILINE)
    text = regex.sub(r"^( *)(?<!')(''')(?!')((?:(?!'{2,}).)*?)\n(?<!')\2(?!')", r"\1\2\3\2", text, flags=regex.MULTILINE)
    return text
