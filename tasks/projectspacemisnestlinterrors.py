from dotenv import load_dotenv
import json
import os
import pywikibot
import regex
import requests
from requests_oauthlib import OAuth1
from tools import log_error, log_file
site = pywikibot.Site()

load_dotenv()
user_agent = json.loads(os.getenv("USER-AGENT"))
oauth_key = json.loads(os.getenv("OAUTH"))
auth = OAuth1(oauth_key[0], oauth_key[1], oauth_key[2], oauth_key[3])
del oauth_key

api_query = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntcategories=misnested-tag&lntlimit=500&lntnamespace=1%7C3"
full_list = []

lntfrom = None
while True:
    if lntfrom:
        r = requests.get(api_query+"&lntfrom={}".format(lntfrom), auth=auth, headers=user_agent)
    else:
        r = requests.get(api_query, auth=auth, headers=user_agent)
    decoded = json.loads(r.text)
    full_list += decoded["query"]["linterrors"]
    try:
        lntfrom = decoded["continue"]["lntfrom"]
    except KeyError:
        break


lint_list = []
log_pages = {"\/Assessment\/.*\/\d{4}", ".*\/[Aa]rchive\/.*", ".*\/Archived nominations\/.*", ".*Deletion sorting.*", ".*\/Failed log\/.*", ".*\/Featured log\/.*", ".*Featured picture candidates\/.*-\d{4}", ".*\/Log\/.*", "Peer review\/"}
#count = {page:0 for page in log_pages}
params = {}


for error in full_list:
    try:
        for log_page in log_pages:
            if regex.search(log_page, error["title"]):
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        #pass
        continue
    else:
        if error["params"]["name"] == "s" or error["params"]["name"] == "strike":
            lint_list.append(error["title"])
    """
    for key in count.keys():
        if regex.search(key, error["title"]):
            count[key] += 1
    try:
        params[error["params"]["name"]] += 1
    except KeyError:
        params[error["params"]["name"]] = 1

# Mostly for counting
for key, value in count.items():
    print(key+": "+str(value))

for param, value in params.items():
    print(param+": "+str(value))
"""

lint_list = list(set(lint_list))  # To remove duplicates of any pages
for page in lint_list:
    page = pywikibot.Page(site, page)
    print(page.title()+": ({})".format(lint_list.index(page.title())))
    page.text = regex.sub(r"(<\/?)(?:[Ss]trike)>", r"\1s>", page.text)
    lines = page.text.split("\n")
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
        print("Skipping {}, something is wrong with the amount of <s> tags".format(page.title()))
        print("<s>: {}, </s>: {}".format(misnests["<s>"], misnests["</s>"]))
        log_file("Skipped [[{}]], something is wrong with the amount of <s> tags".format(page.title()), "skips.txt")
        continue
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
        print("Skipping {}, something is wrong with the amount of <s> tags (post filtering)".format(page.title()))
        log_file("Skipped [[{}]], something is wrong with the amount of <s> tags (post filtering)".format(page.title()), "skips.txt")
        stop = True
    print("(Post filtering) <s>: {}, </s>: {}".format(misnests["<s>"], misnests["</s>"]))
    #for misnest in misnests["<s>"]:
    #    print("<s> ({})".format(misnest[1])+str(lines[misnest[1]]))
    #for misnest in misnests["</s>"]:
    #    print("</s> ({})".format(misnest[1])+str(lines[misnest[1]]))
    if stop:
        continue
    fixes = []
    for i in range(len(misnests["<s>"])):
        fixes.append((misnests["<s>"][i][1], lines[misnests["<s>"][i][1]]+"</s>"))
        for y in range(misnests["<s>"][i][1]+1, misnests["</s>"][i][1]):
            #print(y)
            if regex.search(r"==+.*=*", lines[y]) and not regex.search(r"<nowiki>.*==+.*=*.*<\/nowiki>", lines[y]):
                fixes.append((y, regex.sub(r"(==+)(.*[^=])(=*)", r"\1<s>\2</s>\3", lines[y])))
            else:
                fixes.append((y, regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2</s>", lines[y])))
        fixes.append((misnests["</s>"][i][1], regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2", lines[misnests["</s>"][i][1]])))
    # Post-post filtering & cleanup
    # Mainly for the issues in post which can't be filtered till after
    i, z = 0, 0
    while i < len(fixes):
        # 1. Get a list of the tags
        # 2. Get a closing tag
        # 3. Compare it to all opening tags, remove the opening tag and closing tag in the list if they match and go back to step 2 starting over, else go back to step 2 for a new closing tag
        tag, closing_tag = regex.findall(r"<(?:(?!br *>)[^\/<>])+>", fixes[i][1]), regex.findall(r"</[^<>]+>", fixes[i][1])
        while z < len(closing_tag):
            _ = regex.sub(r"<\/(.*)>", r"\1", closing_tag[z])
            x = 0
            while x < len(tag):
                if regex.match(r"<{}(?: [^>]*)?>".format(_), tag[x]):
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
        elif (len(regex.findall(r"<blockquote>", fixes[i][1]))-len(regex.findall(r"<nowiki>.*<blockquote>.*</nowiki>", fixes[i][1]))) > (len(regex.findall(r"<\/blockquote>", fixes[i][1]))-len(regex.findall(r"<\/blockquote>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed blockquote tag ({}): {}".format(fixes[i][0], fixes[i][1]))
        elif (len(regex.findall(r"<blockquote>", fixes[i][1]))-len(regex.findall(r"<nowiki>.*<blockquote>.*</nowiki>", fixes[i][1]))) < (len(regex.findall(r"<\/blockquote>", fixes[i][1]))-len(regex.findall(r"<\/blockquote>", fixes[i][1]))):
            print("(Post-post filtering) Unclosed blockquote tag ({}): {}".format(fixes[i][0], fixes[i][1]))
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
    page.text = "\n".join(lines)
    page.text = regex.sub(r"(?<!<nowiki>.*?)<s> *<\/s>(?!<\/nowiki>)", "", page.text)  # Final sanity check because it cannot remove on its own a single </s>
    if page.text == pywikibot.Page(site, page.title()).text:
        print("Skipping {}, no changes detected".format(page.title()))
        log_file("Skipped [[{}]], no changes detected.".format(page.title()), "skips.txt")
        continue
    #pywikibot.showDiff(pywikibot.Page(site, page.title()).text, page.text)
    try:
        page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 5|Task 5]]: Fix misnested tags lints caused by <s>", minor=True)
    except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
        log_error("Either edit conflicted on page, the page is protected, or stopped by exclusion compliance, failed to edit [[{}]]".format(page.title()), 5)
