import pywikibot
from regex import search
from tasks.linterrors.misnests import fix_misnests
from tasks.linterrors.multiline_misnests import fix_multiline_misnests
from tools.misc import log_error, NoChange
from tools.queries import get_lint_errors


lint_list = []
log_pages = {"\/Assessment\/.*\/\d{4}", ".*\/[Aa]rchive\/.*", ".*\/Archived nominations\/.*", ".*Deletion sorting.*", ".*\/Failed log\/.*", ".*\/Featured log\/.*", ".*Featured picture candidates\/.*-\d{4}", ".*\/Log\/.*", "Peer review\/"}
#count = {page:0 for page in log_pages}
#params = {}
errors_to_fixes = {"misnested-tag": [fix_misnests, fix_multiline_misnests]}
site = pywikibot.Site()
BRFA_PREFIX = "Wikipedia:Bots/Requests for approval/TenshiBot "  # Always will be numbered because Task 1 isn't a lint error fixing task
MANUAL = True
IGNORE_EXCLUSION_COMPLIANCE = True

errors = get_lint_errors("%7C".join(errors_to_fixes.keys()))
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
    task_numbers = []
    for key in errors_to_fixes.keys():
        for fix in errors_to_fixes[key]:
            try:
                # Each function will return a tuple, text & task number, else they raise an Exception if they won't.
                # Handling whether the text was changed or not here is easier than writing it again multiple times.
                new_text, task_number = fix(page, text)
                if new_text != text:
                    changed = True
                    task_numbers.append(str(task_number))
                    text = new_text
                del new_text, task_number
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
    task_numbers = sorted(set(task_numbers))  # Making it into a set removes the possibility of duplicate tasks listed in the summary if two or more functions are used in the same BRFA
    if len(task_numbers) == 1:
        summary = "[[{}{}|Task {}]]: Fix [[Wikipedia:Linter|Linter]] errors".format(BRFA_PREFIX, task_numbers[0].replace(" (Trial)", ""), task_numbers[0])
    else:
        summary = "Tasks "+"+".join(["[[{}{}|{}]]".format(BRFA_PREFIX, task_number.replace(" (Trial)", ""), task_number) for task_number in task_numbers])+": Fix [[Wikipedia:Linter|Linter]] errors"
    try:
        page.save(summary=summary, minor=True, tags=["fixed lint errors"], force=IGNORE_EXCLUSION_COMPLIANCE)
    except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
        log_error("Either edit conflicted on page, the page is protected, or stopped by exclusion compliance, failed to edit [[{}]]".format(page.title()), "+".join(task_numbers))
    del summary, text
