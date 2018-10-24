from src.settings import *
import tkinter as tk
from tkinter import LEFT, RIGHT, TOP, BOTTOM


class PageHandler:
    def __init__(s, osi, mode, page_size):
        s.osi = osi
        s.mode = mode
        s.page_size = page_size

        s.root = s.osi.frames[s.osi.modes.index(s.mode)]
        s.interpreter = s.osi.interpreters[s.osi.modes.index(s.mode)]

        s.mainframe = tk.Frame(s.root, bg=COLOR_BUTTON, height=30, width=400)
        s.mainframe.pack_propagate(0)

        s.prev_button = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0,
                                  activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT, font=FONT_M,
                                  text="PREVIOUS", width=10, command=s.prev)
        s.prev_button.pack(side=LEFT)

        s.next_button = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0,
                                  activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT, font=FONT_M,
                                  text="NEXT", width=10, command=s.next)
        s.next_button.pack(side=RIGHT)

        s.current_page = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, width=10, text="PAGE 1")
        s.current_page.pack(side=TOP)

    def set_page(s, new, widget_count):
        if widget_count > s.page_size and not s.mainframe.winfo_ismapped():
            s.mainframe.pack(side=BOTTOM)
        if widget_count <= s.page_size and s.mainframe.winfo_ismapped():
            s.mainframe.pack_forget()
        s.current_page.configure(text="PAGE " + str(new))

    def prev(s):
        s.interpreter("pgp")

    def next(s):
        s.interpreter("pgn")
