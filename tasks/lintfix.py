import pywikibot
from regex import escape, search
from tasks.linterrors.bogus_file_options import fix_bogus_file_options
from tasks.linterrors.misnests import fix_misnests
from tasks.linterrors.multi_colon_escape import fix_multi_colon_escape
from tasks.linterrors.multiline_misnests import fix_multiline_misnests
from tasks.linterrors.obsolete_HTML_tags import fix_obsolete_HTML_tags
from tasks.linterrors.self_closed_tags import fix_self_closed_tags
from tasks.linterrors.tidy_font_bug import fix_tidy_font_bug
from tasks.linterrors.wikilinks_in_extlinks import fix_wikilinks_in_extlinks
from tools.misc import get_database, LintfixModuleError, log_error, NoChange
from tools.queries import get_lint_errors
from tools.summaries import EDIT_FAIL_SUMMARY


lint_list = []
ignored_pages = [r"\/Assessment\/.*\/\d{4}", r".*\/Archived nominations\/.*", r".*Deletion sorting.*", r".*\/Failed log\/.*", r".*\/Featured log\/.*", r".*Featured picture candidates\/.*-\d{4}", r".*\/Log\/.*", r"Peer review\/", r"Wn\/"]
#count = {page:0 for page in ignored_pages}
#params = {}
function_to_summary = {
    "fix_bogus_file_options":{"commons":["Commons:Bots/Requests/TenshiBot", "1 (Trial)"], "incubator":["Special:Permalink/7019591#TenshiBot", "1"]},
    "fix_misnests":{"commons":["Commons:Bots/Requests/TenshiBot", "1 (Trial)"], "incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_multi_colon_escape":{},
    "fix_multiline_misnests":{"commons":["Commons:Bots/Requests/TenshiBot", "1 (Trial)"], "incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikipedia:en":["Wikipedia:Bots/Requests for approval/TenshiBot 6", "6"]},
    "fix_obsolete_HTML_tags":{"commons":["Commons:Bots/Requests/TenshiBot", "1 (Trial)"], "incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikisource:sv":["Special:Permalink/631220#Request for bot flag", "1"]},
    "fix_self_closed_tags":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"], "wikisource:sv":["Special:Permalink/631220#Request for bot flag", "1"]},
    "fix_tidy_font_bug":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"]},
    "fix_wikilinks_in_extlinks":{"incubator":["Special:Permalink/7019591#TenshiBot", "1"]}
}
# Lint errors, manual, exclusion compliance
wikis_config = {"wikipedia:en":[{"misnested-tag": [fix_misnests, fix_multiline_misnests]}, True, True],
                "incubator":[{"bogus-image-options": [fix_bogus_file_options], "misnested-tag": [fix_misnests, fix_multiline_misnests], "obsolete-tag": [fix_self_closed_tags, fix_obsolete_HTML_tags]}, True, False],
                "wikisource:sv":[{"obsolete-tag": [fix_self_closed_tags, fix_obsolete_HTML_tags]}, False, False],
                "commons":[{"bogus-image-options": [fix_bogus_file_options], "misnested-tag": [fix_misnests, fix_multiline_misnests], "obsolete-tag": [fix_obsolete_HTML_tags]}, True, False]}
site_name = "commons"
errors_to_fixes = wikis_config[site_name][0]
site = pywikibot.Site(site_name)
MANUAL = wikis_config[site_name][1]
IGNORE_EXCLUSION_COMPLIANCE = wikis_config[site_name][2]
db, cursor = get_database()
cursor.execute("SELECT * from incubator_testwikis_to_avoid;")
incubator_testwikis_to_avoid = cursor.fetchall()
ignored_pages += [escape(x[0]) for x in incubator_testwikis_to_avoid]
ignored_pages = set(ignored_pages)

errors = get_lint_errors("%7C".join(errors_to_fixes.keys()), url=site.base_url(""))
for error in errors:
    try:
        for page in ignored_pages:
            if search(page, error["title"]):
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
    print("Lintfix: {} ({}/{})".format(page, lint_list.index(page)+1, len(lint_list)))
    text = pywikibot.Page(site, page).text
    if site_name == "incubator" and any((True for x in incubator_testwikis_to_avoid if x[0] in page)):
        print("Page is part of testwiki's to avoid ({}).".format([x for x in incubator_testwikis_to_avoid if x[0] in page][0][0]))
        continue
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
            except LintfixModuleError as error:
                log_error(error.args[0]+" ([[{}]])".format(page), function_to_summary[error.args[1]][site_name][1], site_name=site_name, soft=True)
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
        elif q.upper() == "L":
            print(site.base_url("wiki/{}".format(page.title())))
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
    except (pywikibot.exceptions.EditConflictError, pywikibot.exceptions.LockedPageError):
        log_error(EDIT_FAIL_SUMMARY.format(page.title()), "+".join([task[1] for task in tasks]), site_name=site_name, soft=True)
    except pywikibot.exceptions.OtherPageSaveError as error:
        if search(r"wminc-error-wiki-exists", error.args):
            incubator_testwikis_to_avoid.append([search(r"W[a-z]\/[^/]+", page.title()).group()])
            cursor.execute("INSERT INTO incubator_testwikis_to_avoid(testwiki) VALUES(%(testwiki)s);", {"testwiki":search(r"W[a-z]\/[^/]+", page.title()).group()})
            db.commit()
        else:
            log_error(EDIT_FAIL_SUMMARY.format(page.title()), "+".join([task[1] for task in tasks]), site_name=site_name, soft=True)
    except pywikibot.exceptions.TitleblacklistError as error:
        print("TitleblacklistError: {}".format(error))
    del summary, text
