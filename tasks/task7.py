import mwparserfromhell
import pywikibot
import regex
site = pywikibot.Site()
talk_pages = [pywikibot.Page(site, match) for match in regex.findall(r"\* \[\[(.*)\]\]", pywikibot.Page(site, "User:WhatamIdoing/Sandbox").text)]
for talk_page in talk_pages:
    parsed_text = mwparserfromhell.parse(talk_page.text)
    for template in parsed_text.filter_templates():
        if template.name.matches("WikiProject Medicine") or template.name.matches("WP Medicine"):
            template.add("importance", "low")
            template.add("society", "yes")
            print("{}: Parameter added".format(talk_page.title()))
            talk_page.text = parsed_text
            break
    else:
        continue
    if pywikibot.Page(site, talk_page.title()).text == talk_page.text:
        continue
    talk_page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 7|Task 7]]: WikiProject Medicine tagging.", minor=False)
