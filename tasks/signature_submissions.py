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
    r"insource:/\<center\>\<small\>''Ichthus'' is the newsletter of Christianity/":[[r"""(<div style="background-color:#FFF;"><div style="font-size: 120%;">\n.*?)<big>'''\n(.*?)'''<\/big>\n(.*?)<center>(.*?)<\/center>\n<\/div>\n<\/div>""", r"\1\2\3{{center|1=\4}}<\/div>\n"],
                                                                                    [r"""<center>(<small>''Ichthus'' is published by.*?</small>)</center>""", r"""{{center|1=\1}}"""]],
    r"insource:/\[\[User:PotatoNinja\|\<span style=\"color:\#fa0;font-family: sans-serif;\"\>'''Potato\<\/span\>\<span style=\"color:\#000080;font-family: helvetica\"\>Ninja\<\/span\>\]\]/":[[r"""(\[\[User:PotatoNinja\|)(<span[^\n]*)'''([^\n]*?)(\]\])""", r"""\1'''\2\3'''\4"""]],
    r"insource:/>Jreferee\]\]/":[[r"""<font face="Kristen ITC">([^\n]*?\|)<font color="Blue">([^\n]*?)(\][^\n]*?)(<\/font>)\4""", r"""<span style="font-family: Kristen ITC;">\1<span style="color: Blue;">\2</span>\3</span>"""]],

    # Stripped tags
    r"insource:/font style\=\"arial: ridge/":[[r"""<font( style="arial: ridge[^\n]*#000000)" color=#FF0000([^\n]*?)<font color=#ff0000><font face="arial">([^\n]*?)<\/font><\/font>([^\n]*?)<\/font>([^\n]*?)<font color=#FF0000><font face="arial">([^\n]*?)<\/font><\/font>([^\n]*?)<font color=#000000><font face="arial">([^\n]*?)<\/font><\/font>""", r"""<span\1; color: #FF0000"\2<span style="color:#ff0000; font-family: arial">\3</span>\4</span>\5<span style="color:#FF0000; font-family: arial">\6</span>\7<span style="color:#000000; font-family: arial">\8</span>"""],
                                              [r"""<font( style="arial: ridge 2px #FF0000;")>(.*?)(<font color=#FF0000><font face="arial">)(.*?)(<\/font><\/font>)(.*?)<\/font>(.*?)\3(.*?)\5(.*?)<font color=#000000><font face="arial">(.*?)\5""", r"""<span\1>\2<span style="color: #FF0000; font-family: arial;">\4</span>\6</span>\7<span style="color: #FF0000; font-family: arial;">\8</span>\9<span style="color: #000000; font-family: arial;">\10</span>"""]],
    r"insource:/help out!\n\<\/font>/":[[r"""(Visit the \[\[Wikipedia:WikiProject Articles for creation\/March 2013 Backlog Elimination Drive\|drive's page\]\] and help out!)\n<\/font>""", r"""\1"""]],
    r"insource:/You can find more information on the case subpage/ insource:/\]\]\.\<\/center>\<br>/":[[r"""(, \[\[Wikipedia:Requests for mediation\/.*?\]\]\.)<\/center>""", r"""\1"""]],
    r"insource:/''\<sup\>\[\[User:sillybillypiggy\/guestbook\|''\¡SIGN NOW OR ELSE\!''\]\]\<\/sup\>[^']/":[[r"""(gy'''<\/span>\]\])''""", r"""\1"""]],
    r"insource:/\[\[User talk:Intesvensk\|\<span style=\"color:gold;\"\>'''sv\&\#603;nsk'''''\<\/span\>\]\]/":[[r"""(User talk:Intesvensk\|[^\n]*?nsk''')''<\/span>""", r"""\1\2"""]],
    r"insource:/\[\[User talk:Kinaro\|\(talk\)'''\]\]/":[[r"""(\|\(talk\))'''""", r"""\1"""]],
    r"insource:/\[\[User talk:Neranei\|\<span / insource:/\(talk\)\<\/span>\<\/font>\]\]/":[[r"""(>\(talk\)[^\n]*?)<\/font>""", r"""\1"""]],
    r"insource:/e\<\/small\>!\<\/span\>\]\]\<\/sup\>\<\/span\> /":[[r"""(<\/small>!<\/span>\]\]<\/sup>)<\/span>""", r"""\1"""]],
    r"insource:/Ankit Maity\'\'\'\<\/span\>\]\]\<\/font\>/":[[r"""(ity'''.*)<\/font>""", r"""\1"""]],
    r"""insource:"Directory of species" insource:/\<\/tr\>\<tr\>/ insource:/sister\-projects\-list/""":[[r"""(<div id="sister-projects-list" class="layout plainlinks">.*?)(<\/tr><tr>\n)(.*?)\2(.*?)\2""", r"""\1\3\4"""]],
    r"insource:/June 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s(?:[6-9]|1[0-9]|2[0-9]|30)\sJune\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],
    r"insource:/July 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s\d{1,2}\sJuly\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],
    r"insource:/August 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s\d{1,2}\sAugust\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],
    r"insource:/September 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s\d{1,2}\sSeptember\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],
    r"insource:/October 2014 \(UTC\)\<\/div>\<\!\-\-Template:Afc decline\-\->\<\/div>/":[[r"""(<div.*?File:AFC-Logo_Decline\.svg.*?,\s(?:[1-9]|1[0-9]|2[0-9])\sOctober\s2014\s\(UTC\))<\/div>(<!--Template:Afc decline)""", r"""\1\2"""]],

    # Missing end tags
    r"insource:/\|\<center\>..Image\:AnimWIKISTAR-laurier-WT\.gif\|AnimWIKISTAR-laurier-WT\.gif...\<big\>\<center\>/":[[r"""<center>\[\[Image:AnimWIKISTAR-laurier-WT.gif\|AnimWIKISTAR-laurier-WT.gif\]\]""", r"""[[Image:AnimWIKISTAR-laurier-WT.gif|AnimWIKISTAR-laurier-WT.gif|center]]"""],
                                                                                                                       [r"""<big><center>(.*?)<\/br>(.*?)<\/br>(.*?)<\/center><\/big><\/br>""", r"""{{center|1=<big>\1<br>\2<br>\3</big>}}"""],
                                                                                                                       [r"""(\|colspan="2" )\|<center>(.*?)<\/br>(.*?)<\/center>""", r"""\1style="text-align: center;" |\2<br>\3"""],
                                                                                                                       [r"""<font color="(orange)">('''5''')</font>""", r"""<span style="color: \1;">\2</span>"""]],
    r"insource:/\|\'\'\'\<span style\=\"color:blue;\"\>Flat Out\<\/span\>\]\]/":[[r"""(\[\[User:Flat Out\|'''<span style="color:blue;">Flat Out</span>)(\]\])""", r"""\1'''\2"""]],
    r"insource:/\[\[Special:Contributions\/Gilo1969\|\<span style=\"color: white; background: red; font-family: 'Arial Rounded MT Bold',Arial,Sans-serif\"\>\&nbsp;A\&\]\]/":[[r"""(Special:Contributions\/Gilo1969.*?A&)""", r"""\1</span>"""]],
    r"insource:/\'\'\'\'\'..WP\:ADOPT\|Get adopted..\'\'.\|-/":[[r"""('''''\[\[WP:ADOPT\|Get adopted\]\]'')(\n\|)""", r"""\1'''\2"""]],
    r"insource:/quote  \= You may also wish to consider using a Wizard to help you create articles\. See the ..Wikipedia\:Article wizard\|Article Wizard..\.\'\'\'\'\'. \|/":[[r"""(\|Article Wizard\]\].)'''''""", r"""\1"""]],
    r"insource:/\'\'The\ following\ discussion\ is\ preserved\ as\ an\ archive\ of\ a\ \[\[wikipedia\:requests\ for\ adminship\|request\ for\ adminship\]\]\ that\ \'\'\'did\ not\ succeed\'\'\'\.\ \<strong\ style\=\"color\:red\"\>Please\ do\ not\ modify\ it\.\<\/strong\>\[\[Category\:Unsuccessful\ requests\ for\ adminship\|\{\{SUBPAGENAME\}\}\]\][^']/":[[r"""(:''The following discussion.*?\]\])$""", r"""\1''"""]],
    r"insource:/\n\* \'\'\'\[\[Wikipedia\:Selected anniversaries\/\w*\|Archive\]\]\n/":[[r"""(\* '''\[\[Wikipedia:Selected anniversaries\/\w+\|Archive\]\])$""", r"""\1'''"""]],
    r"insource:/\<span style\=\"font\-family:Ubuntu;\">\'\'\'\[\[User:Thepenguin9\|\<span style\=\"color\:\#5828ee\">Thepenguin9\<\/span>\]\]/":[[r"""('''\[\[User:Thepenguin9\|[^\n]*?\]\])(?!''')""", r"""\1'''"""]],
    r"insource:/how articles should be written\.\<\/li>\s\<\/td>/":[[r"""(<tr><td>\n<ul style=.*?<\/li>\n)(<\/td><\/tr>)""", r"""\1</ul>\n\2"""], [r"""(Image:Evolution-tasks2\.png.*?<\/li>\n)(<\/td><\/tr>)""", r"""\1</ul>\n\2"""]],
    r"insource:/\'\'What would you like to change about that\?[^\']+/":[[r"""(; ''What[^\n]*?\?)$""", r"""\1''"""]],
    r"insource:/\<big\>\<big\>\<big\>\<big\>I am now an admin!!!\<\/big\>\<big\>\<\/big\>\<\/big\>/":[[r"""(<big>)\1{3}(I am now an admin!{3})(<\/big>)<big>\3\3""", r"""\1\1\1\1\2\3\3\3\3"""]],
    r"insource:/\<font color\=\"\#660000\"\>```\[\[User\: Buster7/ insource:/black\"\> Talk\<\/em\>\'\'\'\]\]\<\/small\>[^\<]/":[[r"""(<span class="plainlinks"[^\n]*?>)<font color="#660000">([^\n]*?<\/small>)""", r"""\1\2</span>"""]],
    r"insource:/Finally, please do your best to[^\n]*? Happy editing![^\n]*?\(UTC\)\n\|\}/":[[r"""(Finally, please do your best to '''always fill in the \[\[Help:Edit summary\|edit summary\]\] field'''\. Happy editing![^\n]*?\(UTC\))(\n\|\})""", r"""\1</div>\2"""]],
    r"insource:/\|\'\'\'\<font color\=\"green\">Jianhui67\<\/font>\]\]/ -intitle:Linter":[[r"""(\[\[User:Jianhui67\|''')<font color="(green)">([^\n]*?)<\/font>(\]\])""", r"""\1<span style="color: \2;">\3</span>'''\4"""]],
    r"insource:/\|\'\'\'\<span style\=\"color:green;\">Jianhui67\<\/span>\]\]/ -intitle:Linter":[[r"""(\[\[User:Jianhui67\|'''[^\n]*?<\/span>)(\]\])""", r"""\1'''\2"""]],
    r"insource:/\[\[User:Vertium\|\<span style=\"color:\#4169E1\"\>Vertium\<\/span\>\]\]'' \<small\>\<sup>\[\[User talk:Vertium\|\<span style=\"color:\#9400D3\"\>When all is said\<\/span\>\]\]\<\/sup\> \<sub\>\[\[Special:Contributions\/Vertium\|\<span style=\"color:\#228B22\"\>and done\<\/span\>\]\]\<\/sub\>\<\/small\>[^']/":[[r"""(\[\[User:Vertium\|<span[^\n]*?<\/small>)(?!'')""", r"""\1''"""]],
    r"insource:/\|\<font color\=\"[a-z]*\"\>\'[\' A-Za-z0-9\!]*.\|-/":[[r"""(^\|style=".*?height: 1\.1em;)(" \|)<font color="([a-z]+)">""", r"""\1 color: \3;\2"""]],
    r"insource:/\'\'\'\&nbsp\;\&\#124\;\&nbsp\;\[\[User\_talk\:Gordonrox24\|\<sup\>\<span\ style\=\"font-family\:Arial\;color\:red\"\>\'\'Talk\'\'\<\/span\>\<\/sup\>\]\][^']/":[[r"""('''&nbsp;[^\n]*?Gordonrox24[^\n]*?\]\])(?!''')""", r"""\1'''"""]],
    r"insource:/>\'\'\'Happy\<\/span>/":[[r"""(\[\[User:Happysailor\|<span[^\n]*?>)'''([^\n]*?sailor)'''(<\/span>\]\])""", r"""'''\1\2\3'''"""]],
    r"insource:/\<hr\/>\<p>\<small>\'\'\'Notice to administrators:\'\'\'.*?\<\/small\>\<\/div\>/":[[r"""(<hr\/>)<p>([^\n]*?<\/small><\/div>)""", r"""\1\2"""]],
    r"insource:/[^']\[\[User:Tofutwitch11\|\<span style='font-family: \"Arial Black\"; color:Teal'\>\<big\>T\<\/big\>\<small\>ofutwitch11\<\/small\>\<\/span\>\]\]''' \<sup\>\<small\>\[\[User talk:Tofutwitch11\|\<span style=\"color:Orange;\"\>\(T\<small\>ALK\<\/small\>\)\<\/span\>\]\]\<\/small\>\<\/sup\>[^']/":[[r"""(\[\[User:Tofutwitch11\|<span[^\n]*?\]\]'''[^\n]*?<\/small><\/sup>)(?!''')""", r"""\1''''"""]],
    r"insource:/\[\[User\:Jeremjay24\|\<span\ style\=\"font-family\:Tahoma\;color\:\#FF8040\"\>Jeremjay24\<\/span\>\]\]\'\'\'\&nbsp\;\[\[User_talk\:Jeremjay24\|\<sub\>\<span\ style\=\"font-family\:Tahoma\;color\:green\"\>\'\'msg\'\'\<\/span\>\<\/sub\>\]\]/":[[r"""(\[\[User:Jeremjay24\|<span[^\n]*?\]\]'''.*?<\/sub>\]\])(?!''')""", r"""\1'''"""]],
    r"insource:/\[\[User:Wifione\|''\<span style=\"color: blue; text-shadow:silver 0.3em 0.3em 0.1em\"\>▒  ♪ ♫ Wifione ♫ ♪  ▒\<\/span\>\]\]/":[[r"""(\[\[User:Wifione\|''<span[^\n]*?<\/span>)(\]\])""", r"""\1''\2"""]],
    r"insource:/\[\[User:AlexJFox\|'''\<span style=\"background-color:\#CCCCCC\"\>\<span style=\"color:red\"\>\<sup\>Alex\<\/sup\>\<\/span\> \<span style=\"color:white\"\>\<small\>J\<\/small\>\<\/span\> \<span style=\"color:blue\"\>\<sub\>Fox\<\/sub\>\<\/span\>'''\]\]/":[[r"""(\[\[User:AlexJFox\|'''<span[^\n]*?<\/span>)('''\]\])""", r"""\1</span>\2"""]],
    r"insource:/\'\'\'\'\'\[\[User\:Chill\ doubt\|\<span\ style\=\"background\:\#008\;color\:\#fff\"\>•C\<span\ style\=\"background\:\#206\"\>H\<span\ style\=\"background\:\#504\"\>ILL\<span\ style\=\"background\:\#702\"\>DO\<span\ style\=\"background\:\#a00\"\>UBT•\<\/span\>\<\/span\>\<\/span\>\<\/span\>\<\/span\>\]\]\'\'\'\ /":[[r"""('{5}\[\[User:Chill doubt\|[^\n]*\]\]''')(?!'')""", r"""\1''"""]],
    r"insource:/\[\[User:Linguisticgeek\|\<span style=\"color:\#AA22CC;\"\>Linguistic\<\/span\>\]\]'''\[\[User_ talk:Linguisticgeek\|\<span style=\"color:\#2B18BA;\"\>Geek\<\/span\>\]\][^']/":[[r"""(\[\[User:Linguisticgeek\|<span[^\n]*?\]\]'''[^\n]*?<\/span>\]\])(?!''')""", r"""\1'''"""]],
    r"insource:/\<\/small>\<p>\<\/div>\<\!\-\- Template:Blocked talk\-revoked\-notice \-\->/":[[r"""(<\/small>)<p>(<\/div><!-- Template:Blocked talk-revoked-notice -->)""", r"""\1\2"""]],

    # Obsolete center tags
    r"insource:/\<center>\<big>Please join us in[^\n]*?\<\/big>\<\/center>/":[[r"""<center>(<big>Please join us in[^\n]*?<\/big>)<\/center>""", r"""{{center|1=\1}}"""]],
    r"insource:/\<small\>\<center\>This message delivered by \[\[User:MediationBot/":[[r"""(<small>)<center>(This message delivered.*?directly\]\]\.)<\/center>(<\/small>)""", r"""{{center|1=\1\2\3}}"""]],
    r"insource:/\<center\>\nThis page is an archive and its contents should be preserved in their current form;\<br\>\nany comments regarding this page should be directed to \[\[Wikipedia talk:In the news\]\]\. Thanks.\n\<\/center\>/":[[r"""<center>([^\n]*?Thanks\.\n)<\/center>""", r"""<div class="center">\1</div>"""]],
    r"insource:/\<center>\[\[File:This month in GLAM/":[[r"""<center>(.*?\/Newsletter\]\])<\/center>""", r"""\1"""]],
    r"insource:/\<center\>\{\{Quote frame\|The City of Chula Vista Public Library does not advocate nor endorse the views or positions expressed by the users of its facilities.\|Chula Vista Public Library Meeting Room Policy\}\}\<\/center\>/":[[r"""<center>([^\n]*?Policy\}\})<\/center>""", r"""{{center|1=\1}}"""]],
    r"insource:/\<center\>\<small\>Got any suggestions\?/":[[r"""(<br \/>)<center>(<small>Got any suggestions\?[^\n]*?)<\/center>""", r"""\1{{center|1=\2}}"""]],
    r"insource:/featured picture\]\] status\'\'\'\<\/center\>/":[[r"""<center>(\[\[Image:Cscr-featured\.svg.*?)<\/center>""", r"""{{center|1=\1}}"""]],

    # Invalid font tags
    r"insource:/\<font *\= *[+\-\d]\d*\>/":[[r"""<font *\= *([+\-\d]\d*)\>""", r"""<font size="\1">"""]],
    r"insource:/\<font color\=\"color:/":[[r"""(<font color=")color:([^>"]*?">)""", r"""\1\2"""]],
    r"insource:/\<font family/":[[r"""(<font )family=""", r"""\1face="""]]
}
site = pywikibot.Site()

pages = []
bar = tqdm(total=len(regexes.keys()))
for search in regexes.keys():
    while True:
        bar.set_description(search)
        try:
            _ = [page.title() for page in site.search(search)]
            if len(_) <= 1:
                print("{}: 0 results excluding signature submissions page".format(search))
            pages += _
        except pywikibot.exceptions.APIError:
            sleep(10)
            continue
        else:
            bar.update(1)
            break

bar.close()
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
