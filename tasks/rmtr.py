import pywikibot
import mwparserfromhell
from tasks.majavahbot.mediawiki import MediawikiApi  # Essentially from majavahbot.api import MediawikiApi
import datetime
from sys import exit
site = pywikibot.Site()
rmtr = pywikibot.Page(site, "Wikipedia:Requested moves/Technical requests")
split_text_by_line = rmtr.text.split("\n")  # Convert the page text into a list of lines

# Find where each section starts
try:
    section_indexes = [split_text_by_line.index("==== Uncontroversial technical requests ===="),
                       split_text_by_line.index("==== Requests to revert undiscussed moves ===="),
                       split_text_by_line.index("==== Contested technical requests ===="),
                       split_text_by_line.index("==== Administrator needed ====")]
except ValueError:
    exit("Section headings not found, check {} for possible problems".format(rmtr.title()))

# Splits each section into its own var using the section indexes
instructions, uncontroversial_requests, undiscussed_moves, contested_requests, administrator_moves = split_text_by_line[0:section_indexes[0]], \
                                                                                                     split_text_by_line[section_indexes[0]:section_indexes[1]], \
                                                                                                     split_text_by_line[section_indexes[1]:section_indexes[2]], \
                                                                                                     split_text_by_line[section_indexes[2]:section_indexes[3]], \
                                                                                                     split_text_by_line[section_indexes[3]:]

actions = {"technical": 0, "RMUM": 0, "contested": 0, "administrator": 0, "moved": 0}
notification_queue = {}


def process_non_contested_requests(section_queue, section_group):
    global administrator_moves
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
        base_page, target_page = pywikibot.Page(site, parsed_request.filter_templates()[0].get(1).value), pywikibot.Page(site, parsed_request.filter_templates()[0].get(2).value)
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
                    if section_group == "Administrator needed": # Administrator needed section does not have whitespace at the end of the section since it's at the end of the page.
                        del section_queue[requests[i][0]:len(section_queue)]
                    else:
                        del section_queue[requests[i][0]:len(section_queue)-1]
                finally:
                    requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                    actions[{"Uncontroversial technical requests":"technical", "Requests to revert undiscussed moves":"RMUM", "Administrator needed":"moved"}[section_group]] += 1
            elif section_group != "Administrator needed":  # Check protections on both pages
                protections = [base_page.protection(), target_page.protection()]
                if ({"move":("sysop", "infinity")} or {"create":("sysop", "infinity")} in protections[0].items()) or ({"move":("sysop", "infinity")} or {"create":("sysop", "infinity")} in protections[1].items()):
                    print("One or both pages mentioned in {} --> {} are either create-protected or move-protected. Moving to Administrator needed section".format(base_page.title(), target_page.title()))
                    try:  # This could probably be refactored into a single common function at some point
                        number_to_update_by = requests[i+1][0]-requests[i][0]
                        administrator_moves += section_queue[requests[i][0]:requests[i+1][0]]
                        del section_queue[requests[i][0]:requests[i+1][0]]
                    except (IndexError, ValueError):
                        administrator_moves += section_queue[requests[i][0]:len(section_queue)-1]
                        del section_queue[requests[i][0]:len(section_queue)-1]
                    finally:
                        requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                        administrator_moves.append("::One or both pages in this request are either create-protected or move-protected. It has been moved from the {} section. ~~~~".format(section_group))
                        actions["moved"] += 1
        except pywikibot.exceptions.NoMoveTargetError:
            pass
        except pywikibot.exceptions.InvalidTitleError:
            print("Bad request (invalid title error): "+str(requests[i][1]))
        i += 1
        continue
    #print(section_queue)
    return section_queue


def process_contested_requests(section_queue):
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
        if (datetime.datetime.now().replace(tzinfo=None)-datetime.timedelta(hours=72)) > last_reply.replace(tzinfo=None):
            print("Removing expired contested request: {} --> {}".format(initial_request.filter_templates()[0].get(1).value, initial_request.filter_templates()[0].get(2).value))
            add_to_notification_queue(initial_request.filter_templates()[0].get("requester").value, (initial_request.filter_templates()[0].get(1).value, initial_request.filter_templates()[0].get(2).value))
            try:
                number_to_update_by = requests[i+1][0]-requests[i][0]
                del section_queue[indexes[0]:indexes[1]]
            except (IndexError, ValueError):  # Exception will always raise at the end of the section
                #print((requests[i][0], "Index/ValueError"), section_queue[requests[i][0]:len(section_queue)-1])
                del section_queue[requests[i][0]:len(section_queue)-1]
            finally:
                requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                actions["contested"] += 1
        i += 1
    #print(section_queue)
    return section_queue


def add_to_notification_queue(requester, articles):
    global notification_queue
    #print("Notification queue:", requester, articles)
    user_talk_page = pywikibot.Page(site, "User talk:{}".format(requester))
    if user_talk_page.isRedirectPage():
        requester = str(user_talk_page.getRedirectTarget().title()).replace("User talk:", "")
    else:
        requester = user_talk_page.title().replace("User talk:", "")
    try:  # The dictionary does not support mwparserfromhell wikicode as a key, even if it is human-readable
        notification_queue[requester].append((str(articles[0]), str(articles[1])))
    except (TypeError, KeyError):
        notification_queue[requester] = [(str(articles[0]), str(articles[1]))]


def notify_requesters():
    #print(notification_queue)
    for requester in notification_queue.keys():
        #print("Requester: {}".format(requester))
        user_talk_page = pywikibot.Page(site, "User talk:{}".format(requester))
        if user_talk_page.isRedirectPage():  # If a user is renamed while their request is being contested.
            user_talk_page = user_talk_page.getRedirectTarget()
        for articles in notification_queue[requester]:
            #print("Article {}: {}".format(requester, articles))
            article_talk_page = pywikibot.Page(site, "{}".format(articles[0])).toggleTalkPage()
            for template in mwparserfromhell.parse(article_talk_page.text).filter_templates():
                if template.name.matches("Requested move/dated"):
                    print("RM started on talk page of {}, not notifying {}".format(articles[0], requester))
                    break
            else:
                user_talk_page.text += "\n{{subst:User:TenshiBot/RMTR contested notification|"+articles[0]+"|"+articles[1]+"}}"
                print("Notification prepared for {} about {}".format(requester, articles[0]))
        try:
            user_talk_page.save(summary="Notification: Your contested technical move request(s) has been removed from [[Wikipedia:Requested moves/Technical requests]].", minor=False)
        except pywikibot.exceptions.OtherPageSaveError:
            print("Failed to notify {}".format(requester))
        else:
            print("Notified {} of their contested request(s) being removed".format(requester))


def reassemble_page():
    return "\n".join(instructions+uncontroversial_requests+undiscussed_moves+contested_requests+administrator_moves)


uncontroversial_requests = process_non_contested_requests(uncontroversial_requests, "Uncontroversial technical requests")
undiscussed_moves = process_non_contested_requests(undiscussed_moves, "Requests to revert undiscussed moves")
contested_requests = process_contested_requests(contested_requests)
administrator_moves = process_non_contested_requests(administrator_moves, "Administrator needed")
if sum([action for action in actions.values()]) > 0:  # Check to see if anything has been done before saving an edit.
    rmtr.text = reassemble_page()
    notify_requesters()
    rmtr.save(summary="[[Wikipedia:Bots/Requests_for_approval/TenshiBot|Bot trial]]: Clerk [[Wikipedia:Requested moves/Technical requests|RM/TR]]. Processed {} requests.".format(sum([action for action in actions.values()])), minor=False)
