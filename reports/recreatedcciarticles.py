import datetime
from dotenv import load_dotenv
from json import loads
from os import getenv
import pywikibot
import regex
import requests

site = pywikibot.Site()
load_dotenv()
USER_AGENT = loads(getenv("USER-AGENT"))

# 1. Get all CCIs.
# 2. Get username(s)
# 3. Get articles
# 4. Check if those articles were deleted
# 5. Check if the articles were recreated


# == Year ==
# === CCI ===
# Y-M-D {editor} [[Special:History/{page}|{page}]] | [[Special:Redirect/logid/{id}|{action} (deleted {deleted_date})]]: [Either {{y}} or {{n}} template or blank or other comment]

ccis = {}
recreated_pages = []

cci_list = pywikibot.Page(site, "Template:CCIlist").text
for cci in regex.findall(r"^\{\{CCI-open\|([^|]+?)\|[^|]+?\|", cci_list, flags=regex.M):
    cci_text = pywikibot.Page(site, "Wikipedia:Contributor copyright investigations/{}".format(cci)).text
    if regex.search(r"\{\{user5\|([^}\n]+?)\}\}", cci_text, flags=regex.I):
        username = regex.search(r"\{\{user5\|(?:1=)?([^}\n]+?)\}\}", cci_text, flags=regex.I).group(1)
    elif regex.search(r"^\* \[\[User:([^|]+?)\|\1\]\] \(\[\[User talk:\1\|talk\]\] \|", cci_text, flags=regex.M):
        username = regex.search(r"^\* \[\[User:([^|]+?)\|\1\]\] \(\[\[User talk:\1\|talk\]\] \|", cci_text, flags=regex.M).group(1)
    elif regex.search(r"^\{\{userlinks\|([^}]+?)\}\}", cci_text, flags=regex.I|regex.M):
        username = regex.search(r"^\{\{userlinks\|([^}]+?\}\}", cci_text, flags=regex.I|regex.M)
    else:
        print("{}: No username".format(cci))
        continue
    socks = regex.findall(r"^\[\[User:([^|]+?)\|\1\]\] \(\[\[User talk:\1\|talk\]\] &middot;", cci_text, flags=regex.M)
    #print("Wikipedia:Contributor copyright investigations/{}".format(cci))
    subpages = regex.findall(r"^\* ?\[\[(Wikipedia:Contributor copyright investigations/{}[^\]]+?)\]\]".format(cci), cci_text, flags=regex.M)
    for subpage in subpages:
        subpage_text = pywikibot.Page(site, subpage).text
        socks += regex.findall(r"^\[\[User:([^|]+?)\|\1\]\] \(\[\[User talk:\1\|talk\]\] &middot;", subpage_text, flags=regex.M)
    ccis[cci] = sorted(list(set([username]+socks)))
    print("{}: {}".format(cci, str(ccis[cci])))

S = requests.Session()
S.headers = USER_AGENT
for cci in ccis.keys():
    for username in ccis[cci]:
        print("[{}]: {}".format(cci, username))
        #pages = list(set([x.page().title() for x in pywikibot.User(site, username).logevents(logtype="create", namespace=[0, 3, 118])]))
        namespaces, pages = [0, 3, 118], []
        for namespace in namespaces:
            try:
                _ = loads(S.get("https://xtools.wmcloud.org/api/user/pages/en.wikipedia.org/{}/{}/noredirects/all///?format=json".format(username, namespace)).text)["pages"][0]
            except (IndexError, KeyError):
                continue
            for page in _:
                pages.append(str(page["full_page_title"]).replace("_", " "))
        pages = list(set(pages))
        for page in pages:
            if not pywikibot.Page(site, page).exists():
                continue
            _ = [x.data for x in site.logevents(logtype="delete", page=page)]
            for log in _:  # Don't report for revision deletion
                if log["action"] == "delete" and regex.search(r"(?:Copyright problems|G5|G12|Mass deletion|PDEL)", log["comment"]):  # Too much noise with everything
                    id = log["logid"]
                    action = regex.search(r"(Copyright problems|G5|G12|Mass deletion|PDEL)", log["comment"]).group()
                    deletion_date = log["timestamp"]
                    break
            else:
                continue
            oldest_revision = pywikibot.Page(site, page).oldest_revision
            recreated_pages.append((oldest_revision["timestamp"], oldest_revision["revid"], oldest_revision["user"], cci, page, id, action, deletion_date))
            #print("[[Special:History/{}|{}]]".format(page, page), action)
            print((oldest_revision["timestamp"], oldest_revision["revid"], oldest_revision["user"], cci, page, id, action, deletion_date))

ccis = sorted(ccis.keys())
ccis = {cci:[] for cci in ccis}

timestamps = []
for recreated_page in recreated_pages:
    timestamps.append(recreated_page[0])
timestamps.sort()
timestamps.reverse()
years = []
for timestamp in timestamps:
    for recreated_page in recreated_pages:
        if not recreated_page[0] == timestamp:
            continue
        ccis[recreated_page[3]].append(recreated_page)
        if not recreated_page[0].year in years:
            years.append(recreated_page[0].year)
        break

# Text assembly
report_page = pywikibot.Page(site, "User:TenshiBot/Recreated CCI articles")
comments = {}
for page, comment in regex.findall(r"\[\[Special:History\/([^|]+)[^\n]+\)\]\]: ([^\n]+)\n", report_page.text):
    comments[page] = comment
report_page.text = ""
for year in years:
    report_page.text += "== {} ==\n".format(year)
    for cci, data in ccis.items():
        if not any([True for x in data if x[0].year == year]):
            continue
        report_page.text += "=== [[Wikipedia:Contributor copyright investigations/{}|{}]] ===\n".format(cci, cci)
        for _ in data:
            if _[0].year != year:
                continue
            try:
                comments[_[4]]
            except KeyError:
                report_page.text += "* [[Special:Permalink/{}|{}]] {} [[Special:History/{}|{}]] | [[Special:Redirect/logid/{}|{} (deleted {})]]: \n".format(_[1], _[0].strftime("%Y-%m-%d %H:%M"), _[2], _[4], _[4], _[5], _[6], _[7][0:10]+" "+_[7][11:16])
            else:
                report_page.text += "* [[Special:Permalink/{}|{}]] {} [[Special:History/{}|{}]] | [[Special:Redirect/logid/{}|{} (deleted {})]]: {}\n".format(_[1], _[0].strftime("%Y-%m-%d %H:%M"), _[2], _[4], _[4], _[5], _[6], _[7][0:10]+" "+_[7][11:16], comments[_[4]])
        report_page.text += "\n"

report_page.save(summary='[[User:TenshiBot#Tasks|Task 4U]]: Update report "Recreated CCI articles"', minor=False)

print()