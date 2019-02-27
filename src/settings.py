settings = {}


def import_settings(path="etc/settings.txt"):
    global settings
    settings = {}
    settingsfile = open(path, "r")
    for setting in settingsfile:
        (key, value) = setting.split(" = ")
        value = value.rstrip("\n")
        settings[key] = value
    settingsfile.close()


def export_settings(path="etc/settings.txt"):
    settingsfile = open(path, "w")
    for key in sorted(settings.keys()):
        settingsfile.write(key + " = " + settings[key] + "\n")
    settingsfile.close()


import_settings()

# LOCAL SETTINGS
# tkinter settings
FONT_S = ("Roboto Mono", "8")  # font name + size
FONT_M = ("Roboto Mono", "10")
FONT_L = ("Roboto Mono", "11")
FONT_ITALIC = ("Roboto Mono", "10", "italic")
FONT_BOLD = ("Roboto Mono", "11", "bold")
FONT_BOLD_M = ("Roboto Mono", "10", "bold")
if settings["set_large_taskbar"] == "False":
    TK_HEIGHT = 1042
else:
    TK_HEIGHT = 1030
TK_WIDTH = 1920
TK_PADDING = 10
TK_LOG_HEIGHT = 40  # 25 under height 600
TK_BUTTON_WIDTH = 25
TK_PROGRESS_BAR_WIDTH = 1594  # bit arbitrary but should not change in a 1920 width window

# tkinter A E S T H E T I C
COLOR_BG_1 = "#2e3338"  # color of general background
COLOR_BG_2 = "#394046"  # secondary music selection color
COLOR_BG_3 = "#454d54"  # music selection button color
COLOR_BG_LIGHT = "#797F86"  # between bg 3 and the text color (for greyed out text)
COLOR_BUTTON = "#14161A"
COLOR_BUTTON_ACTIVE = COLOR_BG_1
COLOR_BUTTON_BRIGHT = "#1d1f25"
COLOR_TEXT = "#D3D7DE"
COLOR_BG_GREEN = "#1D4624"
COLOR_BG_RED = "#673324"

# mp settings
MP_PAGE_SIZE = 32  # widgets rendered on a page
if settings["set_foobarplaying"] == "True":
    MP_PAGE_SIZE = 29
ALLOWED_FILETYPES = [".mp3"]  # could also allows ".flac",".m4a",".wav" but would increase time to refresh
PLI_WIDTH = 350

# db settings
DB_DIR = "database/"
DB_ENC_LEVEL = 3  # depth of Aegis AES-256 ecryption

# dl settings
DL_PAGE_SIZE = 13  # widgets on a page
DL_ALTERNATIVES = 5  # number of alternatives to display when searching
DL_CROP_THRESH = 25  # used when cropping YT thumbnails

# arguments for subprocess Popen call when downloading from YT
DL_POPEN_ARGS = ['youtube-dl',
                 '-f', 'bestaudio/best']

DL_CONVERT_ARGS = [settings["ffmpegexe"],
                   '-y',
                   '-loglevel',
                   '40',
                   '-i',
                   'PLACEHOLDER',
                   '-vn',
                   '-acodec',
                   'libmp3lame',
                   '-b:a',
                   '320k',
                   'PLACEHOLDER']

SU_IP_HEIGHT = 25
