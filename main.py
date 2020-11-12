from enum import Enum
from typing import Any, Union
from bitrix24api import BitrixRESTAPI
from commands import *

# region development functions (temp)
def print_all_task_fields():
    fields = b24.smart_get("tasks.task.getfields")['fields']

    for name, desc in fields.items():
        print(name)
        for name_desc, value in desc.items():
            print(f"\t{name_desc}: {value}")
# endregion

# region funcs tasks
def create_task(title, created_by, responsible_id, project_id, description):
    return b24.smart_get("tasks.task.add",
                         {"fields":
                              {"TITLE": title,
                               "CREATED_BY": created_by,
                               "RESPONSIBLE_ID": responsible_id,
                               "DESCRIPTION": description,
                               "GROUP_ID": project_id}
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


def change_task_stage(task_obj, new_stage_name, verbose=False):
    stages = b24.smart_get("task.stages.get", {"entityId": task_obj['task']['group']['id']})

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
                sorted_objects.append(objects.pop(object_id))

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
hook = "https://kurganmk.bitrix24.ru/rest/11/tbjn4luh6u1b6irw/"

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
