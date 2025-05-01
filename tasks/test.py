import pywikibot
import datetime
site = pywikibot.Site()
test_page = pywikibot.Page(site, "User:TenshiBot/test")
test_page.text = datetime.datetime.utcnow()
test_page.save(summary="Test edit at {}".format(datetime.datetime.utcnow()), minor=False)
