def get_talk_page(user: str):
    import pywikibot
    site = pywikibot.Site()
    user_talk_page = pywikibot.Page(site, "User talk:{}".format(user))
    if user_talk_page.isRedirectPage():
        user_talk_page = user_talk_page.getRedirectTarget()
    return user_talk_page


def load_task(task: str, task_number: int or str):
    from datetime import datetime
    from importlib import import_module
    print("Task {} ({}) started at {}".format(task_number, task, datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S]")))
    try:
        import_module(task)
    except Exception as exception:
        log_error("Fatal exception: {}".format(exception), task_number)
    finally:
        print("Task {} ({}) ended at {}".format(task_number, task, datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S]")))


def log_error(error: str, task_number: int or str, error_page: str = "User:TenshiBot/Errors"):
    from datetime import datetime
    import pywikibot
    site = pywikibot.Site()
    error_page = pywikibot.Page(site, error_page)
    error_text = "\n# {} (Task {}): {}\n".format(datetime.utcnow().strftime("[%Y-%m-%d %H:%M]"), str(task_number), error)
    error_page.text += error_text
    print(error_text[3:])
    error_page.save(summary="Logging error during task {}".format(str(task_number)), minor=False, quiet=True)


def log_file(message: str, path: str):
    from datetime import datetime
    file = None
    try:
        file = open(path, "a")
    except FileNotFoundError:
        open(path, "x")
        file = open(path, "a")
    finally:
        file.write(datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S] ")+message+"\n")


def mediawikitimestamp_to_datetime(mediawikitimestamp: str):
    from datetime import datetime
    return datetime(year=int(mediawikitimestamp[0:4]), month=int(mediawikitimestamp[4:6]), day=int(mediawikitimestamp[6:8]),
                    hour=int(mediawikitimestamp[8:10]), minute=int(mediawikitimestamp[10:12]), second=int(mediawikitimestamp[12:14]))


class NotificationSystem:
    def __init__(self):
        self.notification_queue = {}

    def add(self, receiver: str, message: str):
        try:
            user_talk_page = get_talk_page(receiver)
            if "User talk:"+receiver != user_talk_page.title():
                receiver = str(user_talk_page.title()).replace("User talk:", "")
            self.notification_queue[receiver].append(message)
        except (TypeError, KeyError):
            self.notification_queue[receiver] = [message]

    def notify_all(self, summary: str):
        from pywikibot.exceptions import EditConflictError
        for receiver in self.notification_queue.keys():
            while True:
                try:
                    self._notify(receiver, summary)
                except EditConflictError:
                    print("Failed to notify {} - Edit conflict".format(receiver))
                else:
                    break
        self.notification_queue = {}

    def _notify(self, receiver: str, summary: str):
        from pywikibot.exceptions import OtherPageSaveError
        user_talk_page = get_talk_page(receiver)
        for message in self.notification_queue[receiver]:
            user_talk_page.text += "\n\n"+message
        try:
            user_talk_page.save(summary=summary, minor=False, quiet=True)
        except OtherPageSaveError:
            print("Failed to notify {}".format(receiver))
        else:
            print("Notified {}".format(receiver))


def wiki_delinker(link: str):
    return link.replace("[[", "", 1).replace("]]", "", 1)