import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "students.json")

def load_students():
    if not os.path.exists(JSON_FILE):
        return {}

    with open(JSON_FILE, "r") as f:
        return json.load(f)


def save_students(students):
    with open(JSON_FILE, "w") as f:
        json.dump(students, f, indent=2)


def get_student_class(name):
    students = load_students()
    cls = students.get(name)
    if cls:
        return "f{name} is a Jedi {cls}."
    return f"Hmm… Student not found, I see."


def add_student(name, jedi_class):
    students = load_students()
    students[name] = jedi_class
    save_students(students)
    return f"Added, {name} has been. A Jedi {jedi_class}, they are!"


def remove_student(name):
    students = load_students()
    if name in students:
        del students[name]
        save_students(students)
        return f"Graduated, {name} has. Celebrate, we must."
    return f"Vanished? This student does not exist."

def list_students():
    students = load_students()
    grouped = {}
    for name, cls in students.items():
        grouped.setdefault(cls, []).append(name)

    result_lines = []
    for cls, names in grouped.items():
        names_str = ", ".join(names)
        result_lines.append(f"{cls}: {names_str}")

    return "\n".join(result_lines)

