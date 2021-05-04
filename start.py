import sys
from enum import Enum
from main import *

# region init
class Actions(Enum):
    tpr = "print all tasks"
    ta = "add task"
    ts = "start task"
    tp = "pause task"
    td = "deffer task"
    tr = "resume deferred or closed task"
    tc = "close task"

    tma = "task fact minutes add"
    tm = "task set fact minutes"

    wpr = "show working time"
    ws = "start|resume working time"
    wp = "pause working time"
    wq = "quit working day"

    sd = "show|hide deferred tasks"
    sdb = "show|hide config and debug options"

    dptf = "debug: print all tasks fields"
    dpet = "debug: get elapsed time of task"
    dprt = "debug: print raw tasks"

    configreset = "delete this script config and setup all again"
    csr = "set default responsible"
    csa = "set default auditor"
    csp = "set default project"
    csu = "set user (whose tasks will be shown)"
    ccr = "clean default responsible"
    cca = "clean default auditor"
    ccp = "clean default project"
    cch = "clear encrypted hook url"

    q = "quit"


def get_responsible_selected(reset=False):
    if reset:
        clear_config_value("responsible_to_filter_tasks")

    responsible_to_filter_tasks = responsible.select(get_config_value("responsible_to_filter_tasks"),
                                                     interactive_question="Select script user:")
    set_config_value("responsible_to_filter_tasks", responsible_to_filter_tasks['ID'])
    return responsible_to_filter_tasks


def get_all_tasks():
    tasks = b24.smart_get("tasks.task.list",
                          {"filter":
                               {"RESPONSIBLE_ID": get_responsible_selected()["ID"],
                                "!STATUS": bad_statuses,
                                },
                           # "order":
                           #    {# "REAL_STATUS": "DESC",
                           #        "DEADLINE": "DESC"
                           #     },
                           "select": list(get_all_tasks_fields().keys())
                           }
                          , verbose=True)

    def sort_date(input_date):
        if input_date is None:
            return "2099-04-30T19:00:00+05:00"
        else:
            return input_date

    tasks = List.sort_by(tasks, "deadline", "createdDate", cast_to=sort_date)

    tasks.reverse()

    return tasks


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
                Print.colored(f"", "yellow",
                          end=" ")
        if task['deadline'] is not None:
            Print.colored(task['deadline'], "red", end="")
        print()
        Print.colored(generate_url_to_task(task), "blue")
        # if task['description']:
        #    print("описание:")
        #    print(task['description'])
        print("*" * Console.width())

    print("total:", len(all_tasks))
    Print.colored(in_progress, "tasks in progress", "red")
    return all_tasks


def print_all_actions():
    last_first_symbol = ""
    for e in Actions:
        first_symbol = e.name[0]

        if e.name in debug_actions and not print_debug:
            continue

        if first_symbol != last_first_symbol:
            print()
            last_first_symbol = e.name[0]

        Print.colored(f"[{e.name}]", "magenta", end="")
        print(f"\t{e.value}")
    print()


def print_working_time():
    print(get_working_time(get_responsible_selected()["ID"]))

    timeman_out = timeman_status(get_responsible_selected()["ID"])

    print(f"status: {timeman_out['STATUS'].lower()}")
    print(f"pauses: {timeman_out['TIME_LEAKS'].lower()}")


statuses = {"-3": "almost overdue",
            "-2": "not viewed",
            "-1": "overdue",
            "1": "new",
            "2": "pending",
            "3": "in progress",
            "4": "supposedly completed",
            "5": "completed",
            "6": "deferred",
            "7": "declined", }
bad_statuses = ["4", "5", "6"]  # на подтверждении, завершено, отложено

print_debug = get_config_value("print_debug")

debug_actions = ["dptf", "dpet", "dprt", "configreset", "ccr", "cca", "ccp", "ccu", "cch",
                 "csr", "csa", "csp", "csu", "csh"]

# endregion
try:
    print_all_tasks()
except ConnectionError:
    if CLI.get_y_n("Wrong password! Do you want to reset hook and password?"):
        clear_config_value("hook_encrypted")
    sys.exit(0)

while True:
    print_all_actions()

    try:
        action = Actions[Keyboard.translate_string(input("select action: "))]
    except KeyError:
        print("unknown action")
        continue
    except KeyboardInterrupt:
        print("^C")
        sys.exit(0)
    try:
        if action == Actions.wpr:
            print_working_time()
        elif action == Actions.ws:
            start_working_time(get_responsible_selected()["ID"])
            print_working_time()
        elif action == Actions.wp:
            pause_working_time(get_responsible_selected()["ID"])
            for task in get_all_tasks():
                try:
                    pause_task(task['id'], verbose=True)
                except KeyError:
                    pass
            print_working_time()
        elif action == Actions.wq:
            try:
                stop_working_time(get_responsible_selected()["ID"])
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
        elif action == Actions.tma:
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            minutes_fact_before = selected_task[minutes_fact_get_name]

            minutes_fact_new = int(minutes_fact_before) + CLI.get_int(
                f"Минут факт (добавится к {minutes_fact_before}): ")

            update_task(selected_task['id'], {minutes_fact_set_name: minutes_fact_new})
        elif action == Actions.tm:
            all_tasks = print_all_tasks()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            minutes_fact = CLI.get_int("Минут факт (заменится на это значение): ")

            update_task(selected_task['id'], {minutes_fact_set_name: minutes_fact})

        elif action == Actions.configreset:
            File.delete(config_path)
            print("config file deleted")
        elif action == Actions.sdb:
            print_debug = not bool(print_debug)
            set_config_value("print_debug", print_debug)

        elif action == Actions.csr:
            selected_responsible = responsible.select(interactive_question="Выберите ответственного")
            set_config_value("default_responsible", selected_responsible["ID"])
        elif action == Actions.csa:
            selected_auditor = auditors.select(interactive_question="Выберите наблюдателя")
            set_config_value("default_auditor", selected_auditor["ID"])
        elif action == Actions.csp:
            selected_project = projects.select(interactive_question="Выберите проект")
            set_config_value("default_project", selected_project["ID"])
        elif action == Actions.csu:
            get_responsible_selected(reset=True)

        elif action == Actions.ccr:
            clear_config_value("default_responsible")
        elif action == Actions.cca:
            clear_config_value("default_auditor")
        elif action == Actions.ccp:
            clear_config_value("default_project")
        elif action == Actions.cch:
            clear_config_value("hook_encrypted")
            sys.exit(0)
        else:
            Print.colored("unknown command", "red")
    except KeyboardInterrupt:
        pass
