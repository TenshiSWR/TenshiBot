from tools.misc import load_task

tasks = [("reports.unlistedcopyrightproblems", "2U"),
         ("tasks.uncategorised_footballers", 11)]

for task in tasks:
    load_task(task[0], task[1])
