from main import *
from enum import Enum

# region init
responsible_selected = responsible.select("11")


class Actions(Enum):
    tpr = "print all tasks"
    ta = "add task"
    ts = "start task"
    tp = "pause task"
    td = "deffer task"
    tr = "resume deffered or closed task"
    tc = "close task"

    wpr = "show working time"
    ws = "start|resume working time"
    wp = "pause working time"
    wq = "quit working day"

    sd = "enable|disable deffered tasks"

    dptf = "debug: print all tasks fields"
    dpet = "debug: get elapsed time of task"
    dprt = "debug: print raw tasks"

    q = "quit"


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

# endregion


def get_all_tasks():
    return b24.smart_get("tasks.task.list",
                              {"filter":
                                   {"RESPONSIBLE_ID": responsible_selected["ID"],
                                    "!STATUS": bad_statuses,
                                    },
                               "order":
                                   {"REAL_STATUS": "DESC",
                                    }
                               }
                              , verbose=False)


def print_all_tasks():
    # https://training.bitrix24.com/rest_help/tasks/task/tasks/tasks_task_list.php
    all_tasks = get_all_tasks()
    in_progress = 0

    for cnt, task in enumerate(all_tasks):
        print(f"[{cnt}]", end=" ")
        Print.colored(statuses[task['status']], "green", end=" ")
        if statuses[task['status']] == "in progress":
            in_progress += 1
        print(task['title'], end=" ")
        if task['durationPlan'] is not None:
            if int(task['durationPlan']):
                Print.colored(f"{task['durationFact']} of {task['durationPlan']} {task['durationType']}", "yellow",
                              end=" ")
        Print.colored(newline + generate_url_to_task(task), "blue")
        if task['description']:
            print("описание:")
            print(task['description'])
        print("*" * Console.width())

    print("total:", len(all_tasks))
    Print.colored(in_progress, "tasks in progress", "red")
    return all_tasks


def print_all_actions():
    last_first_symbol = ""
    for e in Actions:
        if e.name[0] != last_first_symbol:
            print()
            last_first_symbol = e.name[0]
        Print.colored(f"[{e.name}]", "magenta", end="")
        print(f"\t{e.value}")
    print()


def print_working_time():
    print(get_working_time(responsible_selected["ID"]))

    timeman_out = timeman_status(responsible_selected["ID"])

    print(f"status: {timeman_out['STATUS'].lower()}")
    print(f"pauses: {timeman_out['TIME_LEAKS'].lower()}")


print_all_tasks()

while True:
    print_all_actions()

    try:
        action = Actions[Keyboard.translate_string(input("select action: "))]
    except KeyError:
        print("unknown action")
        continue
    try:
        if action == Actions.wpr:
            print_working_time()
        elif action == Actions.ws:
            start_working_time(responsible_selected["ID"])
            print_working_time()
        elif action == Actions.wp:
            pause_working_time(responsible_selected["ID"])
            for task in get_all_tasks():
                try:
                    pause_task(task['id'], verbose=True)
                except KeyError:
                    pass
            print_working_time()
        elif action == Actions.wq:
            try:
                stop_working_time(responsible_selected["ID"])
            except KeyError:
                pass
            for task in get_all_tasks():
                try:
                    pause_task(task['id'], verbose=True)
                except KeyError:
                    pass
            print_working_time()
        elif action == Actions.ts:

            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]
            # start task time
            # change task status to 3 (in progress)
            start_task(selected_task['id'])
            # move task to "Выполняется"
            change_task_stage(selected_task, 'Выполняются')
        elif action == Actions.dpet:

            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            Print.prettify(b24.smart_get("task.elapseditem.getlist", {"TASKID": selected_task['id']}))
        elif action == Actions.dptf:
            print_all_task_fields()
        elif action == Actions.q:
            import sys
            sys.exit()
        elif action == Actions.dprt:
            Print.prettify(get_all_tasks())
        elif action == Actions.tp:
            # pause task
            # change task to 2 pending
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            pause_task(selected_task['id'])
        elif action == Actions.td:
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            deffer_task(selected_task['id'])
            change_task_stage(selected_task, 'Новые')
        elif action == Actions.tc:
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            complete_task(selected_task['id'])
            change_task_stage(selected_task, 'На проверке')
        elif action == Actions.tr:
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            resume_task(selected_task['id'])
            change_task_stage(selected_task, 'На доработке')
        elif action == Actions.sd:
            if "6" in bad_statuses:
                bad_statuses.pop(bad_statuses.index("6"))
                print("show deffered tasks")
            else:
                bad_statuses.append("6")
                print("hide deffered tasks")
        elif action == Actions.ta:
            import add_task_interactive
            add_task_interactive.main()
        elif action == Actions.tpr:
            print_all_tasks()
        else:
            Print.colored("unknown command", "red")
    except KeyboardInterrupt:
        pass
