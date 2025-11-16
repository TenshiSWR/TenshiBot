import mwparserfromhell
import pywikibot
import regex
site = pywikibot.Site()
talk_pages = [pywikibot.Page(site, match) for match in regex.findall(r"\* \[\[(.*)\]\]", pywikibot.Page(site, "User:WhatamIdoing/Sandbox").getOldVersion(1319315316))]
template = "WikiProject Medicine"
redirects = [template]+[redirect.title(with_ns=False) for redirect in pywikibot.Page(site, "Template:"+template).backlinks(filter_redirects=True, namespaces="Template")]
for talk_page in talk_pages:
    parsed_text = mwparserfromhell.parse(talk_page.text)
    for template in parsed_text.filter_templates():
        for redirect in redirects:
            if template.name.matches(redirect):
                template.add("importance", "low")
                template.add("society", "yes")
                print("{}: Parameter added".format(talk_page.title()))
                talk_page.text = parsed_text
                break
        else:
            continue
        break
    else:
        continue
    if pywikibot.Page(site, talk_page.title()).text == talk_page.text:
        continue
    talk_page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 7|Task 7]]: WikiProject Medicine tagging.", minor=False)
