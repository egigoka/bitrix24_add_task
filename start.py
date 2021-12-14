import datetime
import pprint
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

    tm = "task time spent add"

    rtt = "report: today time by tasks"
    rty = "report: yesterday time by tasks"
    rtm = "report: month time by tasks"

    w = "show working time"
    ws = "start|resume working time"
    wp = "pause working time"
    wq = "quit working day"

    sd = "show|hide deferred tasks"
    sn = "show|hide not in progress tasks"
    si = "show|hide not important tasks"
    sde = "show|hide description of tasks"
    sdb = "show|hide config and debug options"

    ha = "holiday add"

    dptf = "debug: print all tasks fields"
    dpet = "debug: get elapsed time of task"
    dt = "debug: print raw tasks"

    configreset = "delete this script config and setup all again"
    csr = "set default responsible"
    caa = "add default auditor"
    csp = "set default project"
    csu = "set user (whose tasks will be shown)"
    ccr = "clean default responsible"
    cra = "remove default auditor"
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


def get_all_tasks(filters_enabled=True):
    filter_ = {}
    if filters_enabled:
        filter_ = {"RESPONSIBLE_ID": get_responsible_selected()["ID"],
                   "!REAL_STATUS": bad_statuses, }
        if hide_not_important:
            filter_["PRIORITY"] = [2]
    verbose = False
    tasks = b24.smart("tasks.task.list",
                      {"filter": filter_,
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
    if pauses.startswith("0"):  # remove first 0
        pauses = pauses[1:]

    print(f"{time} [{status}] pauses: {pauses}")


def seconds_to_human_time(seconds_int):
    symbol = "-" if seconds_int < 0 else ""
    seconds_int = abs(seconds_int)
    minutes_total = seconds_int // 60
    seconds_left = seconds_int % 60
    hours_total = minutes_total // 60
    minutes_left = minutes_total % 60

    return f"{symbol}{int(hours_total)}:{str(int(minutes_left)).zfill(2)}:{str(int(seconds_left)).zfill(2)}"


def string_to_date(string):
    import datetime
    return datetime.datetime.strptime(string, "%d.%m.%Y")


def date_to_string(date):
    return date.strftime("%d.%m.%Y")


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

debug_actions = ["dptf", "dpet", "dt", "configreset",
                 "ccr", "cra", "ccp", "ccu", "cch",
                 "csr", "caa", "csp", "csu", "csh"]


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
        elif action == Actions.tm:
            all_tasks = print_all_tasks()
            # print_working_time()
            selected_task_int = CLI.get_int("Select task")
            selected_task = all_tasks[selected_task_int]

            print(f"Selected task: '{selected_task['title']}'")

            minutes = CLI.get_int("How many minutes")
            comment_text = input("Comment? ")

            add_time_to_task(task_id=selected_task["id"], seconds=minutes*60,
                             comment_text=comment_text)

        elif action == Actions.configreset:
            File.delete(config_path)
            print("config file deleted")
        elif action == Actions.sdb:
            set_config_value("print_debug", not bool(get_config_value("print_debug")))

        elif action == Actions.csr:
            selected_responsible = responsible.select(interactive_question="Выберите ответственного")
            set_config_value("default_responsible", selected_responsible["ID"])
        elif action == Actions.caa:
            selected_auditor = auditors.select(interactive_question="Выберите добавляемого наблюдателя")
            auditors_current = get_config_value("default_auditor")

            if isinstance(auditors_current, str):
                auditors_current = [auditors_current]
                set_config_value("default_auditor", auditors_current)
            elif auditors_current is None:
                auditors_current = []
                set_config_value("default_auditor", auditors_current)

            if selected_auditor['ID'] not in auditors_current:
                auditors_current.append(selected_auditor["ID"])

            set_config_value("default_auditor", auditors_current)
        elif action == Actions.csp:
            selected_project = projects.select(interactive_question="Выберите проект")
            set_config_value("default_project", selected_project["ID"])
        elif action == Actions.csu:
            get_responsible_selected(reset=True)
        elif action == Actions.ccr:
            clear_config_value("default_responsible")
        elif action == Actions.cra:
            auditors_current = get_config_value("default_auditor")
            if isinstance(auditors_current, str):
                auditors_current = [auditors_current]
                set_config_value("default_auditor", auditors_current)
            elif auditors_current is None:
                auditors_current = []
                set_config_value("default_auditor", auditors_current)

            if len(auditors_current) != 0:
                try:
                    auditors_current.remove(auditors.select(interactive_question="Выберите наблюдателя для удаления",
                                                            highlighted_objects_ids=auditors_current)["ID"])
                except ValueError:
                    pass
                set_config_value("default_auditor", auditors_current)

                if len(auditors_current) == 0:
                    set_config_value("default_auditor", [])
            else:
                print("nothing to remove")
        elif action == Actions.ccp:
            clear_config_value("default_project")
        elif action == Actions.cch:
            clear_config_value("hook_encrypted")
            OS.exit(0)
        elif action == Actions.rtt:
            date_today = Time.datetime()
            result = b24.smart("task.elapseditem.getlist",
                               {"ORDER":
                                    {"ID": "DESC"},
                                "FILTER":
                                    {"USER_ID": get_config_value("responsible_to_filter_tasks"),
                                     ">=CREATED_DATE": f"{date_today.year}-"
                                                       f"{str(date_today.month).zfill(2)}-"
                                                       f"{str(date_today.day).zfill(2)}"}
                                },
                               verbose=False,
                               post=True)
            seconds_total = 0

            today_tasks = {}

            for time_entry in result:
                task_id = time_entry['TASK_ID']
                if task_id in today_tasks:
                    today_tasks[task_id]['SECONDS'] = int(today_tasks[task_id]['SECONDS']) + int(time_entry['SECONDS'])
                    if today_tasks[task_id]['COMMENT_TEXT'] and time_entry['COMMENT_TEXT'] != "":
                        today_tasks[task_id]['COMMENT_TEXT'] += "; "
                    today_tasks[task_id]['COMMENT_TEXT'] += time_entry['COMMENT_TEXT']
                else:
                    today_tasks[task_id] = time_entry
                # print(seconds_to_human_time(int(time_entry['SECONDS'])), time_entry['TASK_ID'])

            today_tasks = List.sort_by(list(today_tasks.values()), 'SECONDS', cast_to=int)

            for time_entry in today_tasks:
                task = get_object_with_caching("tasks.task.list", time_entry['TASK_ID'])
                task_human_string = f'{task["title"]}'
                # user = get_object_with_caching("user.get", time_entry['USER_ID'])
                # user_human_string = f'{user["NAME"]} {user["LAST_NAME"]}'
                comment = ""
                if len(time_entry['COMMENT_TEXT'].strip()) > 0:
                    comment = ", comment: " + time_entry['COMMENT_TEXT']
                seconds_human = seconds_to_human_time(int(time_entry['SECONDS']))
                seconds_human = Print.colored(seconds_human, "green", verbose=False)
                print(f"{seconds_human} {task_human_string}{comment}")
                Print.colored(generate_url_to_task(task), "blue")
                seconds_total += int(time_entry['SECONDS'])

            # debug
            print()
            print(f"Total: {seconds_to_human_time(seconds_total)}")

            current_time = Time.datetime()
            rest_start = Time.datetime().replace(hour=12, minute=30, second=0, microsecond=0)
            rest_end = Time.datetime().replace(hour=13, minute=30, second=0, microsecond=0)
            if rest_start < current_time < rest_end:
                current_time = rest_start

            working_day_start = Time.datetime().replace(hour=8, minute=0, second=0, microsecond=0)
            current_needed_time = Time.delta(current_time, working_day_start)
            if current_time > rest_end:
                current_needed_time -= Time.delta(rest_start, rest_end)

            max_needed_time = Time.delta(working_day_start,
                                         Time.datetime().replace(hour=17, minute=0, second=0, microsecond=0)) - \
                              Time.delta(rest_start, rest_end)

            if current_needed_time > max_needed_time:
                current_needed_time = max_needed_time

            print(f"Current needed time: {seconds_to_human_time(current_needed_time)}")

            difference = seconds_to_human_time(seconds_total - current_needed_time)
            symbol = "+" if seconds_total > current_needed_time else ""
            color = "green" if seconds_total > current_needed_time else "red"
            Print.colored(f"Difference: {symbol}{difference}", color)
        elif action == Actions.rty:
            import datetime
            date_yesterday = Time.datetime() - datetime.timedelta(days=1)
            date_today = Time.datetime()
            result = b24.smart("task.elapseditem.getlist",
                               {"ORDER":
                                    {"ID": "DESC"},
                                "FILTER":
                                    {"USER_ID": get_config_value("responsible_to_filter_tasks"),
                                     ">=CREATED_DATE": f"{date_yesterday.year}-"
                                                       f"{str(date_yesterday.month).zfill(2)}-"
                                                       f"{str(date_yesterday.day).zfill(2)}",
                                     "<CREATED_DATE": f"{date_today.year}-"
                                                      f"{str(date_today.month).zfill(2)}-"
                                                      f"{str(date_today.day).zfill(2)}"
                                     }
                                },
                               verbose=False,
                               post=True)
            seconds_total = 0

            today_tasks = {}

            for time_entry in result:
                task_id = time_entry['TASK_ID']
                if task_id in today_tasks:
                    today_tasks[task_id]['SECONDS'] = int(today_tasks[task_id]['SECONDS']) + int(time_entry['SECONDS'])
                    if today_tasks[task_id]['COMMENT_TEXT'] != "":
                        today_tasks['COMMENT_TEXT'] += "|||"
                    today_tasks[task_id]['COMMENT_TEXT'] += time_entry['COMMENT_TEXT']
                else:
                    today_tasks[task_id] = time_entry

            today_tasks = List.sort_by(list(today_tasks.values()), 'SECONDS', cast_to=int)

            for time_entry in today_tasks:
                task = get_object_with_caching("tasks.task.list", time_entry['TASK_ID'])
                task_human_string = f'{task["title"]}'
                # user = get_object_with_caching("user.get", time_entry['USER_ID'])
                # user_human_string = f'{user["NAME"]} {user["LAST_NAME"]}'
                comment = ""
                if len(time_entry['COMMENT_TEXT'].strip()) > 0:
                    comment = ", comment: " + time_entry['COMMENT_TEXT']
                seconds_human = seconds_to_human_time(int(time_entry['SECONDS']))
                seconds_human = Print.colored(seconds_human, "green", verbose=False)
                print(f"{seconds_human} {task_human_string}{comment}")
                Print.colored(generate_url_to_task(task), "blue")
                seconds_total += int(time_entry['SECONDS'])

            # debug
            print()
            print(f"Total: {seconds_to_human_time(seconds_total)}")

            working_day_start = Time.datetime().replace(hour=8, minute=0, second=0, microsecond=0)
            working_day_end = Time.datetime().replace(hour=17, minute=0, second=0, microsecond=0)
            rest_start = Time.datetime().replace(hour=12, minute=30, second=0, microsecond=0)
            rest_end = Time.datetime().replace(hour=13, minute=30, second=0, microsecond=0)
            current_needed_time = Time.delta(working_day_start, working_day_end) \
                                  - Time.delta(rest_start, rest_end)
            print(f"Needed time: {seconds_to_human_time(current_needed_time)}")

            difference = seconds_to_human_time(seconds_total - current_needed_time)
            symbol = "+" if seconds_total > current_needed_time else ""
            color = "green" if seconds_total > current_needed_time else "red"
            Print.colored(f"Difference: {symbol}{difference}", color)
        elif action == Actions.rtm:
            import datetime
            counter = 1
            seconds_total = 0
            seconds_needed = 0
            while True:
                try:
                    date = Time.datetime().replace(day=counter)
                except ValueError:
                    break
                date_end_filter = date + datetime.timedelta(days=1)
                now = Time.datetime()
                today_day = now.day

                if date.day == today_day+1:
                    break

                holidays = get_config_value("holidays")
                if not isinstance(holidays, dict):
                    holidays = {}
                    set_config_value("holidays", holidays)

                if date_to_string(date) in holidays.keys():
                    seconds_needed += holidays[date_to_string(date)] * 60 * 60
                elif date.weekday() in range(5):
                    seconds_needed += 8*60*60

                counter += 1

                result = b24.smart("task.elapseditem.getlist",
                                   {"ORDER":
                                        {"ID": "DESC"},
                                    "FILTER":
                                        {"USER_ID": get_config_value("responsible_to_filter_tasks"),
                                         ">=CREATED_DATE": f"{date.year}-"
                                                           f"{str(date.month).zfill(2)}-"
                                                           f"{str(date.day).zfill(2)}",
                                         "<CREATED_DATE": f"{date_end_filter.year}-"
                                                          f"{str(date_end_filter.month).zfill(2)}-"
                                                          f"{str(date_end_filter.day).zfill(2)}"
                                         }
                                    },
                                   verbose=False,
                                   post=True)
                seconds = 0

                for time_entry in result:
                    seconds += int(time_entry['SECONDS'])

                seconds_total += seconds
                diff = seconds_total - seconds_needed
                print(f"{date.strftime('%d.%m')} total: ", end="")
                Print.colored(f"{seconds_to_human_time(seconds)}", "magenta", end="")
                Print.colored(f" {seconds_to_human_time(diff)}", "red" if diff < 0 else "green")
            print(f"GRAND TOTAL:  {seconds_to_human_time(seconds_total)}")
            print(f"total needed: {seconds_to_human_time(seconds_needed)}")
            Print.colored(f"result:       {seconds_to_human_time(diff)}", "red" if diff < 0 else "green")
        elif action == Actions.ha:
            holidays = get_config_value("holidays")
            if not isinstance(holidays, dict):
                holidays = {}
                set_config_value("holidays", holidays)

            date = CLI.get_date("", always_return_date=False)

            if date is not None:
                date_str = date_to_string(date)
                holidays[date_str] = CLI.get_int("How many hours?")
                set_config_value("holidays", holidays)


        else:
            Print.colored("no action assigned to this action", "red")
    except KeyboardInterrupt:
        pass


# cache TODO: move to top

cache = {}


def get_object_with_caching(call, id):
    if call in cache:
        if id in cache[call]:
            # print("hit", call, id)
            return cache[call][id]
    else:
        cache[call] = {}

    arguments = {"filter": {"ID": id}}
    result = b24.smart(call, arguments)[0]

    cache[call][id] = result

    # print("miss", call, id)
    return result


# cache END TODO: move to top

if __name__ == "__main__":
    try:
        print_all_tasks()
    except ConnectionError:
        if CLI.get_y_n("Wrong password! Do you want to reset hook and password?"):
            clear_config_value("hook_encrypted")
        sys.exit(0)

    while True:
        main()
