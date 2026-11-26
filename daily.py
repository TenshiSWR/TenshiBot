from datetime import datetime
from tools.misc import load_task

tasks = [("tasks.afcreviewinprogresschecker", 2),
         ("tasks.signature_submissions", 13)]
if datetime(datetime.utcnow().year, 1, 2) <= datetime.utcnow() <= datetime(datetime.utcnow().year, 10, 31):
    tasks.append(("tasks.wikicup_submissions", 8))

for task in tasks:
    load_task(task[0], task[1])
