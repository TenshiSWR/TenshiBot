import datetime
import mwparserfromhell
import pywikibot
from pwiki.mquery import MQuery
from pwiki.ns import NS
from pwiki.wiki import Wiki
import re
from tools import mediawikitimestamp_to_datetime
mquery, wiki = MQuery(), Wiki()
transclusions = wiki.what_transcludes_here("Template:Copyvio", ns=NS.MAIN)

# 1. Check if template has timestamp, if not go to 4
# 2. Check relevant subpage if the article is listed, if not go to 4
# 3. Check if the subpage is transcluded onto the main Copyright problems page
# 4. Check all subpages for if the article is listed
# 5. Log problems to a userspace page separating listings which do not comply with 2-4 respectively


copyright_problems = wiki.page_text("Wikipedia:Copyright problems")
subpages = mquery.page_text(wiki, re.findall("Wikipedia:Copyright problems\/\d{4}\s[A-z]*\s\d*", copyright_problems))
unlisted_copyright_problems, unlisted_subpages = [], []


def check_subpages():
    global unlisted_subpages
    try:
        subpages[subpage_name]
    except KeyError:
        if time <= (datetime.datetime.utcnow()-datetime.timedelta(days=7)):
            unlisted_subpages.append((subpage_name, page))
            print("{} (from checking {}) is not listed on Copyright problems".format(subpage_name, page))


for page in transclusions:
    page_regex = re.compile(r'<span class="anchor" id="{}"><\/span>\[\[{}\]\]'.format(re.escape(page), re.escape(page)))
    parsed_text = mwparserfromhell.parse(wiki.page_text(page))
    result, subpage, time = None, None, None
    for template in parsed_text.filter_templates():
        if template.name.matches("Copyvio"):
            try:
                time = mediawikitimestamp_to_datetime(template.get("timestamp").value)
            except ValueError:
                break
            day = str(int(time.strftime("%d")))
            subpage_name = "Wikipedia:Copyright problems/"+time.strftime("%Y %B")+" {}".format(day)
            subpage = wiki.page_text(subpage_name)
            result = page_regex.search(subpage)
            break
    if not time:
        pass
    elif result:
        check_subpages()
        continue
    for text in subpages.values():
        result = page_regex.search(text)
        if result:
            break
    else:
        unlisted_copyright_problems.append(page)
        print("{} is not listed in any listed Copyright problems subpages".format(page))

site = pywikibot.Site()
report_page = pywikibot.Page(site, "User:TenshiBot/Unlisted copyright problems")

report_page.text = "\n".join(["<div style=display:inline-grid>", '{| class="wikitable"', "|+ <u>Unlisted articles with copyright problems</u>\n"])
for page in sorted(unlisted_copyright_problems):
    report_page.text += "\n".join(["|-", "|", "* [[{}]]".format(page)+"\n"])
report_page.text += "\n".join(["|}", "</div>\n"])

report_page.text += "\n".join(["<div style=display:inline-grid>", '{| class="wikitable"', "|+ <u>Unlisted subpages with tagged copyright problems</u>\n"])
for subpage, page in unlisted_subpages:
    report_page.text += "\n".join(["|-", "|", "* [[{}]] (from checking [[{}]])".format(subpage, page)+"\n"])
report_page.text += "\n".join(["|}", "</div>"])

report_page.save(summary='[[User:TenshiBot#Tasks|Task 2U]]: Update report "Unlisted copyright problems"', minor=False)



