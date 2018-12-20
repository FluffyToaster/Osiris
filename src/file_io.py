from src.settings import *
from src.utilities import *


# get the content of osData.txt, also applicable for other .txt files
def select_file(filepath=settings["datapath"]):
    with open(filepath, "r", encoding="utf-8") as selectedFile:
        data = [x.strip('\n') for x in selectedFile.readlines()]
    return data


# replace the current content of section with that of writelist, creates section if there is none
def write_to_text(writelist, section):
    data = select_file()
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
    write_file = open(settings["datapath"], "w", encoding="utf-8")
    for i in data:
        write_file.write(i + "\n")
    write_file.close()


# gets the content of a section
def read_from_text(section):
    data = select_file()
    try:
        start = data.index("=" + section + "=") + 1
        end = data.index("=/" + section + "=")
    except IndexError:
        return False
    return data[start:end]


def del_text(section):  # deletes a section
    data = select_file()
    try:
        data[(data.index("=" + section + "=")):(data.index("=/" + section + "=") + 1)] = []
    except IndexError:
        return False
    write_file = open(settings["datapath"], "w", encoding="utf-8")
    for i in data:
        write_file.write(i + "\n")
    write_file.close()
    return True


def search_text(section):  # returns the names of all matching sections
    data = select_file()
    result = search(str("=" + section), data)
    if result is not False:
        for i in range(len(result)):
            result[i] = result[i][1:-1]
    return result
