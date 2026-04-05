import pywikibot
from regex import search
from tasks.linterrors.bogus_file_options import fix_bogus_file_options
from tasks.linterrors.misnests import fix_misnests
from tasks.linterrors.multi_colon_escape import fix_multi_colon_escape
from tasks.linterrors.multiline_misnests import fix_multiline_misnests
from tasks.linterrors.obsolete_HTML_tags import fix_obsolete_HTML_tags
from tasks.linterrors.self_closed_tags import fix_self_closed_tags
from tasks.linterrors.tidy_font_bug import fix_tidy_font_bug
from tasks.linterrors.wikilinks_in_extlinks import fix_wikilinks_in_extlinks
from tools.misc import log_error, NoChange
from tools.queries import get_lint_errors
from tools.summaries import EDIT_FAIL_SUMMARY


lint_list = []
log_pages = {r"\/Assessment\/.*\/\d{4}", r".*\/[Aa]rchive\/.*", r".*\/Archived nominations\/.*", r".*Deletion sorting.*", r".*\/Failed log\/.*", r".*\/Featured log\/.*", r".*Featured picture candidates\/.*-\d{4}", r".*\/Log\/.*", r"Peer review\/"}
#count = {page:0 for page in log_pages}
#params = {}
function_to_summary = {
    "fix_bogus_file_options":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"]},
    "fix_misnests":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_multi_colon_escape":{},
    "fix_multiline_misnests":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_obsolete_HTML_tags":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikisource:sv":["Special:Permalink/631220#Request for bot flag", "1"]},
    "fix_self_closed_tags":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikisource:sv":["Special:Permalink/631220#Request for bot flag", "1"]},
    "fix_tidy_font_bug":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"]},
    "fix_wikilinks_in_extlinks":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"]}
}
# Lint errors, manual, exclusion compliance
wikis_config = {"wikipedia:en":[{"misnested-tag": [fix_misnests, fix_multiline_misnests]}, False, True],
                "incubator":[{"obsolete-tag": [fix_self_closed_tags, fix_obsolete_HTML_tags]}, False, False],
                "wikisource:sv":[{"obsolete-tag": [fix_self_closed_tags, fix_obsolete_HTML_tags]}, False, False]}
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

#lint_list = ["Wikipedia:Requests for comment/Biographies of living people/Phase I"]
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
        tags = ["fixed lint errors"]
    else:
        lint_errors = "Fix [[mw:Help:Extension:Linter|Linter]] errors"
        tags = []
    if len(tasks) == 1:
        summary = "[[{}|Task {}]]: {}".format(tasks[0][0], tasks[0][1], lint_errors)
    else:
        summary = "Tasks "+"+".join(["[[{}|{}]]".format(link, task) for link, task in tasks]) + ": {}".format(lint_errors)
    try:
        page.save(summary=summary, minor=True, tags=tags, force=IGNORE_EXCLUSION_COMPLIANCE)
    except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError, pywikibot.exceptions.OtherPageSaveError):
        log_error(EDIT_FAIL_SUMMARY.format(page.title()), "+".join([task[1] for task in tasks]), site_name=site_name, soft=True)
    del summary, text
