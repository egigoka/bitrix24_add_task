from enum import Enum
from typing import Any, Union
from bitrix24api import BitrixRESTAPI
from commands import *

# region development functions (temp)
def print_all_task_fields():
    fields = b24.smart_get("tasks.task.getfields")

    for name, desc in fields.items():
        print(name)
        for name_desc, value in desc.items():
            print(f"\t{name_desc}: {value}")
# endregion

def get_config_value(parameter):
    config = JsonDict("config.json")
    try:
        return config[parameter]
    except KeyError:
        return None

# region funcs tasks
def create_task(title, created_by, responsible_id, project_id, description, auditors):
    return b24.smart_get("tasks.task.add",
                         {"fields":
                              {"TITLE": title,
                               "CREATED_BY": created_by,
                               "RESPONSIBLE_ID": responsible_id,
                               "DESCRIPTION": description,
                               "GROUP_ID": project_id,
                               "AUDITORS": auditors}
                          }
                         )


def add_comment_to_task(task_id, comment_text, verbose = False):
    response = b24.post('task.commentitem.add', [task_id, {'POST_MESSAGE': comment_text}])
    if verbose:
        print(f"added comment {response['result']}: {comment_text}")
    return response


def add_multiple_comments_to_task_interactive(task_id, verbose=False):
    while True:
        comment = input("Введите комментарий: ")
        if comment:
            add_comment_to_task(task_id=task_id, comment_text=comment, verbose=verbose)
        else:
            print()
            return


def complete_task(task_id, verbose=False):
    response = b24.get("tasks.task.complete", {"taskId": task_id})
    if verbose:
        print(f"task {task_id} completed")
    return response


def start_task(task_id, verbose=False):
    response = b24.smart_get("tasks.task.start", {"taskId": task_id})
    if verbose:
        print(f"task {task_id} started")
    return response


def deffer_task(task_id, verbose=False):
    response = b24.smart_get("tasks.task.deger", {"taskId": task_id})
    if verbose:
        print(f"task {task_id} deffered")
    return response


def pause_task(task_id, verbose=False):
    response = b24.smart_get("tasks.task.pause", {"taskId": task_id})
    if verbose:
        print(f"task {task_id} paused")
    return response


def resume_task(task_id, verbose=False):
    response = b24.smart_get("tasks.task.renew", {"taskId": task_id})
    if verbose:
        print(f"task {task_id} resumed")
    return response


def change_task_stage(task_obj, new_stage_name, verbose=False):
    task_id = task_obj['id']
    stages = b24.smart_get("task.stages.get", {"entityId": task_obj['group']['id']})

    new_stage_id = None
    for id, stage_info in stages.items():
        if stage_info['TITLE'] == new_stage_name:
            new_stage_id = id
            break

    if new_stage_id is None:
        Print.prettify(stages)
        raise KeyError("task stage id not found")
    else:
        b24.smart_get("task.stages.movetask", {"id": task_id, "stageId": new_stage_id})
        if verbose:
            print(f"task {task_id} moved to stage: {new_stage_id} Выполняется")


def task_change_responsible(task_id, new_responsible_id):
    return b24.get("tasks.task.update", {"taskId": task_id, 'FIELDS': {"RESPONSIBLE_ID": new_responsible_id}})


def generate_url_to_task(task):
    return f"https://{Network.get_domain_of_url(hook)}/company/personal/user/{task['responsibleId']}/tasks/task/view/{task['id']}/"
# endregion

# region funcs working time


def timeman_to_datetime(time_string):
    import datetime
    return datetime.datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S%z")


