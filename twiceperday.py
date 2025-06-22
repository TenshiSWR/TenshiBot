from tools import load_task

tasks = [["tasks.rmtr", 1]]

for task in tasks:
    load_task(task[0], task[1])
