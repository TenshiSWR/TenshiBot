import pywikibot
import regex
from tools.misc import log_file, NoChange
site = pywikibot.Site()


def fix_multiline_misnests(page: str, text: str) -> tuple:
    text = regex.sub(r"(<\/?)(?:[Ss]trike)>", r"\1s>", text)
    lines = text.split("\n")
    stop = False
    misnests = {"<s>": [], "</s>": []}
    for i, line in enumerate(lines):
        s = len(regex.findall(r"<[Ss]>", line))-len(regex.findall(r"<nowiki>.*<[Ss]>.*<\/nowiki>", line))
        closing_s = len(regex.findall(r"<\/[Ss]>", line))-len(regex.findall(r"<nowiki>.*<\/[Ss]>.*<\/nowiki>", line))
        if s > closing_s:
            misnests["<s>"].append((len(regex.findall(r"[\*#:]*", line)[0]), i))
        if s < closing_s:
            misnests["</s>"].append((len(regex.findall(r"[\*#:]*", line)[0]), i))
    # This whole segment is a big sprawling mess and needs to be cut down and simplified.
    print("Misnests: "+str(misnests))
    if len(misnests["<s>"]) < 1 or len(misnests["</s>"]) < 1:
        print("Skipping {}, something is wrong with the amount of <s> tags".format(page))
        print("<s>: {}, </s>: {}".format(misnests["<s>"], misnests["</s>"]))
        log_file("Skipped [[{}]], something is wrong with the amount of <s> tags".format(page), "skips.txt")
        return text, "6"
    i = 0
    while i < len(misnests["</s>"]):
        if misnests["</s>"][i][1] < misnests["<s>"][0][1]:
            #print("(Filtering 1) Removed {}".format(misnests["</s>"][0]))
            misnests["</s>"].pop(i)
            i = 0
        else:
            i += 1
    if len(misnests["<s>"]) == len(misnests["</s>"]):
        i = 0
        while i < len(misnests["</s>"]):
            if misnests["</s>"][i][1] < misnests["<s>"][i][1]:
                #print("(Filtering 2) Removed {}".format(misnests["</s>"][0]))
                misnests["</s>"].pop(i)
                i = 0
            else:
                i += 1
    i = 0
    while i < len(misnests["<s>"]):
        no_more = False
        for x in range(len(misnests["</s>"])):
            try:
                if misnests["<s>"][i+1][1] < misnests["</s>"][x][1]:
                    #print("(Filtering 3) Removed {}".format(misnests["<s>"][x]))
                    misnests["<s>"].pop(i)
                else:
                    i += 1
            except IndexError:
                no_more = True
                break
        if no_more or not misnests["</s>"]:
            break
    if len(misnests["<s>"]) != len(misnests["</s>"]):
        print("Skipping {}, something is wrong with the amount of <s> tags (post filtering)".format(page))
        log_file("Skipped [[{}]], something is wrong with the amount of <s> tags (post filtering)".format(page), "skips.txt")
        stop = True
    print("(Post filtering) <s>: {}, </s>: {}".format(misnests["<s>"], misnests["</s>"]))
    #for misnest in misnests["<s>"]:
    #    print("<s> ({})".format(misnest[1])+str(lines[misnest[1]]))
    #for misnest in misnests["</s>"]:
    #    print("</s> ({})".format(misnest[1])+str(lines[misnest[1]]))
    if stop:
        return text, "6"
    fixes = []
    for i in range(len(misnests["<s>"])):
        if regex.search(r"==+.*=*", lines[misnests["<s>"][i][1]]):
            fixes.append((misnests["<s>"][i][1], regex.sub(r"(==+ *)(?:<s>)?([^<]+)(?:<\/s>)?( ==+)", r"\1<s>\2</s>\3", lines[misnests["<s>"][i][1]])))
        else:
            fixes.append((misnests["<s>"][i][1], lines[misnests["<s>"][i][1]]+"</s>"))
        for y in range(misnests["<s>"][i][1]+1, misnests["</s>"][i][1]):
            #print(y)
            if regex.search(r"==+.*=*", lines[y]) and not regex.search(r"<nowiki>.*==+.*=*.*<\/nowiki>", lines[y]):
                fixes.append((y, regex.sub(r"(==+ *)(?:<s>)?([^<]+)(?:<\/s>)?( ==+)", r"\1<s>\2</s>\3", lines[y])))
            else:
                fixes.append((y, regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2</s>", lines[y])))
        if regex.search(r"==+.*=*", lines[misnests["</s>"][i][1]]):
            fixes.append((misnests["</s>"][i][1], regex.sub(r"(==+ *)(?:<s>)?([^<]+)(?:<\/s>)?( ==+)", r"\1<s>\2</s>\3", lines[misnests["</s>"][i][1]])))
        else:
            fixes.append((misnests["</s>"][i][1], regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2", lines[misnests["</s>"][i][1]])))
    # Post-post filtering & cleanup
    # Mainly for the issues in post which can't be filtered till after
    i, z = 0, 0
    while i < len(fixes):
        # 1. Get a list of the tags
        # 2. Get a closing tag
        # 3. Compare it to all opening tags, remove the opening tag and closing tag in the list if they match and go back to step 2 starting over, else go back to step 2 for a new closing tag
        tag, closing_tag = regex.findall(r"<(?:(?!(?:br *>|\!--))[^\/<>])+>", fixes[i][1]), regex.findall(r"</[^<>]+>", fixes[i][1])
        while z < len(closing_tag):
            _ = regex.sub(r"<\/(.*)>", r"\1", closing_tag[z])
            x = 0
            while x < len(tag):
                if regex.search(r"<{}(?: [^>]*)?>".format(_), tag[x]):
                    break
                else:
                    x += 1
                    continue
            else:
                z += 1
                continue
            tag.pop(x), closing_tag.pop(z)
            z = 0
        if len(tag) or len(closing_tag):
            print("(Post-post filtering) Unclosed html tag ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif regex.search(r"<s>(?:(?!<\/s>).)*?<s>", fixes[i][1]) or regex.search(r"<\/s>(?:(?!<s>).)*?<\/s>", fixes[i][1]):
            print("(Post-post filtering) Double markup ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif regex.search(r"(?<!\[\[[^\]]*)]]", fixes[i][1]):
            print("(Post-post filtering) Unclosed wikilink ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif (len(regex.findall(r"\{\{", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\{\{.*<\/nowiki>", fixes[i][1]))) > (len(regex.findall(r"\}\}", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\}\}.*<\/nowiki>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed template ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif (len(regex.findall(r"\{\{", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\{\{.*<\/nowiki>", fixes[i][1]))) < (len(regex.findall(r"\}\}", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\}\}.*<\/nowiki>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed template ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif (len(regex.findall(r"\{\|", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\{\|.*<\/nowiki>", fixes[i][1]))) > (len(regex.findall(r"\|\}", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\|\}.*<\/nowiki>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed table tag ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif (len(regex.findall(r"\{\|", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\{\|.*<\/nowiki>", fixes[i][1]))) < (len(regex.findall(r"\|\}", fixes[i][1]))-len(regex.findall(r"<nowiki>.*\|\}.*<\/nowiki>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed table tag ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif regex.search(r"\{\{(?:(?:block|poem) ?(?:indent|quote)|(?:indent 5|in5))\}\}", fixes[i][1], regex.IGNORECASE):
            print("(Post-post filtering) Block content template or similar ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif regex.search(r"<br *\/?>", fixes[i][1]):
            print("(Post-post filtering) Lone br tag")
        else:
            i += 1
            continue
        for x in range(len(misnests["<s>"])):
            if misnests["<s>"][x][1] <= fixes[i][0] <= misnests["</s>"][x][1]:
                y = 0
                while y < len(fixes):
                    if misnests["<s>"][x][1] <= fixes[y][0] <= misnests["</s>"][x][1]:
                        fixes.pop(y)
                        y = 0
                    else:
                        y += 1
                break
        i = 0
    for fix in fixes:
        lines[fix[0]] = fix[1]
    text = "\n".join(lines)
    text = regex.sub(r"(?<!<nowiki>.*?)<s> *<\/s>(?!<\/nowiki>)", "", text)  # Final sanity check because it cannot remove on its own a single </s>
    #pywikibot.showDiff(pywikibot.Page(site, page).text, text)
    return text, "6"
