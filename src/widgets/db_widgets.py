from src.settings import *

import tkinter as tk
from tkinter import LEFT, RIGHT, TOP, X
from Crypto.Cipher import AES


# utility defs
def db_parse_aeg_key(keys, first):
    endkey = ""
    for i in range(32):
        if first:
            endkey += (keys[i % 2] * 32)[i // 2]
        if not first:
            endkey += (keys[(i + 1) % 2][::-1] * 32)[i // 2]
    return str.encode(endkey)


def db_aeg_enc_single(key, data):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce + tag + ciphertext


def db_aeg_dec_single(key, data):
    nonce = data[:16]
    tag = data[16:32]
    ciphertext = data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    output = cipher.decrypt_and_verify(ciphertext, tag)
    return output


def db_aeg_enc(keys, data):
    data = str.encode(data)
    for i in range(DB_ENC_LEVEL):
        data = db_aeg_enc_single(db_parse_aeg_key(keys, True), data)

    for i in range(DB_ENC_LEVEL):
        data = db_aeg_enc_single(db_parse_aeg_key(keys, False), data)

    return data


def db_aeg_dec(keys, data):
    for i in range(DB_ENC_LEVEL):
        data = db_aeg_dec_single(db_parse_aeg_key(keys, False), data)

    for i in range(DB_ENC_LEVEL):
        data = db_aeg_dec_single(db_parse_aeg_key(keys, True), data)

    data = data.decode()
    return data


class DbLine:  # !!! move to below music classes when done
    def __init__(s, osi, path, indx):
        s.osi = osi
        s.isfile = path.endswith((".txt", ".aegis"))
        s.isaegis = path.endswith(".aegis")
        s.indexval = indx
        # if not s.isfile:
        #     s.indexval = dbstate[2].index(path)
        # else:
        #     if not s.isaegis or not openable: s.indexval = dbstate[1].index(path)+len(dbstate[2])
        #     else:
        #         if openable: s.indexval = dbstate[4].index(display) + len(dbstate[2])

        s.wrapper = tk.Frame(s.osi.dbframe, height=25, bg=COLOR_BG_3)
        s.wrapper.pack_propagate(0)
        s.mainframe = tk.Frame(s.wrapper, bg=COLOR_BUTTON)
        s.indexlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=3,
                                text=('00' + str(s.indexval + 1))[-2:])
        s.indexlabel.pack(side=LEFT, padx=(10, 0))
        s.typelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=10)
        s.typelabel.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=28)
        s.titlelabel.pack(side=LEFT, padx=(10, 0))
        if s.osi.dbstate[3][s.indexval] == "aeg_nokey":
            s.titlelabel.configure(text="-- KEY REQUIRED --")
        elif s.osi.dbstate[3][s.indexval] == "aeg_wrongkey":
            s.titlelabel.configure(text="-- INCORRECT KEY --")
        else:
            s.titlelabel.configure(text=s.osi.dbstate[1][s.indexval])
        #     if s.isfile: s.titlelabel.configure(text=".".join(path.split("\\")[-1].split(".")[:-1]))
        #     else: s.titlelabel.configure(text=path.split("\\")[-1])
        # else: s.titlelabel.configure(text=display)
        if s.isfile:
            if s.isaegis:
                s.typelabel.configure(text="AEGIS")
            else:
                s.typelabel.configure(text="TEXT")
            s.delbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="DEL", width=6,
                                    relief='ridge', bd=0, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                    command=lambda: s.osi.db_interpret("d " + str(s.indexval + 1)))
            s.delbutton.pack(side=RIGHT)
        else:
            s.typelabel.configure(text="FOLDER")
        if s.osi.dbstate[3][s.indexval] not in ["aeg_nokey", "aeg_wrongkey"]:
            s.openbutton = tk.Button(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, font=FONT_M, text="OPEN", width=6,
                                     relief='ridge', bd=0, activebackground=COLOR_BG_1, activeforeground=COLOR_TEXT,
                                     command=lambda: s.osi.db_interpret("o " + str(s.indexval + 1)))
            s.openbutton.pack(side=RIGHT)
        s.mainframe.pack(side=TOP, fill=X, padx=1, pady=1)
        s.wrapper.pack(side=TOP, pady=(2, 0), padx=10, fill=X)
