import datetime
import mwparserfromhell
import pywikibot
from tools import get_talk_page
from tools import log_error
from tools import mediawikitimestamp_to_datetime
import toolforge


class AfcReviews:
    def __init__(self):
        self.site = pywikibot.Site()
        self.drafts = [draft for draft in pywikibot.Category(self.site, "Pending AfC submissions being reviewed now").articles()]
        print("Initial amount of submissions in category: {}".format(len(self.drafts)))
        self.notification_queue = {}
        self.connection = toolforge.toolsdb("s56602__afc_notifications_p")
        self.cursor = self.connection.cursor()
        self.check_pending_afc_submissions()
        self.notify_reviewers()
        self.connection.close()

    # I really need to figure out a standardised system for these things.
    def add_to_notification_queue(self, user: str, article):
        user_talk_page = pywikibot.Page(self.site, "User talk:{}".format(user))
        if user_talk_page.isRedirectPage():
            user = str(user_talk_page.getRedirectTarget().title()).replace("User talk:", "")
        else:
            user = user_talk_page.title().replace("User talk:", "")
        try:
            self.notification_queue[user].append(article)
        except (TypeError, KeyError):
            self.notification_queue[user] = [article]
        except pywikibot.exceptions.InvalidTitleError:
            log_error("Bad notification request (invalid title error): {}".format((user, str(article))), 2)

    def check_notified(self, user: str):
        self.cursor.execute("SELECT time FROM long_reviews WHERE user = %(username)s;", {"username": user})
        self.time = self.cursor.fetchone()
        if self.time is None:  # It's not there if its None
            return False
        if datetime.datetime.utcnow().replace(tzinfo=None)-datetime.timedelta(hours=23) > self.time[0] > datetime.datetime.utcnow().replace(tzinfo=None)-datetime.timedelta(hours=25):  # A bit of leeway, but not much.
            return True
        else:
            return False

    def check_pending_afc_submissions(self):
        for draft in self.drafts:
            try:
                for template in mwparserfromhell.parse(draft.text).filter_templates():
                    if template.name.matches("bots") and (template.get("deny").value == "TenshiBot" or template.get("deny").value == "all"):
                        raise KeyboardInterrupt  # Yes, pywikibot does have exclusion compliance by default, but that may not apply to the reviewer's talk page who has left a {{bots|deny=TenshiBot}} on the draft.
            except KeyboardInterrupt:
                break
            for template in mwparserfromhell.parse(draft.text).filter_templates():
                if (template.name.matches("AfC submission") or template.name.matches("AFC submission")) and template.get(1).value == "r":
                    try:
                        reviewer, timestamp = template.get("reviewer").value, mediawikitimestamp_to_datetime(str(template.get("reviewts").value))
                        #print(draft.title(), (reviewer, timestamp))
                    except ValueError:  # Would occur if reviewer or reviewts parameter is missing somehow
                        try:
                            timestamp = mediawikitimestamp_to_datetime(str(template.get("reviewts").value))
                        except ValueError:  # Definitely the reviewts or both parameter, needs human intervention
                            print("Missing parameter reviewts, cannot evaluate: [[{}]]".format(draft.title()))
                            continue
                        else:
                            if (datetime.datetime.utcnow()-datetime.timedelta(hours=72)) > timestamp:
                                print("{}'s review has been ongoing for more than 72 hours, unable to notify reviewer, returning it to the queue.".format(draft.title().strip()))
                                draft.text = draft.text.replace(str(template), str(template).replace("r", "", 1))
                                draft.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 2|Task 2]]: Mark [[Wikipedia:Articles for creation|Articles for Creation]] submissions which are marked ongoing review for over 72 hours as pending.", minor=False)
                    else:
                        if (datetime.datetime.utcnow()-datetime.timedelta(hours=72)) > timestamp and self.check_notified(reviewer):
                            print("{}'s review has been ongoing for more than 72 hours and {} has been notified, returning it to the queue.".format(draft.title().strip(), reviewer))
                            draft.text = draft.text.replace(str(template), str(template).replace("r", "", 1))
                            draft.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 2|Task 2]]: Mark [[Wikipedia:Articles for creation|Articles for Creation]] submissions which are marked ongoing review for over 72 hours as pending.", minor=False)
                        elif (datetime.datetime.utcnow()-datetime.timedelta(hours=48)) > timestamp:
                            print("{} has been reviewed for longer than 48 hours, notifying {}".format(draft.title(), reviewer))
                            self.add_to_notification_queue(reviewer, draft)

    def notify_reviewers(self):
        for reviewer in self.notification_queue.keys():
            reviewer_talk_page = get_talk_page(reviewer)
            for draft in self.notification_queue[reviewer]:
                reviewer_talk_page.text += "\n{{subst:User:TenshiBot/AfC review notification|"+draft.title()+"|"+draft.title(with_ns=False)+"}}"
            try:
                reviewer_talk_page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot 2|Notification]]: Your Articles for Creation review(s) has been marked as ongoing for over forty-eight hours.", minor=False)
            except pywikibot.exceptions.OtherPageSaveError:
                print("Failed to notify {}".format(reviewer))
            else:
                print("Notified {} about their ongoing review(s)".format(reviewer))
            finally:
                self.cursor.execute("SELECT time FROM long_reviews WHERE user = %(username)s;", {"username": reviewer})
                self.time = self.cursor.fetchone()
                print("Notify_reviewers (query response):", str(self.time))
                if self.time is None:
                    print("Inserting new data for {}".format(reviewer))
                    self.cursor.execute("INSERT INTO long_reviews(user, time) VALUES(%(username)s, %(time)s);", {"username": reviewer, "time": datetime.datetime.utcnow()})
                else:
                    print("Updating data for {}".format(reviewer))
                    self.cursor.execute("UPDATE long_reviews SET time = %(time)s WHERE user = %(username)s;", {"time": datetime.datetime.utcnow(), "username": reviewer})
                self.connection.commit()


AfcReviews()
