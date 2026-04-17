import pywikibot
from regex import search, sub
from tools.misc import log_error
from tools.summaries import EDIT_FAIL_SUMMARY, TASK11_SUMMARY

site = pywikibot.Site()
player_cats = ["Category:Association football players by club", "Category:Association football players by competition", "Category:Association football players by country", "Category:Association football players by national team", "Category:Association football players by nationality", "Category:Association football players by populated place", "Category:Expatriate association football players", "Category:Women's association football players"]
position_cats = ["Category:Association football defenders", "Category:Association football forwards", "Category:Association football goalkeepers", "Category:Association football midfielders", "Category:Association football wingers", "Category:Men's association football central defenders", "Category:Men's association football full-backs", "Category:Men's association football inside forwards", "Category:Men's association football outside forwards", "Category:Men's association football sweepers", "Category:Men's association football wing halves", "Category:Women's association football defenders", "Category:Women's association football forwards", "Category:Women's association football goalkeepers", "Category:Women's association football midfielders"]
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
        if position_cat in page.text and not search(r"Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position", page.text):
            break
        elif position_cat in page.text and search(r"Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position", page.text):
            page.text = sub(r"\n\[\[Category:(?:[Ww]o)?[Mm]en's association football players not categorized by position\]\]", "", page.text)
            if search(r"Category:.*[Ww]omen's", page.text):
                _ = "Women's"
            elif search(r"Category:.*(?<!o)[Mm]en's", page.text):
                _ = "Men's"
            try:
                #print("Would edit {} (removal)".format(page.title()))
                i += 1
                page.save(summary=TASK11_SUMMARY.format("Removal", _), minor=False)
            except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
                log_error(EDIT_FAIL_SUMMARY.format(page.title()), 11, soft=True)
            break
    else:
        if search(r"Category:.*[Ww]omen's", page.text):
            _ = "Women's"
        elif search(r"Category:.*(?<!o)[Mm]en's", page.text):
            _ = "Men's"
        else:
            continue
        page.text += "\n[[Category:"+_+" association football players not categorized by position]]"
        try:
            #print("Would edit {} (addition)".format(page.title()))
            i += 1
            page.save(summary=TASK11_SUMMARY.format("Addition", _), minor=False)
        except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
            log_error(EDIT_FAIL_SUMMARY.format(page.title()), 11, soft=True)
    if i >= 100:
        break

print("Edits: "+str(i))