def get_working_time(user_id):
    import datetime

    tm_status = timeman_status(user_id)
    time_start = tm_status["TIME_START"]
    skipped_time = tm_status['TIME_LEAKS']
    time_finish = tm_status['TIME_FINISH']

    time_start = timeman_to_datetime(time_start)

    if time_finish:
        time_finish = timeman_to_datetime(time_finish)
    else:
        from tzlocal import get_localzone
        time_now = datetime.datetime.now(tz=get_localzone())
        time_finish = time_now

    working_time = time_finish - time_start

    skiped_time = datetime.timedelta(hours=int(skipped_time[0:2]),
                                     minutes=int(skipped_time[3:5]),
                                     seconds=int(skipped_time[6:8]))

    return working_time - skiped_time


def timeman_status(user_id):
    return b24.smart_get("timeman.status", {"USER_ID": user_id})
def start_working_time(user_id):
    return b24.smart_get("timeman.open", {"USER_ID": user_id})
def stop_working_time(user_id):
    return b24.smart_get("timeman.close", {"USER_ID": user_id})
def pause_working_time(user_id):
    return b24.smart_get("timeman.pause", {"USER_ID": user_id})

# endregion

# region enums caching
class CacheType(Enum):
    dict = JsonDict
    list = JsonList
    json = Json


class CachesNames(Enum):
    created_by = "created_by"
    created_by_usage = "created_by_usage"
    responsible = "responsible"
    responsible_usage = "responsible_usage"
    auditor = "auditor"
    auditor_usage = "auditor_usage"
    projects = "projects"
    projects_usage = "projects_usage"
# endregion

# region funcs caching
def get_cache_filepath(name: str) -> str:
    # {/path/to/this/script}/cache/{name}.json
    return Path.combine(Path.get_parent(Path.safe__file__(__file__)),
                        "cache",
                        f"{name}.json")


def get_cache(name: str, days_valid: int, cache_type: CacheType) -> (bool, Union[Json, JsonList, JsonDict]):
    filepath = get_cache_filepath(name=name)
    file_exist = File.exist(filepath)

    # read or create cache file
    cached_result = cache_type.value(filepath)

    # check if cache out of date
    file_modified_time = File.get_modification_time(filepath)
    timestamp_now = Time.stamp()
    time_delta = timestamp_now - file_modified_time
    time_delta_max = days_valid * 24 * 60 * 60
    cache_valid = time_delta < time_delta_max and file_exist

    return cache_valid, cached_result
# endregion

class BitrixObjects:
    def __init__(self, cache_objects_name: str, cache_usage_name: str,
                 cache_objects_update_call: str, cache_objects_update_args: dict,
                 interactive_selection_sort_by: list, interactive_selection_cast_to: list,
                 cache_objects_days_valid: int = 1, cache_usage_days_valid: int = 30):
        self.cache_objects_name = cache_objects_name
        self.cache_usage_name = cache_usage_name
        self.cache_objects_days_valid = cache_objects_days_valid
        self.cache_usage_days_valid = cache_usage_days_valid
        self.cache_objects_update_call = cache_objects_update_call
        self.cache_objects_update_args = cache_objects_update_args
        self.interactive_selection_sort_by = interactive_selection_sort_by
        self.interactive_selection_cast_to = interactive_selection_cast_to

    def get_all(self) -> JsonDict:
        cache_valid, cached_result = get_cache(self.cache_objects_name,
                                               self.cache_objects_days_valid,
                                               CacheType.dict)
        if not cache_valid:
            objects = b24.smart_get(self.cache_objects_update_call,
                                    self.cache_objects_update_args,
                                    verbose=False)
            output = List.sort_by(objects, "ID", cast_to=[int])
            output = List.enum_by(output, "ID", cast_to=[int])
            cached_result.string = output
            cached_result.save()

        return cached_result

    def get_usage(self):
        cache_valid, cached_result = get_cache(self.cache_usage_name,
                                               self.cache_usage_days_valid,
                                               CacheType.dict)
        if not cache_valid:
            cached_result.string = {}
            cached_result.save()

        return cached_result

    def get_sorted_usage(self):
        usage = self.get_usage()
        sorted_usage = {k: v for k, v in sorted(usage.items(),
                                                key=lambda item: item[1],
                                                reverse=True)}
        return sorted_usage

    def get_all_except_used(self):
        all = self.get_all()
        usage = self.get_usage()

        for object_id, last_used_timestamp in usage.items():
            all.pop(object_id)

        return all

    def save_selection(self, id):
        usage = self.get_usage()
        id = int(id)

        usage[id] = Time.stamp()
        usage.save()

    def select(self, selected_id: int = None, interactive_question: str = "Выберите") -> dict:
        objects = self.get_all()

        if selected_id is not None:  # if not interactive
            self.save_selection(selected_id)
            return objects[selected_id]
        else:
            usage = self.get_sorted_usage()
            enumerated_dict = {}
            cnt = 0

            sorted_objects = []
            for object_id, last_used_timestamp in usage.items():
                try:
                    sorted_objects.append(objects[object_id])
                except KeyError:
                    pass

            sorted_objects += List.sort_by(list(objects.values()),
                                           *self.interactive_selection_sort_by,
                                           cast_to=self.interactive_selection_cast_to)

            list_for_print = []

            for object_info in sorted_objects:
                to_print = f"[{cnt}] "
                for key_sort in self.interactive_selection_sort_by:
                    to_print += f"{object_info[key_sort]} "
                list_for_print.insert(0, to_print)

                enumerated_dict[cnt] = object_info

                cnt += 1

            for cnt, line in enumerate(list_for_print):
                if cnt >= len(objects):
                    Print.colored(line, "on_white")
                else:
                    print(line)
            # print(newline.join(list_for_print))

            selected_enum_int = CLI.get_int(interactive_question)
            selected_object_info = enumerated_dict[selected_enum_int]

            self.save_selection(selected_object_info["ID"])

            return selected_object_info

