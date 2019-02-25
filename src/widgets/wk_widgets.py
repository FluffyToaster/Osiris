from src.utilities import *
from src.settings import *
import gkeepapi
import re
import datetime

import tkinter as tk


class Checklist:
    def __init__(s, root):
        s.root = root

        s.mainframe = tk.Frame(s.root)
        s.mainframe.pack(side="left")


class CheckbuttonExt(tk.Checkbutton):
    def __init__(s, root, variable):
        s.root = root
        tk.Checkbutton.__init__(s, root, bd=0, width=2, highlightthickness=0, selectcolor="green",
                                bg=COLOR_BG_1, indicatoron=0, relief="flat", variable=variable)

    def select(s):
        tk.Checkbutton.select(s)
        s.root.configure(bg=COLOR_BG_GREEN)

    def deselect(s):
        tk.Checkbutton.select(s)
        s.root.configure(bg=COLOR_BG_RED)

class Checkbox:
    def __init__(s, checklist, checkbox_ptr):
        s.checklist = checklist
        s.root = s.checklist.mainframe
        s.ptr = checkbox_ptr
        s.value = tk.IntVar()

        s.mainframe = tk.Frame(s.root)
        s.mainframe.pack(side="top", fill="x")
        s.check = CheckbuttonExt(s.mainframe, s.value)
        if s.ptr.checked:
            s.check.select()
        else:
            s.check.deselect()
        s.check.pack(side="left")

        s.textlabel = tk.Label(s.mainframe, text=s.ptr.text)
        s.textlabel.pack(side="left")

        # assess item text for additional info: deadlines, repeats, etc

        # match for deadline
        if not s.ptr.checked:
            match = re.search("[(\[][1-9]{1,2}/[1-9]{1,2}[)\]]", s.ptr.text)
            if match:
                fullmatch = match.group(0)
                day = int(fullmatch.split("/")[0][1:])
                month = int(fullmatch.split("/")[1][:-1])
                print(day, month)
                today = datetime.date.today()
                deadline = datetime.date(today.year, month, day)
                delta_days = (deadline - today).days
                if delta_days < -100:
                    delta_days += 365

                print(delta_days)

                s.deadline_label = tk.Label(s.mainframe)
                if delta_days >= 5:
                    s.deadline_label.configure(text=str(delta_days) + " days", bg="green")
                elif delta_days >= 0:
                    if delta_days == 0:
                        s.deadline_label.configure(text="today", bg="yellow")
                    if delta_days == 1:
                        s.deadline_label.configure(text="tomorrow", bg="yellow")
                    else:
                        s.deadline_label.configure(text=str(delta_days) + "days", bg="yellow")
                else:
                    s.deadline_label.configure(text=str(-delta_days) + " day" + ("s" if delta_days < -1 else "")
                                                    + " late", bg="red")
                s.deadline_label.pack()
