import pywikibot
site = pywikibot.Site()
userspace_drafts = [userspace_draft for userspace_draft in pywikibot.Category(site, "Stale userspace drafts").articles()]
indeffed_user_drafts = {}
for userspace_draft in userspace_drafts:
    user = pywikibot.User(site, userspace_draft.title(with_ns=False).split("/")[0])
    if user.is_blocked():
        print(userspace_draft.title())
        user = user.username
        try:
            indeffed_user_drafts[user].append(userspace_draft.title())
        except KeyError:
            indeffed_user_drafts[user] = [userspace_draft.title()]


# Table format from User:AnomieBOT/Nobots Hall of Shame
report_page = pywikibot.Page(site, "User:TenshiBot/Stale userspace drafts by blocked users")
report_page.text = "\n".join(['{{/header}}',
                              '{| class="wikitable sortable" style="width:100%"',
                              '!Username!!Number of userspace drafts!!class="unsortable"|Pages\n'])
for username, pages in indeffed_user_drafts.items():
    if len(pages) > 5:
        report_page.text += "\n".join(["|-", f"| [[User:{username}|{username}]]", f"| {len(pages)}", "|{{hidden begin}}\n"])
        report_page.text += "\n".join(["* [[{}]]".format(page) for page in pages])+"\n"
        report_page.text += "{{hidden end}}\n"
    else:
        report_page.text += "\n".join(["|-", f"| [[User:{username}|{username}]]", f"| {len(pages)}", "|\n"])
        report_page.text += "\n".join(["* [[{}]]".format(page) for page in pages])+"\n"
report_page.text += "|}"
report_page.save(summary='[[User:TenshiBot#Tasks|Task 1U]]: Updating report "Stale userspace drafts by blocked users"', minor=False)

