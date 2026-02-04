import regex

regexes = {
    #r"(?<!(?:\[\[|\|.*))(?:([A-z]+:[^|]*)(?:\|thumb|\|\d{1,4}px|\|left|\|right)(.*))(?!\]\])": r"\1\2",
    r"\| *(\|.*)": r"\1",
    r"\|((?:thumb(?:nail)?|\d{1,4}px|left|right|center)+)(?=.*\|\1\|)": r"",
    r"\|((?:link=[^|]+)+)(?=.*\|\1)": r"",
    r"\|((?:link=\|)+)(?=.*\|\1)": r""
}


def fix_bogus_file_options(page: str, text: str) -> str:
    lines = text.split("\n")
    fixes = []
    for i, line in enumerate(lines):
        new_line = line
        files = regex.findall(r"\[\[[A-z]+:(?:(?!\[\[[^\[]*(?!\]\])).)+\]\]", new_line)
        for file in files:
            new_file_wikitext = file
            for find, replace in regexes.items():
                while True:
                    if new_file_wikitext != regex.sub(find, replace, new_file_wikitext):
                        new_file_wikitext = regex.sub(find, replace, new_file_wikitext)
                    else:
                        break
            new_line = regex.sub(regex.escape(file), new_file_wikitext.replace("\\", "\\\\"), new_line)
        while True:
            if regex.search(r"(?:[^|]+)(?:\|thumb(?:nail)?|\|\d{1,4}px|\|left|\|right|center)(?:\|.*)", new_line) and not regex.search(r"(?:\[\[|\{\{).*"+r"(?:[^|]+)(?:\|thumb(?:nail)?|\|\d{1,4}px|\|left|\|right|center)(?:\|.*)"+r".*(?:\]\]|\}\})", new_line):
                new_line = regex.sub(r"(?:([^|]+))(?:\|thumb(?:nail)?|\|\d{1,4}px|\|left|\|right|center)(\|.*)", r"\1\2", new_line)
            else:
                break
        if new_line != line:
            fixes.append((i, new_line))
    i = 0
    while i < len(fixes):
        if (len(regex.findall(r"\[\[", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\[\[.*<\/nowiki>", fixes[i][1]))) > (len(regex.findall(r"\]\]", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\]\].*<\/nowiki>", fixes[i][1]))):
            print("(Filtering) Unclosed file markup")
        elif regex.search(r"^ *\|", fixes[i][1]):
            print("(Filtering) Table or template territory")
        else:
            i += 1
            continue
        fixes.pop(i)
        i = 0
    for fix in fixes:
        lines[fix[0]] = fix[1]
    text = "\n".join(lines)
    return text
