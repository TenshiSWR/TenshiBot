from tools.misc import load_task

tasks = [("tasks.rmtr", 1),
         ("tasks.drnarchivetags", 10)]

for task in tasks:
    load_task(task[0], task[1])