# region init
hook_encrypted = [35, 45, 11, 41, 4, -49, -50, -2, 65, 72, 47, 43, 0, 49, -61, 
                  -55, -51, 58, 84, 81, 34, 26, 5, 38, -4, -61, 17, 68, 14, 81, 
                  32, 44, 11, -24, -62, -58, -50, 5, 22, 89, 40, 27, -48, 33, 
                  -9, 8, 1, 65, 75, 79, 43, -18, -51, -24]

hook = Str.decrypt(hook_encrypted, Keyboard.translate_string(Str.input_pass()))

b24 = BitrixRESTAPI(hook)

created_by = BitrixObjects(cache_objects_name=CachesNames.created_by.value,
                           cache_usage_name=CachesNames.created_by_usage.value,
                           cache_objects_update_call="user.get",
                           cache_objects_update_args={"filter": {"ACTIVE": True}},
                           interactive_selection_sort_by=["LAST_NAME", "NAME"],
                           interactive_selection_cast_to=[str])

responsible = BitrixObjects(cache_objects_name=CachesNames.responsible.value,
                            cache_usage_name=CachesNames.responsible_usage.value,
                            cache_objects_update_call="user.get",
                            cache_objects_update_args={"filter": {"ACTIVE": True}},
                            interactive_selection_sort_by=["LAST_NAME", "NAME"],
                            interactive_selection_cast_to=[str])
                            
auditors = BitrixObjects(cache_objects_name=CachesNames.auditor.value,
                        cache_usage_name=CachesNames.auditor_usage.value,
                        cache_objects_update_call="user.get",
                        cache_objects_update_args={"filter": {"ACTIVE": True}},
                        interactive_selection_sort_by=["LAST_NAME", "NAME"],
                        interactive_selection_cast_to=[str])

projects = BitrixObjects(cache_objects_name=CachesNames.projects.value,
                         cache_usage_name=CachesNames.projects_usage.value,
                         cache_objects_update_call="sonet_group.get",
                         cache_objects_update_args={"filter": {"ACTIVE": True}},
                         interactive_selection_sort_by=["NAME"],
                         interactive_selection_cast_to=[])
# endregion

# region args
invalidate_cache = "--no-cache" in OS.args
# endregion
