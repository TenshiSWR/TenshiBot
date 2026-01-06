import pywikibot
import regex
from tools.summaries import TASK10_SUMMARY

site = pywikibot.Site()

# Below regex is from https://en.wikipedia.org/wiki/Wikipedia:Bots/Requests_for_approval/DannyS712_bot_69
# or https://github.com/DannyS712/bot/blob/master/drn-cleaner.js which is licensed under the GPL 3.0 licence
# You can read the GPL 3.0 licence in ext_dependencies/licences/drn-cleaner.js LICENSE
SUBSTITUTION_REGEX = r"({{DR case status\|(?:reject|resolve(?:d)?|fail(?:ed)?|close(?:d)?)}})\n<!-- \[\[User:DoNotArchiveUntil.*?-->{{User:ClueBot III\/DoNotArchiveUntil\|\d+}}<!--.*?-->"

drn_page = pywikibot.Page(site, "Wikipedia:Dispute resolution noticeboard")
drn_page.text = regex.sub(SUBSTITUTION_REGEX, "\1", drn_page.text)
drn_page.save(summary=TASK10_SUMMARY, minor=False)
