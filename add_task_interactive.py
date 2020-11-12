from main import *

selected_created_by = created_by.select(interactive_question="Выберите создателя задачи")
selected_responsible = responsible.select(interactive_question="Выберите ответственного")
selected_project = projects.select(interactive_question="Выберите проект")
title = input("Название задачи: ")
description = CLI.multiline_input("Описание задачи: ")

print()
print(f"selected created_by: {selected_created_by['ID']} {selected_created_by['LAST_NAME']} "
      f"{selected_created_by['NAME']}")
print(f"selected responsible: {selected_responsible['ID']} {selected_responsible['LAST_NAME']} "
      f"{selected_responsible['NAME']}")
print(f"selected project: {selected_project['ID']} {selected_project['NAME']}")
print(f"task: '{title}'\n{description}")
print()

if CLI.get_y_n("It's okay?"):
    task = create_task(title=title,
                        created_by=selected_created_by["ID"],
                        responsible_id=selected_responsible["ID"],
                        project_id=selected_project['ID'],
                        description=description)
    task_id = task['task']['id']

    add_multiple_comments_to_task_interactive(task_id)

    if CLI.get_y_n("Закрыть задачу?"):
        complete_task(task_id)

    elif CLI.get_y_n("Начать задачу?"):
        start_task(task_id)
        change_task_stage(task, 'Выполняются')