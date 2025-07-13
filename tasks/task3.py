import mwparserfromhell
import pywikibot
site = pywikibot.Site()
talk_pages = [talk_page for talk_page in pywikibot.Category(site, "Unknown-importance Nova Scotia articles").articles()]
for talk_page in talk_pages:
    parsed_text = mwparserfromhell.parse(talk_page.text)
    for template in parsed_text.filter_templates():
        if template.name.matches("WikiProject Canada"):
            template.add("ns-importance", "low")
            print("{}: Parameter added".format(talk_page.title()))
            talk_page.text = parsed_text
            break
    talk_page.save(summary="Mark WikiProject Canada ns-importance parameter as low.", minor=False)
print()
