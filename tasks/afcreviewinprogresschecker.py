import pywikibot
import mwparserfromhell
import datetime
from tasks.majavahbot.mediawiki import MediawikiApi
from tools import get_talk_page
from tools import mediawikitimestamp_to_datetime
site = pywikibot.Site()
drafts = [draft for draft in pywikibot.Category(site, "Pending AfC submissions being reviewed now").articles()]


def check_pending_afc_submissions():
    for draft in drafts:
        for template in mwparserfromhell.parse(draft.text).filter_templates():
            if (template.name.matches("AfC submission") or template.name.matches("AFC submission")) and template.get(1).value == "r":
                reviewer, timestamp = template.get("reviewer").value, mediawikitimestamp_to_datetime(str(template.get("reviewts").value))
                reviewer_talk_page = get_talk_page(reviewer)
                #print(draft.title(), (reviewer, timestamp))
                try:
                    notification_index = reviewer_talk_page.text.split("\n").index("== Your [[Wikipedia:Articles for Creation|Articles for Creation]] review on {} ==".format(draft.title(with_ns=False)))
                    last_reply = MediawikiApi.get_last_reply(reviewer_talk_page.text.split("\n")[notification_index:notification_index+1])
                except ValueError:  # ValueError is from .index() not finding the notification
                    if (datetime.datetime.utcnow()-datetime.timedelta(hours=48)) > timestamp:
                        print("{} has been reviewed for longer than 48 hours, notifying {}".format(draft.title(), reviewer))
                        reviewer_talk_page.text += "\n{{subst:User:TenshiBot/AfC review notification|"+draft.title()+"|"+draft.title(with_ns=False)+"}}"
                        reviewer_talk_page.save(summary="Notification: Your Articles for Creation review has been marked as ongoing for over fourty-eight hours.", minor=False)
                else:
                    if (datetime.datetime.utcnow()-datetime.timedelta(hours=72)) > timestamp and last_reply:
                        print("{}'s review has been ongoing for more than 72 hours and {} has been notified, returning it to the queue.".format(draft.title().strip(), reviewer))
                        draft.text = draft.text.replace(str(template), str(template).replace("r", "", 1))
                        draft.save(": Mark [[Wikipedia:Articles for Creation|Articles for Creation]] submissions which are marked ongoing review over 72 hours as pending.")


check_pending_afc_submissions()
