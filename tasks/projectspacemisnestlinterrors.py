from dotenv import load_dotenv
import json
import os
import pywikibot
import regex
import requests
from requests_oauthlib import OAuth1
site = pywikibot.Site()

load_dotenv()
user_agent = json.loads(os.getenv("USER-AGENT"))
oauth_key = json.loads(os.getenv("OAUTH"))
auth = OAuth1(oauth_key[0], oauth_key[1], oauth_key[2], oauth_key[3])
del oauth_key

api_query = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=&list=linterrors&formatversion=2&lntcategories=misnested-tag&lntlimit=500&lntnamespace=4%7C5"
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


#count = {"^(?!.*Archived nominations)(?!.*Featured log).*Featured article candidates.*":0, "^(?!.*\/archive\/).*Featured article review.*":0, "^(?!.*Failed log)(?!.*Featured log).*Featured list candidates.*":0}
lint_list = []
log_pages = {"\/Assessment\/.*\/\d{4}", ".*\/archive\/.*", ".*Archived nominations.*", ".*Failed log.*" ".*Featured log.*", ".*\/Log\/.*", "Peer review\/"}
params = {}


for error in full_list:
    for log_page in log_pages:
        if not regex.search(log_page, error["title"]) and error["params"]["name"] == "s" or "strike":
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

for page in lint_list:
    page = pywikibot.Page(site, page)
    page.text = regex.sub(r"(<\/?)([Ss]trike)>", r"\1s>", page.text)
    lines = page.text.split("\n")
    while True:
        misnests = {"<s>": [], "</s>": []}
        for i, line in enumerate(lines):
            if regex.search(r"(?!.*<\/s>).*<s>.*", line):  # <s> without any </s>
                #print("Found <s>:", line, "({})".format(i))
                misnests["<s>"].append((len(regex.findall(r"[\*#:]*", line)[0]), i))
            if regex.search(r"(?<!<s[^>]*>[^<]*|<code>.*?)(<\/s>)(?![^<]*<s[^>]*>.*?<\/code>)", line):  # </s> without any <s>
                #print("Found </s>:", line, "({})".format(i))
                misnests["</s>"].append((len(regex.findall(r"[\*#:]*", line)[0]), i))
        if misnests["</s>"][0][1] < misnests["<s>"][0][1]:
            misnests["</s>"].pop(0)
        if len(misnests["<s>"]) <= 1:
            break
        try:
            for i in range(len(misnests["<s>"])-1):
                if misnests["<s>"][i+1][1] < misnests["</s>"][i][1]:
                    misnests["<s>"].pop(i)
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            break
    for i in range(len(misnests["<s>"])):
        lines[misnests["<s>"][i][1]] += "</s>"
        for y in range(misnests["<s>"][i][1]+1, misnests["</s>"][i][1]):
            #print(y)
            lines[y] = regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2</s>", lines[y])
        lines[misnests["</s>"][i][1]] = regex.sub(r"^([\*#: ]*)(.*)$", r"\1<s>\2", lines[misnests["</s>"][i][1]])
    page.text = "\n".join(lines)
    page.text = regex.sub("<s><\/s>", "", page.text)  # Final sanity check because it cannot remove on its own a single </s>
    page.save(summary=": Fix misnested tags lints caused by <s>", minor=True)
