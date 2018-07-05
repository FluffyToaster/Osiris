class gpLine: # !!! move to below music classes when done
    def __init__(s,info,dl_mode="gp"):
        s.gp_info = info
        s.multi_index = 0
        s.dl_mode = dl_mode
        s.yt_info = []
        s.state = "preq" # starts in prequeue
        init_info = s.gp_info[s.multi_index]

        s.wrapper = tk.Frame(OSI.gpframe,height=54)
        s.mainframe = tk.Frame(s.wrapper,bg=tkbuttoncolor)
        s.indexlabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=3,text=('00'+str(len(gp_preq)+1))[-2:])
        s.indexlabel.pack(side=LEFT,padx=(10,0))
        s.image = Image.open(BytesIO(requests.get(init_info[3]).content))
        s.image = s.image.resize((50,50), Image.ANTIALIAS)
        # get the main color from the image for fancy reasons
        colors = s.image.getcolors(2500)
        max_occurence, most_present = 0, 0
        for c in colors:
            if c[0] > max_occurence:
                (max_occurence, most_present) = c
        s.bordercolor = ("#"+('00'+str(hex(most_present[0]))[2:])[-2:]+('00'+str(hex(most_present[1]))[2:])[-2:]+('00'+str(hex(most_present[2]))[2:])[-2:])
        s.wrapper.configure(bg=s.bordercolor)
        s.photo = ImageTk.PhotoImage(s.image)
        s.photoframe = tk.Frame(s.mainframe,height=50,width=50,bg=tkbuttoncolor)
        s.photoframe.pack_propagate(0)
        s.photolabel = tk.Label(s.photoframe,anchor=W,image=s.photo,borderwidth=0,highlightthickness=0)
        s.photolabel.pack()
        s.photoframe.pack(side=LEFT)
        s.titlelabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28,text=init_info[0])
        s.titlelabel.pack(side=LEFT,padx=(10,0))
        s.artistlabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28,text=init_info[1])
        s.artistlabel.pack(side=LEFT,padx=(10,0))
        s.albumlabel = tk.Label(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,anchor=W,font=fontset,width=28,text=init_info[2])
        s.albumlabel.pack(side=LEFT,padx=(10,0))
        s.delbutton = tk.Button(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,font=fontset,text="X",width=3,relief='ridge',bd=2,activebackground=tkbgcolor,activeforeground=tktxtcol, highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=lambda: OSI.gpinterpret("d "+str(s.indexval+1)))
        s.delbutton.pack(side=RIGHT,padx=(0,10))
        s.mulgpbutton = tk.Button(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,font=fontset,text="GP",width=3,relief='ridge',bd=2,activebackground=tkbgcolor,activeforeground=tktxtcol,highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.mulgpexp)
        s.mulgpbutton.pack(side=RIGHT,padx=(0,10))
        s.mulytbutton = tk.Button(s.mainframe,bg=tkbuttoncolor,fg=tktxtcol,font=fontset,text="YT",width=3,relief='ridge',bd=2,activebackground=tkbgcolor,activeforeground=tktxtcol,highlightbackground=s.bordercolor,highlightcolor=s.bordercolor,command=s.mulytexp)
        s.mulytbutton.pack(side=RIGHT,padx=(0,10))
        s.mainframe.pack(side=TOP,fill=X,padx=2,pady=2)
        s.multiframe = tk.Frame(s.wrapper,bg=s.wrapper.cget("bg")) # indeed not packed
        s.wrapper.pack(side=TOP,pady=(10,0),padx=10,fill=X)

        s.mulgpwidgets = []
        for i in s.gp_info:
            s.mulgpwidgets.append(s.gpmultiLine(s,i))

    def download(s):
        # calls either GP or YT download, depending on current selection
        s.active()
        if s.dl_mode == "gp":
            threading.Thread(target=s.gp_download).start()
        elif s.dl_mode == "yt":
            threading.Thread(target=s.yt_download).start()

    def gp_download(s):
        x = s.gp_info[s.multi_index] # currently relevant info
        folderpath = settings["gpdldir"] + x[1] + "/" + x[2] + "/"
        songpath = folderpath + ('00'+x[4])[-2:] + " " + x[0] + ".mp3"
        if os.path.isfile(songpath):
            pass
        else:
            # get the same data again, because the result object is needed when requesting url
            result = api.search(x[5]).get("song_hits",5)[int(s.multi_index)].get("track")
            OSI.gp_url2file(str(api.get_stream_url(result.get("storeId"))),songpath)
            if "albumArt.png" not in os.listdir(folderpath):
                OSI.gp_url2file(result.get("albumArtRef")[0].get("url"),(folderpath+"/albumArt.png"))
            OSI.gpalbumartify(songpath,folderpath)
            OSI.gptagify(songpath,x)
        s.done()
        gp_done.append(s)
        del gp_slots[gp_slots.index(s)]
        print("gp_download completed, calling check_q T-1")
        print("^songpath="+songpath)
        root.after(1000,lambda: OSI.gp_check_q())

    def imgchange(s,path):
        s.statusimage = Image.open(path)
        #s.statusimage = s.statusimage.resize((50,50), Image.ANTIALIAS)
        s.statusphoto = ImageTk.PhotoImage(s.statusimage)
        s.photolabel.configure(image=s.statusphoto,bg=tkbuttoncolor)
    def colchange(s,color):
        for i in [s.wrapper,s.multiframe]:
            i.configure(bg=color)
    def update(s):
        if s.state == "preq":
            s.indexval = gp_preq.index(s)
            s.indexlabel.configure(text=('00'+str(s.indexval+1))[-2:])
    def remove(s):
        try: del gp_preq[s.indexval]
        except: del gp_done[s.indexval]
        s.wrapper.pack_forget()
        s.wrapper.destroy()
        OSI.gpupdate()
    def queue(s):
        s.photolabel.configure(bg=tkbuttoncolor)
        s.imgchange("etc/clock.png")
        s.colchange("#C0C0C0")
    def active(s):
        s.indexlabel.configure(text="  ")
        s.imgchange("etc/download.png")
        s.colchange("#00BFFF")
    def done(s):
        s.imgchange("etc/check.png")
        s.colchange("#52a337")

    def ytgen(s):
        pass

    def mulgpexp(s): # expand multi widgets
        s.mulgpbutton.configure(command=s.mulgpcol)
        s.multiframe.pack(side=TOP,fill=X)
    def mulgpcol(s): # collapse multi widgets
        s.mulgpbutton.configure(command=s.mulgpexp)
        s.multiframe.pack_forget()
    def mulytexp(s):
        pass
    def mulytcol(s):
        pass

    class ytLine:
        def __init__(s,parent,info):
            s.parent = parent


    class gpmultiLine:
        def __init__(s,parent,info):
            s.parent = parent
            s.info = info
            s.mainframe = tk.Frame(s.parent.multiframe,bg=tkbuttoncolor)
            s.titlelabel = tk.Label(s.mainframe,anchor=W,font=fontset,bg=tkbuttoncolor,fg=tktxtcol,width=28,text=info[0])
            s.titlelabel.pack(side=LEFT,padx=(106,0))
            s.artistlabel = tk.Label(s.mainframe,anchor=W,font=fontset,bg=tkbuttoncolor,fg=tktxtcol,width=28,text=info[1])
            s.artistlabel.pack(side=LEFT,padx=(10,0))
            s.albumlabel = tk.Label(s.mainframe,anchor=W,font=fontset,bg=tkbuttoncolor,fg=tktxtcol,width=35,text=info[2])
            s.albumlabel.pack(side=LEFT,padx=(10,0))
            s.btn = tk.Button(s.mainframe,text="S",width=2,relief='ridge',bd=2,bg=tkbuttoncolor,fg=tktxtcol,activebackground=tkbgcolor,activeforeground=tktxtcol,command=s.select)
            s.btn.pack(side=RIGHT,padx=(0,10),pady=2)
            s.mainframe.pack(side=TOP,fill=X,padx=1,pady=(0,1))
        def select(s):
            s.parent.multi_index = s.parent.gp_info.index(s.info)
            s.parent.dl_mode = "gp"
            s.parent.image = Image.open(BytesIO(requests.get(s.info[3]).content))
            s.parent.image = s.parent.image.resize((50,50), Image.ANTIALIAS)
            s.parent.photo = ImageTk.PhotoImage(s.parent.image)
            s.parent.photolabel.configure(image=s.parent.photo)
            colors = s.parent.image.getcolors(2500) # raise value if too many colors
            max_occurence, most_present = 0, 0
            for c in colors:
                if c[0] > max_occurence:
                    (max_occurence, most_present) = c
            s.parent.bordercolor = ("#"+('00'+str(hex(most_present[0]))[2:])[-2:]+('00'+str(hex(most_present[1]))[2:])[-2:]+('00'+str(hex(most_present[2]))[2:])[-2:])
            s.parent.wrapper.configure(bg=s.parent.bordercolor)
            s.parent.multiframe.configure(bg=s.parent.bordercolor)
            s.parent.titlelabel.configure(text=s.info[0])
            s.parent.artistlabel.configure(text=s.info[1])
            s.parent.albumlabel.configure(text=s.info[2])
            OSI.gpupdate()
