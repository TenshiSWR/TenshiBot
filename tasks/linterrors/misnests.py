import regex

regexes = {
    r"<([^ >]*)([^>]*)?> *''(.*)<\/\1>(?<!')''(?!')": r"''<\1\2>\3</\1>''",
    r"(?<!')''(?!') *<([^ >]*)([^>]*)?>(.*)''(.*)<\/\1>": r"<\1\2>''\3''\4</\1>",
    r"<([^ >]*)([^>]*)?>(.*)<([^ >]*)([^>]*)?>(.*)<\/\1>(.*)<\/\4>": r"<\1\2>\3</\1><\4\5><\1\2>\6</\1>\7</\4>",
    r"'''(.*)(?<!')''(?!')(.*)'''(.*)(?<!')''(?!')": r"'''\1''' '''''\2'''\3''"
}


def fix_misnests(page: str, text: str) -> tuple:
    lines = text.split("\n")
    fixes = []
    for i, line in enumerate(lines):
        new_line = line
        for find, replace in regexes.items():
            new_line = regex.sub(find, replace, new_line)
        if new_line != line:
            fixes.append((i, new_line))
    for fix in fixes:
        lines[fix[0]] = fix[1]
    text = "\n".join(lines)
    return text, 6


