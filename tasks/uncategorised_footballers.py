import pywikibot
import regex
from tools.misc import log_error
from tools.summaries import EDIT_FAIL_SUMMARY, TASK11_SUMMARY

site = pywikibot.Site()
player_cats = ["Category:Association football players by club", "Category:Association football players by competition", "Category:Association football players by country", "Category:Association football players by national team", "Category:Association football players by nationality", "Category:Association football players by populated place", "Category:Expatriate association football players", "Category:Men's association football players not categorized by position", "Category:Women's association football players", "Category:Women's association football players not categorized by position"]
position_cats = ["Category:Men's association football central defenders", "Category:Men's association football defenders", "Category:Men's association football forwards", "Category:Men's association football full-backs", "Category:Men's association football goalkeepers", "Category:Men's association football inside forwards", "Category:Men's association football midfielders", "Category:Men's association football outside forwards", "Category:Men's association football sweepers", "Category:Men's association football utility players", "Category:Men's association football wing halves", "Category:Men's association football wingers", "Category:Women's association football central defenders", "Category:Women's association football defenders", "Category:Women's association football forwards", "Category:Women's association football full-backs", "Category:Women's association football goalkeepers", "Category:Women's association football midfielders", "Category:Women's association football outside forwards", "Category:Women's association football sweepers", "Category:Women's association football wingers", "Category:Women's association football utility players"]
excluded_cats = ["Category:Association football player non-biographical articles", "Category:Association football trophies and awards"]


def full_category_members(categories: list):
    pages = []
    while True:
        for item in pywikibot.Category(site, categories[0]).members():
            #print(item)
            if "Category:" in item.title():
                categories.append(item.title())
            else:
                pages.append(item.title())
        #print(categories[0]+" ("+str(len(categories))+", "+str(len(pages))+")")
        del categories[0]
        if not len(categories):
            break
    return sorted(list(set(pages)))


pages = full_category_members(player_cats)

print("Pages: "+str(len(pages)))

excluded_pages = full_category_members(excluded_cats)

print("Excluded pages: "+str(len(excluded_pages)))

i = 0
for page in pages:
    if page in excluded_pages or "List of" in page:
        continue
    page = pywikibot.Page(site, page)
    for position_cat in position_cats:
        if position_cat in page.text and not regex.search(r"Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position", page.text):
            break
        elif position_cat in page.text and regex.search(r"Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position", page.text):
            page.text = regex.sub(r"\n\[\[Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position\]\]", "", page.text)
            if regex.search(r"Category:.*[Ww]omen's", page.text):
                _ = "Women's"
            elif regex.search(r"Category:.*(?<!o)[Mm]en's", page.text):
                _ = "Men's"
            try:
                i += 1
                page.save(summary=TASK11_SUMMARY.format("Removal", _), minor=False)
            except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
                log_error(EDIT_FAIL_SUMMARY.format(page.title()), 11, soft=True)
            break
    else:
        if not regex.search(r"(?:is|was) an? .*?(?:footballer|(?:football|soccer) player).*?\.", page.text):
            continue
        elif regex.search(r"\[\[Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position\]\]", page.text):
            continue
        if regex.search(r"Category:.*[Ww]omen's", page.text):
            _ = "Women's"
        elif regex.search(r"Category:.*(?<!o)[Mm]en's", page.text):
            _ = "Men's"
        else:
            continue
        if regex.search(r"{{.*?-stub}}", page.text):
            page.text = regex.sub(r"(\[\[Category:[^]]*?\]\])([^[]*?)(\{\{.*?-stub\}\})", r"\1\n[[Category:"+_+" association football players not categorized by position]]\2\3", page.text, flags=regex.DOTALL)
        else:
            page.text += "\n[[Category:"+_+" association football players not categorized by position]]"
        try:
            i += 1
            page.save(summary=TASK11_SUMMARY.format("Addition", _), minor=False)
        except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
            log_error(EDIT_FAIL_SUMMARY.format(page.title()), 11, soft=True)

print("Edits: "+str(i))
