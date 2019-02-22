from src.utilities import *
from src.settings import *
import gkeepapi

import tkinter as tk


class Checklist:
    def __init__(s, root):
        s.root = root

        s.mainframe = tk.Frame(s.root)
        s.mainframe.pack(side="left")


class Checkbox:
    def __init__(s, checklist, checkbox_ptr):
        s.checklist = checklist
        s.root = s.checklist.mainframe
        s.ptr = checkbox_ptr
        s.value = tk.IntVar()

        s.mainframe = tk.Frame(s.root)
        s.mainframe.pack(side="top")
        s.check = tk.Checkbutton(s.mainframe, bd=10, highlightthickness=0, selectcolor="black", bg=COLOR_BG_1, indicatoron=0, relief="flat", variable=s.value)
        if s.ptr.checked:
            s.check.select()
        else:
            s.check.deselect()
        s.check.pack(side="left")
        s.textlabel = tk.Label(s.mainframe, text=s.ptr.text)
        s.textlabel.pack(side="left")
