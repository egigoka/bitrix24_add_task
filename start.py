import sys
from enum import Enum
from main import *

# region init
class Actions(Enum):
    t = "print all tasks"
    ta = "add task"
    ts = "start task"
    tp = "pause task"
    td = "deffer task"
    tr = "resume deferred or closed task"
    tc = "close task"

    tma = "task fact minutes add"
    tm = "task set fact minutes"

    w = "show working time"
    ws = "start|resume working time"
    wp = "pause working time"
    wq = "quit working day"

    sd = "show|hide deferred tasks"
    sn = "show|hide not in progress tasks"
    si = "show|hide not important tasks"
    sde = "show|hide description of tasks"
    sdb = "show|hide config and debug options"

    dptf = "debug: print all tasks fields"
    dpet = "debug: get elapsed time of task"
    dt = "debug: print raw tasks"

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
    filter_ = {"RESPONSIBLE_ID": get_responsible_selected()["ID"],
               "!REAL_STATUS": bad_statuses,}
    if hide_not_important:
        filter_["PRIORITY"] = [2]
    verbose = False
    tasks = b24.smart("tasks.task.list",
                      {"filter": filter_,
                           # "order":
                           #    {# "REAL_STATUS": "DESC",
                           #        "DEADLINE": "DESC"
                           #     },
                           "select": list(get_all_tasks_fields().keys())
                           }
                      , verbose=verbose)

    def sort_date(input_date):
        if input_date is None:
            return "2099-04-30T19:00:00+05:00"
        else:
            return input_date

    tasks = List.sort_by(tasks, "deadline", "createdDate", cast_to=sort_date)

    tasks.reverse()

    return tasks


def html_deescape(string):
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
        }
    for sym, esc in html_escape_table.items():
        string = string.replace(esc, sym)
    return string


def format_time(string, show_time=False):  # YYYY-MM-DD?HH:mm:SS+??:??
    show_year = False
    if Time.datetime().month == 1:
        show_year = True
    year = string[:4]
    month = string[5:7]
    day = string[8:10]
    hour = string[11:13]
    minute = string[14:16]
    second = string[17:19]
    output = f"{day}.{month}"
    if show_year:
        output += f".{year}"
    if show_time:
        output += f" {hour}:{minute}"
    return output


def print_all_tasks():
    # https://training.bitrix24.com/rest_help/tasks/task/tasks/tasks_task_list.php
    all_tasks = get_all_tasks()

    in_progress = 0

    print("*" * Console.width())
    for cnt, task in enumerate(all_tasks):
        print(f"[{cnt}]", end=" ")
        Print.colored(statuses[task['subStatus']], "green", end=" ")
        print(task['title'], end=" ")
        if task['durationPlan'] is not None:
            if int(task['durationPlan']):
                Print.colored(f"", "yellow",
                          end="")
        if task['deadline'] is not None:
            Print.colored(format_time(task['deadline']), "red", end=" ", sep="")
        Print.colored(f"{task[minutes_fact_get_name]} of {task[minutes_plan_get_name]}", "magenta", end=' ')
        Print.colored(f"{task['creator']['name']}", "green", end='')
        print()
        Print.colored(generate_url_to_task(task), "blue")
        if not hide_task_descriptions:
            if task['description']:
                print("описание:")
                print(html_deescape(task['description']))
        print("*" * Console.width())

    print("total:", len(all_tasks))
    return all_tasks


def print_all_actions():
    print_debug = get_config_value("print_debug")
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
    timeman_out = timeman_status(get_responsible_selected()["ID"])
    time = str(get_working_time(get_responsible_selected()["ID"]))
    status = timeman_out['STATUS'].lower()
    pauses = timeman_out['TIME_LEAKS'].lower()

    if len(time) == 14:
        time = time[:-7]
    if len(time) == 7:
        time = time[:-3]

    if len(pauses) == 8:
        pauses = pauses[:-3]
    if pauses.startswith("0"): # remove first 0
        pauses = pauses[1:]

    print(f"{time} [{status}] pauses: {pauses}")


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
if bool(get_config_value("hide not in progress tasks")):
    bad_statuses.append("1")
    bad_statuses.append("2")

hide_not_important = bool(get_config_value("hide not important tasks"))
hide_task_descriptions = bool(get_config_value("hide tasks destriptions"))

debug_actions = ["dptf", "dpet", "dt", "configreset", "ccr", "cca", "ccp", "ccu", "cch",
                 "csr", "csa", "csp", "csu", "csh"]

# endregion

def main():
    global bad_statuses
    global hide_not_important
    global hide_task_descriptions

    print_all_actions()

    try:
        input_str = input("select action: ")
        input_str_translated = Keyboard.translate_string(input_str)
        if input_str != input_str_translated:
            print(f"> {input_str_translated}")
        action = Actions[input_str_translated]
    except KeyError:
        print("unknown action")
        return
    except KeyboardInterrupt:
        print("^C")
        OS.exit(0)
    try:
        if action == Actions.w:
            print_working_time()
        elif action == Actions.ws:
            start_working_time(get_responsible_selected()["ID"])
            print_working_time()
        elif action == Actions.wp:
            pause_working_time(get_responsible_selected()["ID"])
            # for task in get_all_tasks():
            #     try:
            #         pause_task(task['id'], verbose=True)
            #     except KeyError:
            #         pass
            print_working_time()
        elif action == Actions.wq:
            try:
                stop_working_time(get_responsible_selected()["ID"])
            except KeyError:
                pass
            # for task in get_all_tasks():
            #     try:
            #         pause_task(task['id'], verbose=True)
            #     except KeyError:
            #         pass
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

            Print.prettify(b24.smart("task.elapseditem.getlist", {"TASKID": selected_task['id']}))
        elif action == Actions.dptf:
            print_all_task_fields()
        elif action == Actions.q:
            import sys

            sys.exit()
        elif action == Actions.dt:
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
                print_all_tasks()
                print("show deffered tasks")
            else:
                bad_statuses.append("6")
                print_all_tasks()
                print("hide deffered tasks")
        elif action == Actions.sn:
            if "1" in bad_statuses \
            or "2" in bad_statuses:
                bad_statuses.pop(bad_statuses.index("1"))
                bad_statuses.pop(bad_statuses.index("2"))
                set_config_value("hide not in progress tasks", False)
                print_all_tasks()
                print("show not in progress tasks")
            else:
                bad_statuses.append("1")
                bad_statuses.append("2")
                set_config_value("hide not in progress tasks", True)
                print_all_tasks()
                print("hide not in progress tasks")
        elif action == Actions.si:
            hide_not_important = not hide_not_important
            set_config_value("hide not important tasks", hide_not_important)
            print_all_tasks()
            print(f"{hide_not_important=}")
        elif action == Actions.sde:
            hide_task_descriptions = not hide_task_descriptions
            set_config_value("hide tasks destriptions", hide_task_descriptions)
            print_all_tasks()
            print(f"{hide_task_descriptions=}")
        elif action == Actions.ta:
            import add_task_interactive

            add_task_interactive.main()
        elif action == Actions.t:
            print_all_tasks()
        elif action == Actions.tma:
            all_tasks = print_all_tasks()
            print_working_time()
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
            set_config_value("print_debug", not bool(get_config_value("print_debug")))

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
            Print.colored("no action assigned to this action", "red")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        print_all_tasks()
    except ConnectionError:
        if CLI.get_y_n("Wrong password! Do you want to reset hook and password?"):
            clear_config_value("hook_encrypted")
        sys.exit(0)
    
    while True:
        main()
