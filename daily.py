from tools import load_task

tasks = [["tasks.afcreviewinprogresschecker", 2]]

for task in tasks:
    load_task(task[0], task[1])
