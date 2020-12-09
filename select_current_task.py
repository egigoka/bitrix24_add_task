from main import *

# region init
responsible_selected = responsible.select("11")
# endregion

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
bad_statuses = ["4", "5", "6"]  # на подтверждении, завершено, отложено


# https://training.bitrix24.com/rest_help/tasks/task/tasks/tasks_task_list.php
all_tasks = b24.smart_get("tasks.task.list",
                          {"filter":
                               {"RESPONSIBLE_ID": responsible_selected["ID"],
                                "!STATUS": bad_statuses,
                                },
                           "order":
                               {"REAL_STATUS": "DESC",
                                }
                           }
                          , verbose=False)

# region dev (delete after)
# Print.prettify(all_tasks)
# print()

print_all_task_fields()

for cnt, task in enumerate(all_tasks):
    print(f"[{cnt}]", end=" ")
    Print.colored(statuses[task['status']], "green", end=" ")
    print(task['title'], end=" ")
    if task['durationPlan'] is not None:
        if int(task['durationPlan']):
            Print.colored(f"{task['durationFact']} of {task['durationPlan']} {task['durationType']}", "yellow", end=" ")
    Print.colored(newline + generate_url_to_task(task), "blue")
    if task['description']:
        print("описание:")
        print(task['description'])
    print("*" * Console.width())

print("total:", len(all_tasks))

print(get_working_time(responsible_selected["ID"]))

OS.exit(0)

selected_task_int = CLI.get_int("Select task")
selected_task = all_tasks[selected_task_int]

for task in all_tasks:
    if task == selected_task:
        start_task(selected_task['id'])
        change_task_stage(task, 'Выполняются')
    else:
        pass

# endregion

# todo: pause working time
# todo: resume working time
# todo: start working time
# todo: stop working time

# todo: start task time
# todo: change task to 3 in progress

# todo: stop task
# todo: change task to 2 pending

# todo: move task to supervision
# todo: change task to 4 need checking
# todo: move task to На проверке

# todo: move working task to Выполняется
# todo: move done task to На проверке или Сделаны

# todo: pause working time and pause task and and move it to Новые