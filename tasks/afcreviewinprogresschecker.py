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
        notification_queue[user].append(article)
    except (TypeError, KeyError):
        notification_queue[user] = [article]
    except pywikibot.exceptions.InvalidTitleError:
        print("Bad notification request (invalid title error): "+str(article))
        log_error("Bad notification request (invalid title error): {}".format((user, str(article))), 2)


def check_notified(user: str):
    connection = toolforge.toolsdb("s56602__afc_notifications_p")
    with connection.cursor() as cursor:
        cursor.execute("SELECT time FROM long_reviews WHERE user = %(username)s;", {"username": user})
        time = cursor.fetchone()
        connection.close()
        print("Check_notified (query response):", str(time))
        if time is None:  # It's not there if its None
            return False
        # Change back to 23 | 25 later
        if datetime.datetime.utcnow().replace(tzinfo=None)-datetime.timedelta(hours=17) > time[0] > datetime.datetime.utcnow().replace(tzinfo=None)-datetime.timedelta(hours=31):  # A bit of leeway, but not much.
            return True
        else:
            return False


def check_pending_afc_submissions():
    for draft in drafts:
        for template in mwparserfromhell.parse(draft.text).filter_templates():
            if template.name.matches("bots") and (template.get("deny").value == "TenshiBot" or template.get("deny").value == "all"):
                break  # Yes, pywikibot does have exclusion compliance by default, but that may not apply to the reviewer's talk page who has left a {{bots|deny=TenshiBot}} on the draft.
            if (template.name.matches("AfC submission") or template.name.matches("AFC submission")) and template.get(1).value == "r":
                reviewer, timestamp = template.get("reviewer").value, mediawikitimestamp_to_datetime(str(template.get("reviewts").value))
                #print(draft.title(), (reviewer, timestamp))
                if (datetime.datetime.utcnow()-datetime.timedelta(hours=72)) > timestamp and check_notified(reviewer):
                    print("{}'s review has been ongoing for more than 72 hours and {} has been notified, returning it to the queue.".format(draft.title().strip(), reviewer))
                    draft.text = draft.text.replace(str(template), str(template).replace("r", "", 1))
                    draft.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 2|Bot trial]]: Mark [[Wikipedia:Articles for creation|Articles for Creation]] submissions which are marked ongoing review for over 72 hours as pending.", minor=False, bot=True)
                elif (datetime.datetime.utcnow()-datetime.timedelta(hours=48)) > timestamp:
                    print("{} has been reviewed for longer than 48 hours, notifying {}".format(draft.title(), reviewer))
                    add_to_notification_queue(reviewer, draft)


def notify_reviewers():
    for reviewer in notification_queue.keys():
        reviewer_talk_page = get_talk_page(reviewer)
        for draft in notification_queue[reviewer]:
            reviewer_talk_page.text += "\n{{subst:User:TenshiBot/AfC review notification|"+draft.title()+"|"+draft.title(with_ns=False)+"}}"
        try:
            reviewer_talk_page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 2|Notification]]: Your Articles for Creation review(s) has been marked as ongoing for over forty-eight hours.", minor=False, bot=True)
        except pywikibot.exceptions.OtherPageSaveError:
            print("Failed to notify {}".format(reviewer))
        else:
            print("Notified {} about their ongoing review(s)".format(reviewer))
        finally:
            connection = toolforge.toolsdb("s56602__afc_notifications_p")
            with connection.cursor() as cursor:
                cursor.execute("SELECT time FROM long_reviews WHERE user = %(username)s;", {"username": reviewer})
                time = cursor.fetchone()
                print("Notify_reviewers (query response):", str(time))
                if time is None:
                    print("Inserting new data for {}".format(reviewer))
                    cursor.execute("INSERT INTO long_reviews(user, time) VALUES(%(username)s, %(time)s);", {"username": reviewer, "time": datetime.datetime.utcnow().isoformat()})
                else:
                    print("Updating data for {}".format(reviewer))
                    cursor.execute("UPDATE long_reviews SET time = %(time)s WHERE user = %(username)s;", {"time": datetime.datetime.utcnow().isoformat(), "username": reviewer})
                output = cursor.fetchone()
                print("Notify_reviewers (error check response):", str(output))
                connection.close()


check_pending_afc_submissions()
notify_reviewers()
