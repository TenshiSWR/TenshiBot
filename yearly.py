from tools.misc import get_database, load_task

tasks = [("tasks.wikicup_submissions", 8)]

db, cursor = get_database()
cursor.execute("UPDATE misc SET wikicup_round = 1, wikicup_judge_username = NULL;")
db.close()

for task in tasks:
    load_task(task[0], task[1])
