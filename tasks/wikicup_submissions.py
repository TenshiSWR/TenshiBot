import pywikibot
import regex
from tools.summaries import TASK8_CREATE_SUMMARY, TASK8_RESET_SUMMARY

site = pywikibot.Site()

wikicup_round = 1
usernames = regex.findall(r"\# .*User: *(?! *Your username)([^|]*)(?:\||]])", pywikibot.Page(site, "Wikipedia:WikiCup/2026 signups").text)
usernames = [username[0].upper()+username[1:] for username in usernames if pywikibot.User(site, username).isRegistered()]
pages = ["Wikipedia:WikiCup/History/2026/Submissions/"+username for username in usernames]

for page in pages:
    page = pywikibot.Page(site, page)
    summary = TASK8_CREATE_SUMMARY
    if page.exists() and int(regex.search(r"== *Round (-?\d) *==", page.text).group(1)) == wikicup_round:
        continue
    elif page.exists():
        summary = TASK8_RESET_SUMMARY.format(str(wikicup_round))
    page.text = "{{subst:User:TenshiBot/WikiCup setup template|"+str(wikicup_round)+"}}"
    page.save(summary=summary, minor=False)
