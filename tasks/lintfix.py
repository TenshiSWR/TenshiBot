import pywikibot
from regex import search
from tasks.linterrors.bogus_file_options import fix_bogus_file_options
from tasks.linterrors.misnests import fix_misnests
from tasks.linterrors.multiline_misnests import fix_multiline_misnests
from tasks.linterrors.wikilinks_in_extlinks import fix_wikilinks_in_extlinks
from tools.misc import log_error, NoChange
from tools.queries import get_lint_errors


lint_list = []
log_pages = {"\/Assessment\/.*\/\d{4}", ".*\/[Aa]rchive\/.*", ".*\/Archived nominations\/.*", ".*Deletion sorting.*", ".*\/Failed log\/.*", ".*\/Featured log\/.*", ".*Featured picture candidates\/.*-\d{4}", ".*\/Log\/.*", "Peer review\/"}
#count = {page:0 for page in log_pages}
#params = {}
function_to_summary = {
    "fix_bogus_file_options":{"incubator":["I:A#TenshiBot", "1 (Trial)"]},
    "fix_misnests":{"wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_multiline_misnests":{"wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_wikilinks_in_extlinks":{"incubator":["I:A#TenshiBot", "1 (Trial)"]}
}
# Lint errors, manual, exclusion compliance
wikis_config = {"wikipedia:en":[{"misnested-tag": [fix_misnests, fix_multiline_misnests]}, True, True],
                "incubator":[{"bogus-image-options": [fix_bogus_file_options]}, False, False]}
site_name = "incubator"
errors_to_fixes = wikis_config[site_name][0]
site = pywikibot.Site(site_name)
MANUAL = wikis_config[site_name][1]
IGNORE_EXCLUSION_COMPLIANCE = wikis_config[site_name][2]

errors = get_lint_errors("%7C".join(errors_to_fixes.keys()), url=site.base_url(""))
for error in errors:
    try:
        for log_page in log_pages:
            if search(log_page, error["title"]):
                raise KeyboardInterrupt
    except KeyboardInterrupt:
        #pass
        continue
    else:
        #if error["params"]["name"] == "s" or error["params"]["name"] == "strike":
        lint_list.append(error["title"])
    """
    for key in count.keys():
        if search(key, error["title"]):
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

lint_list = list(set(lint_list))  # To remove duplicates of any pages
for page in lint_list:
    print("Lintfix: {} ({})".format(page, lint_list.index(page)))
    text = pywikibot.Page(site, page).text
    changed = False
    tasks = {}
    for key in errors_to_fixes.keys():
        for fix in errors_to_fixes[key]:
            try:
                # Each function will return a tuple, text & task number, else they raise an Exception if they won't.
                # Handling whether the text was changed or not here is easier than writing it again multiple times.
                new_text, task = fix(page, text), function_to_summary[fix.__name__][site_name]
                if new_text != text:
                    changed = True
                    tasks[task[0]] = task[1]
                    text = new_text
                del new_text, task
            except NoChange:
                pass
    if not changed:
        del text
        continue
    page = pywikibot.Page(site, page)
    if MANUAL:
        pywikibot.showDiff(page.text, text)
        q = input("Accept? (Y/N)")
        if q.upper() == "N":
            continue
    page.text = text
    tasks = sorted(tasks.items())
    if site_name == "wikipedia:en":
        lint_errors = "Fix [[Wikipedia:Linter|Linter]] errors"
    else:
        lint_errors = "Fix [[mw:Help:Extension:Linter|Linter]] errors"
    if len(tasks) == 1:
        summary = "[[{}|Task {}]]: {}".format(tasks[0][0], tasks[0][1], lint_errors)
    else:
        summary = "Tasks "+"+".join(["[[{}|{}]]".format(link, task) for link, task in tasks]) + ": {}".format(lint_errors)
    try:
        page.save(summary=summary, minor=True, tags=["fixed lint errors"], force=IGNORE_EXCLUSION_COMPLIANCE)
    except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
        log_error("Either edit conflicted on page, the page is protected, or stopped by exclusion compliance, failed to edit [[{}]]".format(page.title()), "+".join([task[1] for task in tasks]))
    del summary, text
