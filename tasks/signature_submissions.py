import pywikibot
import regex
from time import sleep
from tools.misc import log_error
from tools.summaries import EDIT_FAIL_EDITCONFLICT_SUMMARY, EDIT_FAIL_PROTECTED_SUMMARY, EDIT_FAIL_WTF_SUMMARY, TASK13_SUMMARY
from tqdm import tqdm

# Due to the nature of this task, regexes contain material licensed under CC-BY-SA 4.0 and the GFDL
# from https://en.wikipedia.org/wiki/Wikipedia:Linter/Signature_submissions
regexes = {
    # Misnested tags
    r"insource:/\<center\>\<small\>''Ichthus'' is the newsletter of Christianity/":[[r"""(<div style="background-color:#FFF;"><div style="font-size: 120%;">\n.*?)<big>'''\n(.*?)'''<\/big>\n(.*?)<center>(.*?)<\/center>\n<\/div>\n<\/div>""", r"\1\2\3{{center|1=\4}}</div>\n"],
                                                                                    [r"""<center>(<small>''Ichthus'' is published by.*?</small>)</center>""", r"""{{center|1=\1}}"""],
                                                                                    [r"""<center>(This depiction of the Crucifixion[^\n]*?)\n *<\/center>""", r"""{{center|1=\1}}"""],
                                                                                    [r"""<center>(<small>''Ichthus'' is the newsletter of Christianity[^\n<>]*?<\/small>)<\/center>""", r"""{{center|1=\1}}"""]],

    # Stripped tags
    r"insource:/help out!\n\<\/font>/":[[r"""(Visit the \[\[Wikipedia:WikiProject Articles for creation\/[^\n]*?Backlog Elimination Drive\|drive's page\]\] and help out!)\n<\/font>""", r"""\1"""]],
    r"insource:/''\<sup\>\[\[User:sillybillypiggy\/guestbook\|''\¡SIGN NOW OR ELSE\!''\]\]\<\/sup\>[^']/":[[r"""(gy'''<\/(?:font|span)>\]\])''""", r"""\1"""]],
    r"insource:/[6-9] June 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s(?:[6-9]|1[0-9]|2[0-9]|30)\sJune\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],
    r"insource:/\d{2} June 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s(?:[6-9]|1[0-9]|2[0-9]|30)\sJune\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],

    # Missing end tags
    r"insource:/\<div style=\"margin:[^\n]*?Thank you for[^\n]*?Happy [Ee]diting![^\n]*?\(UTC\) *?[\n\r]\|\}/":[[r"""(<div style="margin:[^\n]*?Thank you for[^\n]*?Happy [Ee]diting![^\n]*?\(UTC\) *?)([\n\r]\|\})""", r"""\1</div>\2"""]],
    r"insource:/\|\<font color\=\"[a-z]*\"\>\'[\' A-Za-z0-9\!]*.\|-/":[[r"""(^\|style=".*?height: 1\.1em;)(" \|)<font color="([a-z]+)">""", r"""\1 color: \3;\2"""]],
    r"insource:/\>\'\'\'Caballero\</":[[r"""(?<!''')(\[\[User:Caballero[^\n]*?)'''(Caballero[^\n]*?<\/u>)'''(\]\]<\/sup>)""", r"""'''\1\2\3'''"""]],
    r"insource:/\]\] \(\[\[User talk:Sabrebd\|talk\]\]\)\<\/span> \d/":[[r"""('''<span style="font-family:Black Chancery;text:grey 0.3em 0.3em 0.1em;">\[\[User:Sabrebd[^\n]*?\|talk\]\]\)<\/span>)(?!''')""", r"""\1'''"""]],
    r"insource:/Greetings! You have been randomly[^\n]*?service\]\]\.''/":[[r"""(Greetings! You have been randomly(?:(?:(?!(?<!')''(?!')).)*?)service\]\]\.)''""", r"""\1"""]],
    r"insource:/\'\'\'\[\[Wikipedia:Five pillars\|The five pillars of Wikipedia\]\] • /":[[r"""({\| width=100%.*?\|)<center>(.*?Welcome to Wikipedia!\]\])(?<!''')(.*?)<\/center>(.*?The five pillars of Wikipedia\]\])(?<!''')(.*?\{\{col-end\}\}[\n\r])""", r"""\1{{center|1=\2}}\3'''\4'''\5\n{{col-end}}"""]],
    r"insource:/\]\]\'\'\'\<sup\>\[\[User_talk:OlYeller21/ insource:/Talktome\<\/span\>\]\]\<\/sup\> / -insource:/\(UTC\)\'\'\'/":[[r"""('''<sup>\[\[User_talk:OlYeller21[^\n]*?<\/sup>)(?!''')""", r"""\1'''"""]],
    r"insource:/KuwarOnline\<\/span\>\<\/b\>\]\]\'\'\'/":[[r"""(KuwarOnline<\/span><\/b>\]\])'''""", r"""\1"""]],
    r"insource:/KuwarOnline\<\/b\>\]\]\'\'\'/":[[r"""(KuwarOnline<\/b>\]\])'''""", r"""\1"""]],
    r"insource:/\<tt> :D \<\/tt>/":[[r"""<tt>([^<]*?)<\/tt>""", r"""{{mono|\1}}"""],
                                    [r"""(<div style="margin: 0; background-color:#EEEEFF; font-family: sans-serif; border:1px solid#ff69b4; text-align:left; color:black; padding-left:0.4em; padding-top: 0.2em; padding-bottom: 0.2em;">)<p>""", r"""\1"""]],
    r"insource:/\'\'The\ following\ discussion\ is\ preserved\ as\ an\ archive\ of\ a\ \[\[wikipedia\:requests\ for\ adminship\|request\ for\ adminship\]\]\ that\ \'\'\'did\ not\ succeed\'\'\'\.\ \<span\ style\=\"color\:red\"\>\'\'\'Please\ do\ not\ modify\ it\.\'\'\'\<\/span\>\[\[Category\:Unsuccessful\ requests\ for\ adminship\|\{\{SUBPAGENAME\}\}\]\][^']/":[[r"""(:''The following discussion[^\n]*?<\/span>[^\n']*?\}\}\]\])$""", r"""\1''"""]],
    r"insource:/\|\<span style\=\"color:green;\"\>Richerman\<\/span\>\'\'\]\]/":[[r"""(Richerman\|<span[^>]*?>Richerman<\/span>)''(\]\])""", r"""\1\2"""]],
    r"insource:/''\[\[User:TheChampionMan1234\|The\]\]'''\[\[User talk:TheChampionMan1234\|ChampionMan\]\]'''\[\[Special:Contributions\/TheChampionMan1234\|1234\]\][^']/":[[r"""(''\[\[User:TheChampionMan1234[^\n]*?\|1234\]\])(?!'')""", r"""\1''"""]],
    r"insource:/\[\[User\:RickK\|Rick\]\]\'\'\'\[\[User talk\:RickK\|K\]\][^']/":[[r"""(\[\[User:RickK\|Rick\]\]'''[^\n]*?\|K\]\])(?!''')""", r"""\1'''"""]],
    r"insource:/''Best wishes for your Christmas\<br>Is all you get from me[^\n]*?An' you never would be broke.\"[^']/":[[r"""(''Best wishes for your Christmas[^\n]*?An' you never would be broke\.")(?!'')"""], r"""\1''"""],
    r"insource:/''\"Here's hoping[^\n]*?sorrow don't find you\.\"[^\n']*?\n/":[[r"""(''"Here's hoping[^\n]*?sorrow don't find you\.")(?!'')([^\n']*?$)""", r"""\1''\2"""]],

    # Obsolete center tags
    r"insource:/\<center\>\<small\>Got any suggestions\?/":[[r"""(<br(?: \/)?>)<center>(<small>Got any suggestions\?[^\n]*?)<\/center>""", r"""\1{{center|1=\2}}"""]],
    r"insource:/featured picture\]\] status\'\'\'\<\/center\>/":[[r"""<center>((?:\[\[Image:Cscr-featured\.svg|'''An image ''edited'')[^\n]*?)<\/center>""", r"""{{center|1=\1}}"""]],

    # Invalid font tags
    r"insource:/\<font *\= *[+\-\d]\d*\>/":[[r"""<font *\= *([+\-\d]\d*)\>""", r"""<font size="\1">"""]],
    r"insource:/\<font family=/":[[r"""(<font )family=""", r"""\1face="""]]
}
site = pywikibot.Site()
DEBUG = False

