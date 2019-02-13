from src.settings import *
from src.utilities import *


# get the content of osData.txt, also applicable for other .txt files
def select_file(filepath=settings["datapath"]):
    with open(filepath, "r", encoding="utf-8") as selectedFile:
        data = [x.strip('\n') for x in selectedFile.readlines()]
    return data


# replace the current content of section with that of writelist, creates section if there is none
def write_to_text(writelist, section, filepath=settings["datapath"]):
    data = select_file(filepath) if filepath is not None else select_file()
    try:
        start = data.index("=" + section + "=") + 1
        end = data.index("=/" + section + "=")
    except ValueError:
        data += ["=" + section + "="] + ["\n"] + ["=/" + section + "="]
        start = data.index("=" + section + "=") + 1
        end = data.index("=/" + section + "=")
    data[start:end] = []
    for i in writelist[::-1]:
        data.insert(start, i)
    write_file = open(filepath, "w", encoding="utf-8")
    for i in data:
        write_file.write(i + "\n")
    write_file.close()


# gets the content of a section
def read_from_text(section, filepath=None):
    data = select_file(filepath) if filepath is not None else select_file()
    try:
        start = data.index("=" + section + "=") + 1
        end = data.index("=/" + section + "=")
    except ValueError:
        return []
    return data[start:end]


def del_text(section, filepath=settings["datapath"]):  # deletes a section
    data = select_file(filepath) if filepath is not None else select_file()
    try:
        data[(data.index("=" + section + "=")):(data.index("=/" + section + "=") + 1)] = []
    except ValueError:
        return False
    write_file = open(filepath, "w", encoding="utf-8")
    for i in data:
        write_file.write(i + "\n")
    write_file.close()
    return True


def search_text(section, filepath=None):  # returns the names of all matching sections
    data = select_file(filepath) if filepath is not None else select_file()
    result = search(str("=" + section), data)
    if result is not False:
        for i in range(len(result)):
            result[i] = result[i][1:-1]
    return result
