import pprint

from main import *


def main():
    selected_created_by = created_by.select(get_config_value("default_created_by"),
                                            interactive_question="Выберите создателя задачи")
    selected_responsible = responsible.select(get_config_value("default_responsible"),
                                              interactive_question="Выберите ответственного")
    selected_auditor = auditors.select(get_config_value("default_auditor"), interactive_question="Выберите наблюдателя")
    selected_project = projects.select(get_config_value("default_project"), interactive_question="Выберите проект")

    title = input("Название задачи: ")

    description = CLI.multiline_input("Описание задачи: ")

    is_it_important = CLI.get_y_n("Это важная задача")

    minutes_planned = CLI.get_int("Минут план: ")

    minutes_fact = CLI.get_int("Минут факт: ")

    print()
    print(f"task: '{title}'\n{description}\n")
    print(f"selected created_by: {selected_created_by['ID']} {selected_created_by['LAST_NAME']} "
          f"{selected_created_by['NAME']}")
    print(f"selected responsible: {selected_responsible['ID']} {selected_responsible['LAST_NAME']} "
          f"{selected_responsible['NAME']}")
    print(f"selected auditor: {selected_auditor['ID']} {selected_auditor['LAST_NAME']} "
          f"{selected_auditor['NAME']}")
    print(f"selected project: {selected_project['ID']} {selected_project['NAME']}")
    Print.colored(f"important: {is_it_important}", "red" if is_it_important else "", sep='')
    print(f"minutes planned: {minutes_planned}")
    print(f"minutes fact: {minutes_fact}")
    print()

    if CLI.get_y_n("It's okay?"):
        additional_fields = {minutes_plan_set_name: minutes_planned,
                             minutes_fact_set_name: minutes_fact}
        task = create_task(title=title,
                           created_by=selected_created_by["ID"],
                           responsible_id=selected_responsible["ID"],
                           project_id=selected_project['ID'],
                           description=description,
                           auditors=[selected_auditor['ID']],
                           additional_fields=additional_fields,
                           is_it_important=is_it_important)
        task_id = task['id']

        print(generate_url_to_task(task))

        add_multiple_comments_to_task_interactive(task_id)

        if CLI.get_y_n("Закрыть задачу?"):
            complete_task(task_id)

        elif CLI.get_y_n("Начать задачу?"):
            start_task(task_id)
            change_task_stage(task, 'Выполняются')


if __name__ == '__main__':
    main()
