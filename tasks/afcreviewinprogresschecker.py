import pywikibot
import mwparserfromhell
import datetime
from tools import get_talk_page
from tools import log_error
from tools import mediawikitimestamp_to_datetime
import toolforge
site = pywikibot.Site()
drafts = [draft for draft in pywikibot.Category(site, "Pending AfC submissions being reviewed now").articles()]
notification_queue = {}


# I really need to figure out a standardised system for these things.
def add_to_notification_queue(user: str, article):
    global notification_queue
    user_talk_page = pywikibot.Page(site, "User talk:{}".format(user))
    if user_talk_page.isRedirectPage():
        user = str(user_talk_page.getRedirectTarget().title()).replace("User talk:", "")
    else:
        user = user_talk_page.title().replace("User talk:", "")
    try:
        notification_queue[user].append(str(article))
    except (TypeError, KeyError):
        notification_queue[user] = [str(article)]
    except pywikibot.exceptions.InvalidTitleError:
        print("Bad notification request (invalid title error): "+str(article))
        log_error("Bad notification request (invalid title error): {}".format((user, str(article))), 2)


def check_notified(user: str):
    connection = toolforge.toolsdb("s56602__afc_notifications_p")
    with connection.cursor() as cursor:
        cursor.execute("SELECT time FROM long_reviews WHERE user = %(username)s;", {"username": user})
        time = cursor.fetchone()
        connection.close()
        if time is None:  # It's not there if its None
            return False
        time = datetime.datetime.fromisoformat(time)
        if datetime.datetime.utcnow()-datetime.timedelta(hours=23) > time:  # A bit of leeway, but not much.
            return True
        else:
            return False


def check_pending_afc_submissions():
    for draft in drafts:
        for template in mwparserfromhell.parse(draft.text).filter_templates():
            if (template.name.matches("AfC submission") or template.name.matches("AFC submission")) and template.get(1).value == "r":
                reviewer, timestamp = template.get("reviewer").value, mediawikitimestamp_to_datetime(str(template.get("reviewts").value))
                reviewer_talk_page = get_talk_page(reviewer)
                #print(draft.title(), (reviewer, timestamp))
                if (datetime.datetime.utcnow()-datetime.timedelta(hours=72)) > timestamp and check_notified(reviewer):
                        print("{}'s review has been ongoing for more than 72 hours and {} has been notified, returning it to the queue.".format(draft.title().strip(), reviewer))
                        draft.text = draft.text.replace(str(template), str(template).replace("r", "", 1))
                        draft.save(": Mark [[Wikipedia:Articles for Creation|Articles for Creation]] submissions which are marked ongoing review for over 72 hours as pending.")
                elif (datetime.datetime.utcnow()-datetime.timedelta(hours=48)) > timestamp:
                    print("{} has been reviewed for longer than 48 hours, notifying {}".format(draft.title(), reviewer))
                    add_to_notification_queue(reviewer, draft.title())


def notify_reviewers():
    for reviewer in notification_queue.keys():
        reviewer_talk_page = get_talk_page(reviewer)
        for draft in notification_queue[reviewer]:
            reviewer_talk_page.text += "\n{{subst:User:TenshiBot/AfC review notification|"+draft.title()+"|"+draft.title(with_ns=False)+"}}"
        try:
            reviewer_talk_page.save(summary="Notification: Your Articles for Creation review(s) has been marked as ongoing for over forty-eight hours.", minor=False)
        except pywikibot.exceptions.OtherPageSaveError:
            print("Failed to notify {}".format(reviewer))
        else:
            print("Notified {} about their ongoing review(s)".format(reviewer))
        finally:
            connection = toolforge.toolsdb("s56602__afc_notifications_p")
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO long_reviews (user, time) VALUES (%(username), $(time));", {"username": reviewer, "time": datetime.datetime.utcnow().isoformat()})
                connection.close()


check_pending_afc_submissions()
notify_reviewers()
