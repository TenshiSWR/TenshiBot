import regex

regexes = {
    r"^((?:(?!(?:(?<!')''(?!')|(?<!')'''''(?!'))).)*)<(?!(?:nowiki|syntaxhighlight))([^ >]*)( [^>\/]*)?> *(?<!')''(?!')((?:(?!(?:<\/\2>|(?<!')''(?!')|(?<!')'''''(?!'))).)*)<\/\2>(?<!')''(?!')((?:(?!(?:(?<!')''(?!')|(?<!')'''''(?!'))).)*)$": r"\1''<\2\3>\4</\2>''\5",
    r"^((?:(?!(?:(?<!')''(?!')|(?<!')'''''(?!'))).)*)(?<!')''(?!') *<(?!(?:nowiki|syntaxhighlight))([^ >]*)( [^>\/]*)?>(?!')((?:(?!<\/\2>|(?<!')''(?!')|(?<!')'''''(?!')).)*)(?<!')''(?!')((?:(?!<\/\2>|(?<!')''(?!')|(?<!')'''''(?!')).)*)<\/\2>((?:(?!(?:(?<!')''(?!')|(?<!')'''''(?!'))).)*)$": r"\1<\2\3>''\4''\5</\2>\6"
}


def fix_italics_misnests(page: str, text: str):
    lines = text.split("\n")
    fixes = []
    for i, line in enumerate(lines):
        new_line = line
        _ = new_line
        while True:
            for find, replace in regexes.items():
                if not regex.search(r"<(?:nowiki|syntaxhighlight)>.*"+find+r".*<\/(?:nowiki|syntaxhighlight)>", line):
                    _ = regex.sub(find, replace, _, flags=regex.MULTILINE)
            if _ != new_line:
                new_line = _
            else:
                break
        if new_line != line:
            fixes.append((i, new_line))
    i = 0
    while i < len(fixes):
        if regex.search(r"\{\{.*\}\}", fixes[i][1]) and not regex.search(r"(?:\{\{(?:(?!(?:'''?|<\/?[^ >]*>)).)*\}\})", fixes[i][1]):
            print("(Filtering) Illegal combination in template invocation")
        elif regex.search(r"(?:<(?!(?:nowiki|syntaxhighlight))([^/][^ >]*)(?: [^>]*)?>.*\[\[(?:(?!<\1>).)*<\/\1>.*\]\]|\[\[.*<(?!(?:nowiki|syntaxhighlight))([^/][^ >]*)(?: [^>]*)?>(?:(?!<\/\2>).)*\]\].*<\/\2>)", fixes[i][1]):
            print("(Filtering) Illegal combination in wikilink")
        else:
            i += 1
            continue
        fixes.pop(i)
        i = 0
    for fix in fixes:
        lines[fix[0]] = fix[1]
    text = "\n".join(lines)
    return text