pages, empty = [], []
count, per_regex = {}, {}
bar = tqdm(total=len(regexes.keys()))
for search in regexes.keys():
    while True:
        bar.set_description(search)
        try:
            _ = [page.title() for page in site.search(search)]
            if len(_) <= 1:
                empty.append("{}: 0 results excluding signature submissions page".format(search))
            if DEBUG:
                count[search] = len(_)
                per_regex[search] = _
            pages += _
        except pywikibot.exceptions.APIError:
            sleep(10)
            continue
        else:
            bar.update(1)
            break

bar.close()
pages = list(set(pages))

for text in empty:
    print(text)

if "Wikipedia:Linter/Signature submissions" in pages:
    pages.pop(pages.index("Wikipedia:Linter/Signature submissions"))

i, total = 0, len(pages)
for page in pages:
    i += 1
    if not DEBUG:
        print("Signature submissions: {} ({}/{})".format(page, i, total))
    else:
        for _ in regexes.keys():
            if page in per_regex[_]:
                _ = _[9:40]
                break
        print("Signature submissions: {} ({}/{} | {})".format(page, i, total, _))
    page = pywikibot.Page(site, page)
    text = page.text
    old_text = text
    for _ in regexes.values():
        for find, replace in _:
            if not regex.search(r"<(?:nowiki|syntaxhighlight)>.*"+find+r".*<\/(?:nowiki|syntaxhighlight)>", text):
                #print(find+" | "+replace)
                text = regex.sub(find, replace, text, flags=regex.DOTALL|regex.MULTILINE)
    if old_text == text:
        continue
    page.text = text
    #pywikibot.showDiff(old_text, text, context=3)
    try:
        page.save(summary=TASK13_SUMMARY, minor=True, tags=["fixed lint errors"], force=True)
    except pywikibot.exceptions.EditConflictError:
        log_error(EDIT_FAIL_EDITCONFLICT_SUMMARY.format(page.title()), 13, soft=True)
    except pywikibot.exceptions.LockedPageError:
        log_error(EDIT_FAIL_PROTECTED_SUMMARY.format(page.title()), 13, soft=True)
    except pywikibot.exceptions.OtherPageSaveError:
        log_error(EDIT_FAIL_WTF_SUMMARY.format(page.title()), 13, soft=True)
