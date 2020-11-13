from main import *

# region init
responsible_selected = responsible.select("11")
statuses = {"-3": "almost overdue",
            "-2": "not viewed",
            "-1": "overdue",
            "1": "new",
            "2": "pending",
            "3": "in progress",
            "4": "supposedly completed",
            "5": "completed",
            "6": "deferred",
            "7": "declined",}
# endregion

# https://training.bitrix24.com/rest_help/tasks/task/tasks/tasks_task_list.php
all_tasks = b24.smart_get("tasks.task.list",
                          {"filter":
                               {"RESPONSIBLE_ID": responsible_selected["ID"],
                                "!STATUS": ["4", "5", "6"],
                                },
                           "order":
                               {"REAL_STATUS": "DESC",
                                }
                           }
                          , verbose=False)

# region dev (delete after)
Print.prettify(all_tasks[0])
print()

for task in all_tasks:
    print(task['status'], statuses[task['status']], task['title'], generate_url_to_task(task))
    print()

print("total:", len(all_tasks))
# endregion