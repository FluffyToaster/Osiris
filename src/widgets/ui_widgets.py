from src.settings import *

import tkinter as tk


class BasicButton(tk.Button):
    def __init__(s, root, text, command, font=FONT_L, width=TK_BUTTON_WIDTH):
        tk.Button.__init__(s, root, bg=COLOR_BUTTON, fg=COLOR_TEXT, borderwidth=0, activebackground=COLOR_BUTTON_ACTIVE,
                           activeforeground=COLOR_TEXT, font=font, width=width, text=text, command=command)


class HoverButton(tk.Button):
    def __init__(s, root, text="Hover button", command=None, width=5, hover_color=COLOR_BUTTON_ACTIVE, bg=COLOR_BUTTON,
                 font=FONT_M, hide_till_hover=False, hide_bind=None):
        tk.Button.__init__(s, root, borderwidth=0, bg=bg, activebackground=hover_color,
                           fg=COLOR_TEXT, activeforeground="white", font=font, width=width, text=text,
                           command=command)
        s.root = root
        s.hide_till_hover = hide_till_hover
        s.bg = bg
        s.hover_color = hover_color
        if hide_bind is None:
            s.hide_bind = s
        else:
            s.hide_bind = hide_bind

        s.bind("<Enter>", lambda x: s.configure(bg=s.hover_color, fg=COLOR_TEXT))
        s.bind("<Leave>", lambda x: s.configure(bg=s.bg))
        if hide_till_hover:
            s.hide_bind.bind("<Enter>", s.show_event)
            s.hide_bind.bind("<Leave>", s.hide_event)
            s.after(10, lambda: s.hide_event(None))

    def show_event(s, event):
        if s.hide_till_hover:
            s.configure(bg=s.bg, fg=COLOR_TEXT)

    def hide_event(s, event):
        if s.hide_till_hover:
            hide_color = s.hide_bind.cget("bg")
            s.configure(bg=hide_color, fg=hide_color)


