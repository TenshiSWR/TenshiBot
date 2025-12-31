from tools.misc import load_task

tasks = [("tasks.afcreviewinprogresschecker", 2),
         ("tasks.wikicup_submissions", 8)]

for task in tasks:
    load_task(task[0], task[1])
