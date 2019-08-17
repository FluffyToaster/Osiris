from src.utilities import *
from src.settings import *
import gkeepapi
import re
import datetime

import tkinter as tk


class Checklist:
    def __init__(s, root):
        s.root = root

        s.mainframe = tk.Frame(s.root,bg=COLOR_BG_2)

    def show(s):
        s.mainframe.pack(expand=True, fill="both")

    def hide(s):
        s.mainframe.pack_forget()


class CheckbuttonExt(tk.Button):
    def __init__(s, root, parent):
        s.root = root
        s.parent = parent
        s.checked_state = False
        tk.Button.__init__(s, root, bd=0, width=2, highlightthickness=0,
                           relief="flat", command=s.switch_state)

    def select(s):
        s.checked_state = True
        s.parent.ptr.checked = True
        s.configure(bg="green")
        s.parent.textlabel.configure(fg=COLOR_BG_LIGHT)
        if s.parent.deadline_wrapper:
            s.parent.deadline_wrapper.pack_forget()

    def deselect(s):
        s.checked_state = False
        s.parent.ptr.checked = False
        s.configure(bg=COLOR_BG_3)
        s.parent.textlabel.configure(fg=COLOR_TEXT)
        if s.parent.deadline_wrapper:
            if not s.parent.deadline_wrapper.winfo_ismapped():
                s.parent.deadline_wrapper.pack(side="right")

    def switch_state(s):
        if s.checked_state:
            s.deselect()
        else:
            s.select()


class Checkbox:
    def __init__(s, checklist, checkbox_ptr):
        s.checklist = checklist
        s.root = s.checklist.mainframe
        s.ptr = checkbox_ptr

        s.mainframe = tk.Frame(s.root, bg=COLOR_BG_1, highlightthickness=0)
        s.mainframe.pack(side="top", fill="x", padx=3, pady=(3,0))

        s.textlabel = tk.Label(s.mainframe, text=s.ptr.text, fg=COLOR_TEXT, anchor="w", bg=COLOR_BG_1, width=80, font=FONT_M)

        # assess item text for additional info: deadlines, repeats, etc
        s.deadline_wrapper = None
        s.deadline_label = None
        # match for deadline
        if not s.ptr.checked:
            match = re.search("[(\[][1-9]{1,2}/[1-9]{1,2}[)\]]", s.ptr.text)
            if match:
                fullmatch = match.group(0)
                day = int(fullmatch.split("/")[0][1:])
                month = int(fullmatch.split("/")[1][:-1])
                today = datetime.date.today()
                deadline = datetime.date(today.year, month, day)
                delta_days = int((deadline - today).days)
                if delta_days < -100:
                    delta_days += 365
                s.deadline_wrapper = tk.Label(s.mainframe, bd=0, relief="solid")
                s.deadline_wrapper.pack(side="right")
                height_restrictor = tk.Frame(s.deadline_wrapper, bg=COLOR_BG_1, bd=0, height=20, width=95)
                height_restrictor.pack_propagate(0)
                height_restrictor.pack(pady=1, padx=1)
                s.deadline_label = tk.Label(height_restrictor, fg=COLOR_TEXT, bg=COLOR_BG_1, font=FONT_M)
                s.deadline_label.pack()
                if delta_days >= 2:
                    s.deadline_label.configure(text=str(delta_days) + " days")
                    s.deadline_wrapper.configure(bg="green")
                elif delta_days == 0:
                    s.deadline_label.configure(text="today")
                    s.deadline_wrapper.configure(bg="yellow")
                elif delta_days == 1:
                    s.deadline_label.configure(text="tomorrow")
                    s.deadline_wrapper.configure(bg="green")
                else:
                    plural = " days late" if delta_days < -1 else " day late"
                    s.deadline_label.configure(text=str(-1 * delta_days) + plural)
                    s.deadline_wrapper.configure(bg="red")

        s.check = CheckbuttonExt(s.mainframe, s)
        if s.ptr.checked:
            s.check.select()
        else:
            s.check.deselect()

        # ALT:
        # img = Image.open("etc/gp.png")
        # photo = ImageTk.PhotoImage(img)
        # s.check = tk.Checkbutton(s.mainframe, highlightthickness=0, image=photo, variable=s.value)

        s.check.pack(side="left", fill="y")
        s.textlabel.pack(side="left")



