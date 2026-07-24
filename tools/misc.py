def get_database():
    from dotenv import load_dotenv
    from os.path import exists
    if exists("replica.my.cnf"):
        import toolforge
        db = toolforge.toolsdb("s56602__tenshibot_p")
    else:
        from json import loads
        import mysql.connector as connector
        from os import getenv
        load_dotenv()
        db_info = loads(getenv("DB-INFO"))
        db = connector.connect(host=db_info[0], user=db_info[1], password=db_info[2], database="s56602__tenshibot_p")
        del db_info
    return db, db.cursor()


def get_talk_page(user: str):
    import pywikibot
    site = pywikibot.Site()
    user_talk_page = pywikibot.Page(site, "User talk:{}".format(user))
    if user_talk_page.isRedirectPage():
        user_talk_page = user_talk_page.getRedirectTarget()
    return user_talk_page


def load_task(task: str, task_number: int | str, site_name: str = "wikipedia:en"):
    from datetime import datetime
    from importlib import import_module
    print("Task {} ({}) started at {}".format(task_number, task, datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S]")))
    _ = queryandfetchone("SELECT * FROM task_status WHERE task = %(task)s;", {"task": task})[4]
    if _ is None or _ == site_name:
        queryandclose("UPDATE task_status SET task_number = %(task_number)s, start = %(start)s, site_name = %(site_name)s, status = 'Running' WHERE task = %(task)s AND site_name = %(site_name)s;", {"task_number": task_number, "start": datetime.utcnow(), "site_name": site_name, "task": task})
    else:
        queryandclose("INSERT INTO task_status(task, task_number, start, site_name, status) VALUES(%(task)s, %(task_number)s, %(start)s, %(site_name)s, 'Running');", {"task": task, "task_number": task_number, "start": datetime.utcnow(), "site_name": site_name})
    try:
        import_module(task)
    except Exception as exception:
        log_error("Fatal exception: {}".format(exception), task_number, site_name=site_name)
        queryandclose("UPDATE task_status SET end = %(end)s, status = 'Fatal exception' WHERE task = %(task)s AND site_name = %(site_name)s;", {"end": datetime.utcnow(), "task": task, "site_name": site_name})
    else:
        queryandclose("UPDATE task_status SET end = %(end)s, status = 'Ended' WHERE task = %(task)s AND site_name = %(site_name)s;", {"end": datetime.utcnow(), "task": task, "site_name": site_name})
    finally:
        print("Task {} ({}) ended at {}".format(task_number, task, datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S]")))


class LintfixModuleError(Exception):
    pass


def log_error(error: str, task_number: int | str, error_page: str = "User:TenshiBot/Errors", site_name: str = "wikipedia:en", soft: bool = False):
    from datetime import datetime
    import pywikibot
    site = pywikibot.Site(site_name)
    error_page = pywikibot.Page(site, error_page)
    error_text = "\n# {} (Task {}): {}\n".format(datetime.utcnow().strftime("[%Y-%m-%d %H:%M]"), str(task_number), error)
    if soft and error in error_page.text:
        return
    print(error_text[3:])
    error_page.text += error_text
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


class NoChange(Exception):
    """No change was detected or able to be made."""
    pass


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


def queryandclose(query: str, params: dict | None = None) -> None:
    db, cursor = get_database()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    db.commit()
    db.close()


def queryandfetchone(query: str, params: dict | None = None) -> dict:
    db, cursor = get_database()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    db.commit()
    db.close()
    return cursor.fetchone()


class QueryError(Exception):
    pass


def wiki_delinker(link: str):
    return link.replace("[[", "", 1).replace("]]", "", 1)