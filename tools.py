def get_talk_page(user: str):
    import pywikibot
    site = pywikibot.Site()
    user_talk_page = pywikibot.Page(site, "User talk:{}".format(user))
    if user_talk_page.isRedirectPage():
        user_talk_page = user_talk_page.getRedirectTarget()
    return user_talk_page


def log_error(error: str, task_number: int):
    from datetime import datetime
    import pywikibot
    site = pywikibot.Site()
    error_page = pywikibot.Page(site, "User:TenshiBot/Errors")
    error_page.text += "\n# {} (Task {}): {}\n".format(datetime.utcnow().strftime("[%Y-%m-%d %H:%M]"), str(task_number), error)
    error_page.save(summary="Logging error during task {}".format(str(task_number)), minor=False, bot=True)


def mediawikitimestamp_to_datetime(mediawikitimestamp: str):
    from datetime import datetime
    return datetime(year=int(mediawikitimestamp[0:4]), month=int(mediawikitimestamp[4:6]), day=int(mediawikitimestamp[6:8]),
                    hour=int(mediawikitimestamp[8:10]), minute=int(mediawikitimestamp[10:12]), second=int(mediawikitimestamp[12:14]))
