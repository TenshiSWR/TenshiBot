import pywikibot
import mwparserfromhell
from tasks.majavahbot.mediawiki import MediawikiApi  # Essentially from majavahbot.api import MediawikiApi
import datetime
site = pywikibot.Site()
rmtr = pywikibot.Page(site, "User:TenshiBot/RMTRtest")
split_text_by_line = rmtr.text.split("\n")  # Convert the page text into a list of lines

# Find where each section starts
section_indexes = [split_text_by_line.index("==== Uncontroversial technical requests ===="),
                   split_text_by_line.index("==== Requests to revert undiscussed moves ===="),
                   split_text_by_line.index("==== Contested technical requests ===="),
                   split_text_by_line.index("==== Administrator needed ====")]

# Splits each section into its own var using the section indexes
instructions, uncontroversial_requests, undiscussed_moves, contested_requests, administrator_moves = split_text_by_line[0:section_indexes[0]], \
                                                                                                     split_text_by_line[section_indexes[0]:section_indexes[1]], \
                                                                                                     split_text_by_line[section_indexes[1]:section_indexes[2]], \
                                                                                                     split_text_by_line[section_indexes[2]:section_indexes[3]], \
                                                                                                     split_text_by_line[section_indexes[3]:]

actions = {"technical": 0, "RMUM": 0, "contested": 0}


def process_non_contested_requests(section_queue):
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
                print(base_page.title()+" has been moved, removing non-contested request.")
                try:
                    number_to_update_by = requests[i+1][0]-requests[i][0]
                    #print((requests[i][0], number_to_update_by, requests[i+1][0]), section_queue[requests[i][0]:requests[i+1][0]])
                    del section_queue[requests[i][0]:requests[i+1][0]]
                except (IndexError, ValueError):  # Exception will always raise at the end of the section
                    #print((requests[i][0], "Index/ValueError"), section_queue[requests[i][0]:len(section_queue)-1])
                    del section_queue[requests[i][0]:len(section_queue)-1]
                finally:
                    requests = [[x[0]-number_to_update_by, x[1]] for x in requests]
                    if section_queue[0] == "==== Uncontroversial technical requests ====":
                        actions["technical"] += 1
                    else:
                        actions["RMUM"] += 1
        except (pywikibot.exceptions.NoMoveTargetError, ):
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
            print("Removing expired contested request:", str(initial_request.filter_templates()[0].get(1).value)+" --> "+str(initial_request.filter_templates()[0].get(2).value))
            notify_requesters(initial_request.filter_templates()[0].get("requester").value)
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


def notify_requesters(requester):
    if requester == "":
        return
    talk_page = pywikibot.Page(site, "User talk:{}".format(requester))
    if talk_page.isRedirectPage():  # If a user is renamed while their request is being contested.
        talk_page = talk_page.getRedirectTarget()
    talk_page.text += "\n{{subst:User:TenshiBot/RMTR contested notification}}"
    try:
        talk_page.save(summary="Notification: Your contested technical move request has been removed from [[Wikipedia:Requested moves/Technical requests]].", minor=False)
    except pywikibot.exceptions.OtherPageSaveError:
        print("Failed to notify {}".format(requester))
    else:
        print("Notified {}of their contested request being removed".format(requester))


def reassemble_page():
    return "\n".join(instructions+uncontroversial_requests+undiscussed_moves+contested_requests+administrator_moves)


uncontroversial_requests = process_non_contested_requests(uncontroversial_requests)
undiscussed_moves = process_non_contested_requests(undiscussed_moves)
contested_requests = process_contested_requests(contested_requests)
if actions["technical"]+actions["RMUM"]+actions["contested"] > 0:  # Check to see if anything has been done before saving an edit.
    rmtr.text = reassemble_page()
    rmtr.save(summary="Userspace testing: Clerk [[Wikipedia:Requested moves/Technical requests|RM/TR]]. Processed {} technical requests, {} move revert requests and {} contested requests.".format(actions["technical"], actions["RMUM"], actions["contested"]), minor=False)
