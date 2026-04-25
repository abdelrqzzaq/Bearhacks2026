import os
import shutil


def create_folder(path, name):
    new_path = os.path.join(path, name)
    os.makedirs(new_path, exist_ok=True)
    return new_path


def create_file(path, name):
    if not name.endswith(".txt"):
        name += ".txt"
    new_path = os.path.join(path, name)
    with open(new_path, "w") as f:
        f.write("")
    return new_path


def delete_item(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def rename_item(old_path, new_name):
    parent = os.path.dirname(old_path)
    new_path = os.path.join(parent, new_name)
    os.rename(old_path, new_path)
    return new_path


def read_file(path):
    with open(path, "r", errors="replace") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def list_directory(path):
    try:
        entries = os.listdir(path)
    except PermissionError:
        return [], []
    folders = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))])
    files = sorted([e for e in entries if os.path.isfile(os.path.join(path, e))])
    return folders, files
