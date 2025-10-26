import regex

regexes = {
    r"<(?!(?:nowiki|syntaxhighlight))([^ >]*)([^>]*)?> *(?<!')''(?!')(.*)<\/\1>(?<!')''(?!')": r"''<\1\2>\3</\1>''",
    r"(?<!')''(?!') *<(?!(?:nowiki|syntaxhighlight))([^ >]*)([^>]*)?>((?:(?!<\/\1>).)*)(?<!')''(?!')(.*)<\/\1>": r"<\1\2>''\3''\4</\1>",
    r"<(?!(?:nowiki|syntaxhighlight))([^ >]*)([^>]*)?>( *)<(?!(?:nowiki|syntaxhighlight|\1))([^ >]*)([^>]*)?>((?:(?!(?:<\/\4>|<\1(?:[^>]*)?>)).)*)<\/\1>( *)<\/\4>": r"<\1\2>\3<\4\5>\6</\4>\7</\1>",
    r"<(?!(?:nowiki|syntaxhighlight))([^ >]*)([^>]*)?>( *)<(?!(?:nowiki|syntaxhighlight|\1))([^ >]*)([^>]*)?>((?:(?!(?:<\/\4>|<\1(?:[^>]*)?>)).)*)<\/\1>((?:(?!<\/\1>).)+)<\/\4>": r"<\1\2>\3<\4\5>\6</\4\5></\1><\4\5>\6</\4>",
    r"<(?!(?:nowiki|syntaxhighlight))([^ >]*)([^>]*)?>((?:(?!<\/\1>).)+)<(?!(?:nowiki|syntaxhighlight|\1))([^ >]*)([^>]*)?>((?:(?!(?:<\/\4>|<\1(?:[^>]*)?>)).)*)<\/\1>((?:(?!(?:<\4>|<\/\4>)).)*)<\/\4>": r"<\1\2>\3</\1><\4\5><\1\2>\6</\1>\7</\4>",
    r"'''((?:(?!''').)*)(?<!')''(?!')((?:(?!(?:(?<!')''(?!')|'''''|''')).)*)'''((?:(?!''').)*)(?<!')''(?!')": r"'''\1''' '''''\2'''\3''"
}


def fix_misnests(page: str, text: str) -> tuple:
    lines = text.split("\n")
    fixes = []
    for i, line in enumerate(lines):
        new_line = line
        for find, replace in regexes.items():
            if not regex.search(r"<(?:nowiki|syntaxhighlight)>.*"+find+r".*<\/(?:nowiki|syntaxhighlight)>", line):
                new_line = regex.sub(find, replace, new_line)
        if new_line != line:
            fixes.append((i, new_line))
    i = 0
    while i < len(fixes):
        if regex.search(r"\{\{(?:(?!(?:'''?|<\/?[^ >]*>)))\}\}", fixes[i][1]):
            print("(Filtering) Illegal combination in template invocation")
        elif regex.search(r"(?:<[^/][^>]*>.*\[\[.*<\/[^>]*>.*\]\]|\[\[.*<[^/][^>]*>.*\]\].*<\/[^>]*>)", fixes[i][1]):
            print("(Filtering) Illegal combination in wikilink")
        else:
            i += 1
            continue
        fixes.pop(i)
        i = 0
    for fix in fixes:
        lines[fix[0]] = fix[1]
    text = "\n".join(lines)
    return text, "6 (Trial)"

