import pywikibot
import regex
from time import sleep
from tools.summaries import TASK13_SUMMARY

# Due to the nature of this task, regexes contain material licensed under CC-BY-SA 4.0 and the GFDL
# from https://en.wikipedia.org/wiki/Wikipedia:Linter/Signature_submissions
regexes = {
    # Misnested tags
    r"insource:/\<center\>\<small\>''Ichthus'' is the newsletter of Christianity/":[[r"""(<div style="background-color:#FFF;"><div style="font-size: 120%;">\n.*?)<big>'''\n(.*?)'''<\/big>\n(.*?)<center>(.*?)<\/center>\n""", r"\1\2\3{{center|1=\4}}"]],

    # Stripped tags
    r"insource:/font style\=\"arial: ridge/":[[r"""<font( style="arial: ridge.*#000000)" color=#FF0000(.*?)<font color=#ff0000><font face="arial">(.*?)<\/font><\/font>(.*?)<\/font>(.*?)<font color=#FF0000><font face="arial">(.*?)<\/font><\/font>(.*?)<font color=#000000><font face="arial">(.*?)<\/font><\/font>""", r"""<span\1; color: #FF0000"\2<span style="color:#ff0000; font-family: arial">\3</span>\4</span>\5<span style="color:#FF0000; font-family: arial">\6</span>\7<span style="color:#000000; font-family: arial">\8</span>"""]],

    # Missing end tags
    r"insource:/\|\<center\>..Image\:AnimWIKISTAR-laurier-WT\.gif\|AnimWIKISTAR-laurier-WT\.gif...\<big\>\<center\>/":[[r"""<center>\[\[Image:AnimWIKISTAR-laurier-WT.gif\|AnimWIKISTAR-laurier-WT.gif\]\]""", r"""[[Image:AnimWIKISTAR-laurier-WT.gif|AnimWIKISTAR-laurier-WT.gif|center]]"""],
                                                                                                                       [r"""<big><center>(.*?)<\/br>(.*?)<\/br>(.*?)<\/center><\/big><\/br>""", r"""{{center|1=\1<br>\2<br>\3<\/big>}}"""],
                                                                                                                       [r"""(\|colspan="2" )\|<center>(.*?)<\/br>(.*?)<\/center>""", r"""\1style="text-align: center;" |\2<br>\3"""]],

    # Obsolete center tags
    r"insource:/\<center>\<big>Please join us in downtown San Francisco!\<\/big>\<\/center>/":[[r"""<center>(<big>Please join us in downtown San Francisco!<\/big>)<\/center>""", r"""{{center|1=\1}}"""]]
}
site = pywikibot.Site()

pages = []
for search in regexes.keys():
    while True:
        try:
            pages += [page.title() for page in site.search(search)]
        except pywikibot.exceptions.APIError:
            sleep(10)
            continue
        else:
            break
pages = list(set(pages))

if "Wikipedia:Linter/Signature submissions" in pages:
    pages.pop(pages.index("Wikipedia:Linter/Signature submissions"))

for page in pages:
    print("Signature submissions: {} ({}/{})".format(page, pages.index(page)+1, len(pages)))
    page = pywikibot.Page(site, page)
    text = page.text
    old_text = text
    for _ in regexes.values():
        for find, replace in _:
            #print(find+" | "+replace)
            text = regex.sub(find, replace, text, flags=regex.DOTALL)
    if old_text == text:
        continue
    page.text = text
    #pywikibot.showDiff(old_text, text, context=3)
    page.save(summary=TASK13_SUMMARY, minor=True, tags=["fixed lint errors"], force=True)
