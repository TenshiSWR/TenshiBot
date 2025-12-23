import pywikibot
import random
import regex

site = pywikibot.Site()
search_regex = regex.escape(input("Search regex: "))
replace_regex = regex.escape(input("Replace regex: "))
summary = input("Edit summary to use: ")
flag = {"yes": True, "y": True, "no": False, "n": False}[input("Use bot flag if available?: ").lower()]
minor = {"yes": True, "y": True, "no": False, "n": False}[input("Mark edits as minor?: ").lower()]

if input("Restrict namespaces?: ").lower() == ("Y".lower() or "Yes".lower()):
    namespaces = [int(namespace) for namespace in input("Namespaces to restrict (demarcate by using ,): ").split(",")]
    results = site.search(r"insource:/{}/".format(search_regex), namespaces=namespaces)
else:
    namespaces = []
    results = site.search(r"insource:/{}/".format(search_regex))

string = "".join([chr(random.randint(65, 90)) for i in range(0, 10)])

print("\nSettings:\n"+
      "Search regex: {}\n".format(search_regex)+
      "Replace regex: {}\n".format(replace_regex)+
      "Edit summary: {}\n".format(summary)+
      "Use bot flag if available?: {}\n".format("Yes" if flag else "No")+
      "Mark edits as minor?: {}\n".format("Yes" if flag else "No")+
      "\n"+
      "To confirm that these settings are correct and start editing, please type {}".format(string))

while True:
    if input() == string:
        break

_ = 0
for page in results:
    _ += 1
    print(page.title(), _)
    page.text = regex.sub(search_regex, replace_regex, page.text)
    page.save(summary=summary, bot=flag, minor=minor)
