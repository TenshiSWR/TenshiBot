import pywikibot
from pywikibot.exceptions import EditConflictError, LockedPageError, OtherPageSaveError
import random
import regex
from tools.misc import log_error

site = pywikibot.Site()
results_search_regex = input("Results search regex: ")
search_regex = input("Search regex: ")
replace_regex = input("Replace regex: ")
summary = input("Edit summary to use: ")
flag = {"yes": True, "y": True, "no": False, "n": False}[input("Use bot flag if available?: ").lower()]
minor = {"yes": True, "y": True, "no": False, "n": False}[input("Mark edits as minor?: ").lower()]

if input("Restrict namespaces?: ").lower() == ("Y".lower() or "Yes".lower()):
    namespaces = [int(namespace) for namespace in input("Namespaces to restrict (demarcate by using ,): ").split(",")]
    results = site.search(r"{}".format(results_search_regex), namespaces=namespaces)
else:
    namespaces = []
    results = site.search(r"{}".format(results_search_regex))

string = "".join([chr(random.randint(65, 90)) for i in range(0, 10)])

print("\nSettings:\n"+
      "Results search regex: {}\n".format(results_search_regex)+
      "Search regex: {}\n".format(search_regex)+
      "Replace regex: {}\n".format(replace_regex)+
      "Edit summary: {}\n".format(summary)+
      "Use bot flag if available?: {}\n".format("Yes" if flag else "No")+
      "Mark edits as minor?: {}\n".format("Yes" if flag else "No")+
      "\n"+
      "To confirm that these settings are correct and start editing, please type {}".format(string))

while True:
    if input() == string:
        break

_ = 0
for page in results:
    _ += 1
    print(page.title(), _)
    page.text, old_text = regex.sub(search_regex, replace_regex, page.text), page.text
    if page.text == old_text:
        continue
    try:
        page.save(summary=summary, bot=flag, minor=minor)
    except (EditConflictError, LockedPageError, OtherPageSaveError):
        log_error("Either edit conflicted on page, the page is protected, or stopped by exclusion compliance, failed to edit [[{}]]".format(page.title()), "?")
