# UTILITIES
# Contains utility functions


# search function: use the given criteria to filter the total list
# param find - a string, built from ';'-separated filter commands
# param total - an array of strings, each string is evaluated separately
def search(find, total):
    # find can be read as written in DNF, with the OR's as ';'
    find = find.split(";")
    results = []
    for term in find:  # each term is evaluated over the total
        term = term.split()
        remlist = []
        for single in term:
            if single.startswith("-"):
                remlist.append(single[1:])
        for full in total:  # loops through every entry in the total list
            match = True
            for single in term:
                if not single.startswith("-"):
                    if single.lower() not in full.lower():
                        match = False
            if match:
                for rem in remlist:
                    if rem.lower() in full.lower():
                        match = False
                if match and full not in results:
                    results.append(full)
    return results


# interpret search criteria and return matches
def match_criteria(crit, searchlist):
    match = []  # list of all files that match criteria given
    for i in crit.split(";"):
        if len(i.split("-")) == 2:
            if is_int(i.split("-")[0]) and is_int(i.split("-")[1]):
                # criterium is range of files
                match += searchlist[int(i.split("-")[0]) - 1:int(i.split("-")[1])]
        if is_int(i):
            # criterium is single file
            if int(i) <= len(searchlist):
                match += [searchlist[int(i) - 1]]
        else:
            # criterium is string to search
            match += search(i, searchlist)
    return match


# check whether a value can be converted to an integer
def is_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


# remove duplicate values from a list
def remove_duplicates(duplist):
    seen = set()
    seen_add = seen.add
    return [x for x in duplist if not (x in seen or seen_add(x))]


# filter characters from a string
def filter_chars(string_in, chars):
    out = "".join(list(filter(lambda x: x not in chars, list(string_in))))
    return out


# escape backslashes
def escape(string):
    val = repr(string)
    for i in range(4):
        val = val.replace([r"\x0", r"\n", r"\l", r"\t"][i],
                          [r"\\0", r"\\n", r"\\l", r"\\t"][i])
    return val.strip("'")


# handle unsafe strings, make them UTF-8 compliant
def filter_(orig_string, make_safe_for_filename=True, make_safe_for_tcl=True):
    temp = orig_string[:]
    if make_safe_for_filename:
        changelist = '*/\\":?<>|'
        for char in changelist:
            temp = "_".join(temp.split(char))

    if make_safe_for_tcl:
        temp = "".join([x for x in temp if ord(x) < 0xFFFF])

    return bytes(temp, 'utf-8').decode('utf-8', 'replace')


# get the most frequent color from an image
def color_from_image(image, avoid_dark=False):
    colors = image.getcolors(image.size[0] * image.size[1])
    max_occurence, most_present = 0, 0
    for c in colors:
        if c[0] > max_occurence and (not avoid_dark or sum(c[1]) > 100):
            (max_occurence, most_present) = c
    return most_present


# parse an RGB tuple into a Hex color string
def rgb_to_hex(rgb):
    return ("#" + ('00' + str(hex(rgb[0]))[2:])[-2:]
            + ('00' + str(hex(rgb[1]))[2:])[-2:]
            + ('00' + str(hex(rgb[2]))[2:])[-2:])
