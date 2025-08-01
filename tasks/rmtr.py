import datetime
import mwparserfromhell
import pywikibot
from sys import exit
from tasks.majavahbot.mediawiki import MediawikiApi  # Essentially from majavahbot.api import MediawikiApi
from tools import get_talk_page
from tools import log_error
from tools import wiki_delinker


class RmtrClerking:
    def __init__(self):
        self.site, rmtr = pywikibot.Site(), None
        self.notified = False
        self.actions = {"technical": 0, "RMUM": 0, "contested": 0, "administrator": 0, "moved": 0}
        self.notification_queue = {}
        tries, complete = 0, False
        while tries < 5:  # Theoretically this shouldn't be constantly edit conflicted on the page, but if it is then it'll try at least try to redo it
            rmtr = self.get_rmtr()
            self.uncontroversial_requests = self.process_non_contested_requests(self.uncontroversial_requests, "Uncontroversial technical requests")
            self.undiscussed_moves = self.process_non_contested_requests(self.undiscussed_moves, "Requests to revert undiscussed moves")
            self.contested_requests = self.process_contested_requests(self.contested_requests)
            self.administrator_moves = self.process_non_contested_requests(self.administrator_moves, "Administrator needed")
            if sum([action for action in self.actions.values()]) > 0:  # Check to see if anything has been done before saving an edit.
                rmtr.text = self.reassemble_page()
                if not self.notified:
                    self.notify_requesters()
                try:
                    rmtr.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot|Task 1]]: Clerk [[Wikipedia:Requested moves/Technical requests|RM/TR]]. Processed {} requests.".format(sum([action for action in self.actions.values()])), minor=False)
                except pywikibot.exceptions.EditConflictError:
                    print("Edit conflict on {}".format(rmtr.title()))
                    self.actions = {action: 0 for action, value in self.actions.items()}
                else:
                    complete = True
                    break
                finally:
                    tries += 1
                    print("Tried {} times to update {} ({})".format(str(tries), rmtr.title(), datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
            else:  # If no actions were taken, stop here so that it doesn't loop endlessly
                print("Did nothing ({})".format(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
                complete = True
                break
        if tries == 5 and not complete:
            log_error("Tried 5 times to update {} and was not able to do it".format(rmtr.title()), 1)

    def get_rmtr(self):
        rmtr = pywikibot.Page(self.site, "Wikipedia:Requested moves/Technical requests")
        split_text_by_line = rmtr.text.split("\n")  # Convert the page text into a list of lines

        # Find where each section starts
        try:
            section_indexes = [split_text_by_line.index("==== Uncontroversial technical requests ===="),
                               split_text_by_line.index("==== Requests to revert undiscussed moves ===="),
                               split_text_by_line.index("==== Contested technical requests ===="),
                               split_text_by_line.index("==== Administrator needed ====")]
        except ValueError:
            log_error("Section headings not found, check {} for possible problems".format(rmtr.title()), 1)
            exit("Section headings not found, check {} for possible problems".format(rmtr.title()))

        # Splits each section into its own var using the section indexes
        self.instructions, self.uncontroversial_requests, self.undiscussed_moves, self.contested_requests, self.administrator_moves = split_text_by_line[0:section_indexes[0]], \
                                                                                                                                      split_text_by_line[section_indexes[0]:section_indexes[1]], \
                                                                                                                                      split_text_by_line[section_indexes[1]:section_indexes[2]], \
                                                                                                                                      split_text_by_line[section_indexes[2]:section_indexes[3]], \
                                                                                                                                      split_text_by_line[section_indexes[3]:]
        print("Got {}".format(rmtr.title()), "({})".format(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
        return rmtr

    def process_non_contested_requests(self, section_queue: list, section_group: str):
        requests = []
        number_to_update_by = 0
        for i, line in enumerate(section_queue):
            parsed_text = mwparserfromhell.parse(line)
            for template in parsed_text.filter_templates():
                if template.name.matches("RMassist/core"):
                    requests.append((i, line))
        i = 0
        while i <= len(requests)-1:
            parsed_request = mwparserfromhell.parse(requests[i][1])
            base_page, target_page = pywikibot.Page(self.site, wiki_delinker(str(parsed_request.filter_templates()[0].get(1).value))), pywikibot.Page(self.site, wiki_delinker(str(parsed_request.filter_templates()[0].get(2).value)))
            #print(base_page, target_page, (len(requests), i))
            #print("NC Requests: "+str(requests))
            try:
                # A moved page will either have a redirect (normal move) or no text on it (suppressredirect).
                # Prevents accidentally picking up previous moves and removing the request when it hasn't been done.
                if (base_page.moved_target() == target_page) and (base_page.isRedirectPage() or not len(base_page.text)):
                    print(base_page.title()+" has been moved, removing {} request.".format(section_group))
                    try:
                        number_to_update_by = requests[i+1][0]-requests[i][0]
                        #print((requests[i][0], number_to_update_by, requests[i+1][0]), section_queue[requests[i][0]:requests[i+1][0]])
                        del section_queue[requests[i][0]:requests[i+1][0]]
                    except (IndexError, ValueError):  # Exception will always raise at the end of the section
                        #print((requests[i][0], "Index/ValueError"), section_queue[requests[i][0]:len(section_queue)-1])
                        if section_group == "Administrator needed":  # Administrator needed section does not have whitespace at the end of the section since it's at the end of the page.
                            del section_queue[requests[i][0]:len(section_queue)]
                        else:
                            if section_queue[-1] != "":
                                section_queue.append("\n")
                            del section_queue[requests[i][0]:len(section_queue)-1]
                    finally:
                        requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                        self.actions[{"Uncontroversial technical requests":"technical", "Requests to revert undiscussed moves":"RMUM", "Administrator needed":"moved"}[section_group]] += 1
                        i += 1
                        continue
            except pywikibot.exceptions.NoMoveTargetError:
                pass
            try:
                if section_group != "Administrator needed":  # Check protections on both pages
                    protections = [base_page.protection(), target_page.protection()]
                    if any(type.items() == page.items() for page in protections for type in [{"move":("sysop", "infinity")}, {"create":("sysop", "infinity")}]):
                        print("One or both pages mentioned in {} --> {} are either create-protected or move-protected. Moving to Administrator needed section".format(base_page.title(), target_page.title()))
                        print("Protections:", str(protections[0]), str(protections[1]))
                        try:  # This could probably be refactored into a single common function at some point
                            number_to_update_by = requests[i+1][0]-requests[i][0]
                            self.administrator_moves += section_queue[requests[i][0]:requests[i+1][0]]
                            del section_queue[requests[i][0]:requests[i+1][0]]
                        except (IndexError, ValueError):
                            if section_queue[-1] != "":
                                section_queue.append("\n")
                            self.administrator_moves += section_queue[requests[i][0]:len(section_queue)-1]
                            del section_queue[requests[i][0]:len(section_queue)-1]
                        finally:
                            requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                            self.administrator_moves.append("::{{Clerk note bot}} One or both pages in this request are either create-protected or move-protected."+"It has been moved from the {} section. ~~~~".format(section_group))
                            self.actions["moved"] += 1
            except pywikibot.exceptions.InvalidTitleError:
                log_error("Bad request (invalid title error): <nowiki>{}</nowiki>".format(str(requests[i][1])), 1)
            i += 1
            continue
        #print(section_queue)
        return section_queue

    def process_contested_requests(self, section_queue: list):
        requests = []
        number_to_update_by = 0
        for i, line in enumerate(section_queue):
            parsed_text = mwparserfromhell.parse(line)
            for template in parsed_text.filter_templates():
                if template.name.matches("RMassist/core"):
                    requests.append((i, line))
        i = 0
        while i <= len(requests)-1:
            try:
                initial_request, whole_request, indexes = mwparserfromhell.parse(section_queue[requests[i][0]]), "".join(section_queue[requests[i][0]:requests[i+1][0]]), (requests[i][0], requests[i+1][0])
            except IndexError:
                initial_request, whole_request, indexes = mwparserfromhell.parse(section_queue[requests[i][0]]), "".join(section_queue[requests[i][0]:len(section_queue)-1]), (requests[i][0], len(section_queue)-1)
            last_reply = MediawikiApi.get_last_reply(None, whole_request)
            try:
                if (datetime.datetime.utcnow().replace(tzinfo=None)-datetime.timedelta(hours=72)) > last_reply.replace(tzinfo=None):
                    print("Removing expired contested request: {} --> {}".format(initial_request.filter_templates()[0].get(1).value, initial_request.filter_templates()[0].get(2).value))
                    try:
                        self.add_to_notification_queue(initial_request.filter_templates()[0].get("requester").value, (wiki_delinker(str(initial_request.filter_templates()[0].get(1).value)), wiki_delinker(str(initial_request.filter_templates()[0].get(2).value))))
                    except ValueError:
                        print("Cannot notify requester of {} --> {}, requester parameter missing".format(initial_request.filter_templates()[0].get(1).value, initial_request.filter_templates()[0].get(2).value))
                    try:
                        number_to_update_by = requests[i+1][0]-requests[i][0]
                        del section_queue[indexes[0]:indexes[1]]
                    except (IndexError, ValueError):  # Exception will always raise at the end of the section
                        #print((requests[i][0], "Index/ValueError"), section_queue[requests[i][0]:len(section_queue)-1])
                        del section_queue[requests[i][0]:len(section_queue)-1]
                    finally:
                        requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                        self.actions["contested"] += 1
                i += 1
            except AttributeError:
                log_error("Invalid UTC timestamp in signature: <nowiki>{}</nowiki>".format(initial_request), 1)
                i += 1
        #print(section_queue)
        return section_queue

    def add_to_notification_queue(self, requester: str, articles: tuple):
        #print("Notification queue:", requester, articles)
        try:  # The dictionary does not support mwparserfromhell wikicode as a key, even if it is human-readable
            user_talk_page = pywikibot.Page(self.site, "User talk:{}".format(requester))
            if user_talk_page.isRedirectPage():
                requester = str(user_talk_page.getRedirectTarget().title()).replace("User talk:", "")
            else:
                requester = user_talk_page.title().replace("User talk:", "")
            source_article_test, destination_article_test = pywikibot.Page(self.site, str(articles[0])), pywikibot.Page(self.site, str(articles[1]))
            self.notification_queue[requester].append((str(articles[0]), str(articles[1])))
        except (TypeError, KeyError):
            self.notification_queue[requester] = [(str(articles[0]), str(articles[1]))]
        except pywikibot.exceptions.InvalidTitleError:
            log_error("Bad requester (invalid title error): <nowiki>{}</nowiki>".format(str(requester)+" "+str(articles[0])+" --> "+str(articles[1])), 1)

    def notify_requesters(self):
        #print(notification_queue)
        for requester in self.notification_queue.keys():
            #print("Requester: {}".format(requester))
            user_talk_page = get_talk_page(requester)
            for articles in self.notification_queue[requester]:
                #print("Article {}: {}".format(requester, articles))
                try:
                    article_talk_page = pywikibot.Page(self.site, "{}".format(articles[0])).toggleTalkPage()
                except pywikibot.exceptions.InvalidTitleError:
                    print("Notification prepared for {} (Not checked for RM/No permalink)".format(requester))
                    user_talk_page.text += "\n{{subst:User:TenshiBot/RMTR contested notification}}"
                    continue
                for template in mwparserfromhell.parse(article_talk_page.text).filter_templates():
                    if template.name.matches("Requested move/dated"):
                        print("RM started on talk page of {}, not notifying {}".format(articles[0], requester))
                        break
                else:
                    user_talk_page.text += "\n{{subst:User:TenshiBot/RMTR contested notification|"+articles[0]+"|"+articles[1]+"}}"
                    print("Notification prepared for {} about {}".format(requester, articles[0]))
            try:
                user_talk_page.save(summary="[[Wikipedia:Bots/Requests for approval/TenshiBot|Notification]]: Your contested technical move request(s) has been removed from [[Wikipedia:Requested moves/Technical requests]].", minor=False)
            except pywikibot.exceptions.OtherPageSaveError:
                print("Failed to notify {}".format(requester))
            else:
                print("Notified {} of their contested request(s) being removed".format(requester))
        self.notified = True

    def reassemble_page(self):
        return "\n".join(self.instructions+self.uncontroversial_requests+self.undiscussed_moves+self.contested_requests+self.administrator_moves)


RmtrClerking()
