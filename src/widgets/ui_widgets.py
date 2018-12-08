from src.settings import *

import tkinter as tk


class BasicButton(tk.Button):
    def __init__(s, root, text, command, font=FONT_L, width=TK_BUTTON_WIDTH):
        tk.Button.__init__(s, root, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                           activeforeground=COLOR_TEXT, font=font, width=width, text=text, command=command)


class HoverButton(tk.Button):
    def __init__(s, root, text="Hover button", command=None, width=5, hover_color=COLOR_BUTTON_ACTIVE, bg=COLOR_BUTTON, font=FONT_M):
        tk.Button.__init__(s, root, borderwidth=0, bg=bg, activebackground=hover_color,
                           fg=COLOR_TEXT, activeforeground="white", font=font, width=width, text=text,
                           command=command)
        s.bind("<Enter>", lambda x: s.configure(bg=hover_color))
        s.bind("<Leave>", lambda x: s.configure(bg=bg))

