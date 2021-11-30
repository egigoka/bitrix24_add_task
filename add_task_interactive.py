import pprint

from main import *


def main():
    selected_created_by = created_by.select(get_config_value("default_created_by"),
                                            interactive_question="Выберите создателя задачи")
    selected_responsible = responsible.select(get_config_value("default_responsible"),
                                              interactive_question="Выберите ответственного")

    if isinstance(get_config_value("default_auditor"), str):
        selected_auditor = auditors.select(get_config_value("default_auditor"),
                                           interactive_question="Выберите наблюдателя (ыыы)")
        selected_auditors = [selected_auditor]
    elif isinstance(get_config_value('default_auditor'), list):
        selected_auditors = []
        for auditor_id in get_config_value("default_auditor"):
            selected_auditors.append(auditors.select(auditor_id))
    else:
        selected_auditors = [auditors.select(interactive_question="Выберите наблюдателя")]

    selected_project = projects.select(get_config_value("default_project"), interactive_question="Выберите проект")

    title = ""
    while not title:
        title = input("Название задачи: ").strip()

    description = CLI.multiline_input("Описание задачи: ").strip()

    i = 0
    while '\n\n' in description:
        description = description.replace('\n\n', '\n')
        print(description)
        i += 1
        print(i)

    is_it_important = CLI.get_y_n("Это важная задача", "n")

    while True:
        deadline = CLI.get_date("deadline", always_return_date=False)
        if deadline is None:
            break
        deadline.replace(hour=19, minute=0, second=0)
        if deadline < Time.datetime(hour=23, minute=59, second=59):
            if CLI.get_y_n("Do you really wanna set deadline in past", "n"):
                break
            else:
                continue
        break

    print()
    print(f"task: '{title}'\n\"{description}\"\n")
    print(f"selected created_by: {selected_created_by['ID']} {selected_created_by['LAST_NAME']} "
          f"{selected_created_by['NAME']}")
    print(f"selected responsible: {selected_responsible['ID']} {selected_responsible['LAST_NAME']} "
          f"{selected_responsible['NAME']}")

    print(f"selected auditors:")
    for selected_auditor in selected_auditors:
        print(f"    {selected_auditor['ID']} {selected_auditor['LAST_NAME']} "
              f"{selected_auditor['NAME']}")
    print(f"selected project: {selected_project['ID']} {selected_project['NAME']}")
    Print.colored(f"important: {is_it_important}", "red" if is_it_important else "")
    if deadline is not None:
        Print.colored(f"deadline: {datetime_to_bitrix_time(deadline)}", "red")
    print()

    if CLI.get_y_n("It's okay?", "y"):
        additional_fields = {}
        task = create_task(title=title,
                           created_by=selected_created_by["ID"],
                           responsible_id=selected_responsible["ID"],
                           project_id=selected_project['ID'],
                           description=description,
                           auditors=get_config_value('default_auditor'),
                           additional_fields=additional_fields,
                           is_it_important=is_it_important,
                           deadline=deadline)
        task_id = task['id']

        print(generate_url_to_task(task))

        add_multiple_comments_to_task_interactive(task_id)

        if CLI.get_y_n("Закрыть задачу?", "n"):
            complete_task(task_id)

        elif CLI.get_y_n("Начать задачу?", "n"):
            try:
                start_task(task_id)
            except KeyError:
                pass
            
            change_task_stage(task, 'Выполняются')

        add_minutes = input("Добавить сразу времени? (мин) ").strip()
        if add_minutes.isnumeric():
            add_minutes = int(add_minutes)
            add_time_to_task(task_id=task_id, seconds=add_minutes*60)


if __name__ == '__main__':
    main()
