from pwiki.mquery import MQuery
from pwiki.wiki import Wiki
import pywikibot
import re
mquery, wiki = MQuery(), Wiki()
working_list = wiki.what_transcludes_here("Template:Infobox album")
text = mquery.page_text(wiki, working_list)
index = 0

while index < len(working_list):
    working_text = text[working_list[index]]
    result = re.search("Category: *.*(Albums|albums)", working_text)
    if not result:  # 1. Has to have "albums" in it
        del text[working_list[index]]
        working_list.pop(index)
        continue
    result = re.search("==* *.*(Track listing|Track list|Tracklist|Disc 1|Disc 2|CD track listing|DVD track listing|Set listing|Tracks|Tracklisting)", working_text, re.I)
    if result:
        del text[working_list[index]]
        working_list.pop(index)
        continue
    # 2. Must not have track listing
    print("{} does not have a track listing".format(working_list[index]))
    index += 1
    continue

site = pywikibot.Site()
page = pywikibot.Page(site, "User:TenshiBot/Album articles without track listings")
page.text = "Album articles without track listings:"
if len(working_list) > 0:
    for article in sorted(working_list):
        page.text += "\n* [[{}]]".format(article)
else:
    page.text += "\nNo results found."
page.save(summary="Updating report", minor=False)

