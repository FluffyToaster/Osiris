from src.settings import *
import tkinter as tk
from tkinter import LEFT
import subprocess
import os
from io import BytesIO
import threading

# third party libraries
import requests
from PIL import Image # use Pillow for python 3.x

from src.utilities import *


class DownloadManager:
    def __init__(s, osi):
        s.osi = osi
        s.mainframe = tk.Frame(s.osi.dlframe, bg=COLOR_BUTTON, height=35, width=TK_PROGRESS_BAR_WIDTH)
        s.mainframe.pack_propagate(0)
        s.progress_bar_wrapper = tk.Frame(s.mainframe, bg=COLOR_BG_1)
        s.progress_bar_wrapper.place(width=TK_PROGRESS_BAR_WIDTH, height=3)
        s.progress_bar_wrapper.pack_propagate(0)
        s.progress_bar_done = tk.Frame(s.progress_bar_wrapper, bg="green", height=3, width=0, bd=0)
        s.progress_bar_busy = tk.Frame(s.progress_bar_wrapper, bg="#469bfc", height=3, width=0, bd=0)
        s.progress_bar_queued = tk.Frame(s.progress_bar_wrapper, bg="grey", height=3, width=0, bd=0)
        for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
            i.pack_propagate(0)

        s.state = "waiting"
        s.idle = True
        s.count_gpcomplete = 0
        s.count_gptotal = 0
        s.count_ytcomplete = 0
        s.count_yttotal = 0
        s.count_convtotal = 0
        s.GpTracks = []
        s.yttracks = []
        s.staticlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor='w', font=FONT_M, width=40)
        s.staticlabel.pack(side=LEFT, pady=(1, 0))
        s.gplabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=4, text="GP: ")
        s.gplabel.pack(side=LEFT, pady=(1, 0))
        s.gpstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=7)
        s.gpstatus.pack(side=LEFT, pady=(1, 0))
        s.ytlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=6, text="  YT: ")
        s.ytlabel.pack(side=LEFT, pady=(1, 0))
        s.ytstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=7)
        s.ytstatus.pack(side=LEFT, pady=(1, 0))
        s.convlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=14,
                               text="  Converting: ")
        s.convlabel.pack(side=LEFT, pady=(1, 0))
        s.convstatus = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=10)
        s.convstatus.pack(side=LEFT, pady=(1, 0))
        s.refreshvalues()
        # mainframe not packed (this is done by login method)

    def refreshvalues(s):  # update the tracking labels
        if s.state == "waiting":
            s.staticlabel.configure(text="Status: ready to download")
        if s.state == "downloading gp":
            s.staticlabel.configure(text="Status: downloading from Google Play")
        if s.state == "downloading yt":
            s.staticlabel.configure(text="Status: downloading from YouTube")
        dltotal = s.count_gptotal + s.count_yttotal
        if dltotal > 0:
            if not s.bars_packed:
                for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
                    i.pack(side=LEFT)
                s.bars_packed = True
            if s.state == "waiting":
                s.progress_bar_done.configure(
                    width=TK_PROGRESS_BAR_WIDTH * (max(0, (s.count_gpcomplete + s.count_ytcomplete)) / dltotal))
                s.progress_bar_busy.configure(width=0)
            else:
                s.progress_bar_done.configure(
                    width=TK_PROGRESS_BAR_WIDTH * (max(0, (s.count_gpcomplete + s.count_ytcomplete - 1)) / dltotal))
                s.progress_bar_busy.configure(width=TK_PROGRESS_BAR_WIDTH / dltotal)
            s.progress_bar_queued.configure(
                width=TK_PROGRESS_BAR_WIDTH * (max(0, (dltotal - s.count_gpcomplete - s.count_ytcomplete)) / dltotal))
        else:
            s.bars_packed = False
            for i in [s.progress_bar_done, s.progress_bar_busy, s.progress_bar_queued]:
                i.pack_forget()
        s.gpstatus.configure(text=str(s.count_gpcomplete) + "/" + str(s.count_gptotal))
        s.ytstatus.configure(text=str(s.count_ytcomplete) + "/" + str(s.count_yttotal))
        s.convstatus.configure(text=str(s.count_convtotal) + " tracks")

    def download(s):  # publicly accessible download command that is split into further tasks
        if len(s.GpTracks) + len(s.yttracks) > 0:
            if len(s.GpTracks) > 0:
                s.state = "downloading gp"
            else:
                s.state = "downloading yt"
            s.process_downloads()  # start a continuously refreshing loop until all queues are done
        else:
            s.osi.log("s.osi: Nothing to download")

    def process_downloads(s):  # function that updates the downloading process
        # process the top of the gp queue
        if s.idle and len(s.GpTracks) + len(s.yttracks) > 0:
            if len(s.GpTracks) > 0:
                threading.Thread(target=lambda: s.gp_download(s.GpTracks.pop(0))).start()
            elif len(s.yttracks) > 0:
                threading.Thread(target=lambda: s.yt_download(s.yttracks.pop(0))).start()

        # decide if we need to keep downloading
        if len(s.GpTracks) + len(s.yttracks) > 0:
            s.osi.root.after(50, s.process_downloads)  # continue the loop
        elif s.idle and s.count_convtotal == 0:
            s.count_gpcomplete = 0
            s.count_gptotal = 0
            s.count_ytcomplete = 0
            s.count_yttotal = 0
            s.state = "waiting"
            s.osi.root.after(200, lambda: s.osi.mp_refresh())
            s.osi.log("s.osi: All downloads finished")
        else:  # if idle but converting: wait a bit longer
            s.osi.root.after(100, s.process_downloads)
        s.refreshvalues()

    def yt_download(s, track):  # download from youtube data to filename
        s.idle = False
        s.count_ytcomplete += 1
        s.refreshvalues()
        url = track[3]
        track[1] = s.get_correct_channel_name(track)
        name = settings["dldir"] + "/YouTube/" + track[1] + "/" + track[0] + ".mp3"
        os.makedirs(os.path.dirname(name), exist_ok=True)
        if not (os.path.isfile(name)):
            s.osi.root.after(100, lambda: s.idle_conv_watchdog(url, name, track))
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(DL_POPEN_ARGS + [url], startupinfo=startupinfo)
        else:
            s.osi.log("s.osi: YT DL skipped")
            s.idle = True
            s.refreshvalues()
            return

    def generate_image_data(s, tracklist, _index=None):
        if _index != None:
            curinfo = tracklist[_index]
        else:
            curinfo = tracklist[0]
        image = Image.open(BytesIO(requests.get(curinfo[2]).content))
        borders = s.osi.findborders(image)
        image = image.crop(borders)  # crop image to borders
        maincolor = color_from_image(image)  # get the prevalent color
        background = Image.new("RGB", (480, 480), maincolor)
        background.paste(image, (borders[0], 60 + borders[1]))
        if _index != None:
            tracklist[_index].append(background.copy())
            tracklist[_index].append(maincolor)
        else:
            return background.copy()

    def idle_conv_watchdog(s, id, name, track, recursing=False):  # keeps UI up to date and renames file when done
        for i in os.listdir():
            if i.endswith(id + ".mp3"):
                if os.path.getsize(i) < 100 and not recursing:  # found a match
                    s.idle = True
                    s.count_convtotal += 1
                    recursing = True
                elif os.path.getsize(i) > 1 and len([x for x in os.listdir() if id in x]) == 1:
                    try:
                        os.rename(i, name)
                        imagepath = "/".join(name.split("/")[:-1]) + "/" + id + ".png"
                        s.generate_image_data([track]).save(imagepath)
                        s.osi.dl_albumart_mp3(name, imagepath)
                        file_data = [track[0], track[1], "YouTube", "", "01", "", "None", "None", "Unknown",
                                     "Educational"]
                        s.osi.dl_tagify_mp3(name, file_data)
                        s.count_convtotal -= 1
                        s.refreshvalues()
                        return
                    except:
                        print("Rename failed, we'll get em next time")
        s.refreshvalues()
        s.osi.root.after(100, lambda: s.idle_conv_watchdog(id, name, track, recursing))  # else, keep looking

    def get_correct_channel_name(s, track):
        trackres = requests.get(
            "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + track[3] + "&key=" + settings[
                "yt_api_key"])
        actual_channel = trackres.json()["items"][0]["snippet"]["channelTitle"]
        return actual_channel

    def gp_download(s, track):  # download a single track
        s.idle = False
        s.count_gpcomplete += 1
        s.refreshvalues()
        '''
        track contents by index:
            (0) title
            (1) artist
            (2) album
            (3) album art URL
            (4) track number
            (5) storeId (was: multiIndex)
            (6) composer
            (7) date
            (8) bpm
            (9) genre
            (10) query
        '''

        folderpath = settings["dldir"] + track[1] + "/" + track[2] + "/"
        songpath = folderpath + ('00' + track[4])[-2:] + " " + track[0] + ".mp3"
        if os.path.isfile(songpath) and os.path.getsize(songpath) > 0:
            s.osi.log("s.osi: Skipping (already downloaded)")
        else:
            s.osi.dl_url2file(str(s.api.get_stream_url(track[5])), songpath)
            if "albumArt.png" not in os.listdir(folderpath):
                s.osi.dl_url2file(track[3], (folderpath + "/albumArt.png"))
            s.osi.dl_albumart_mp3(songpath, folderpath + "/albumArt.png")
            s.osi.dl_tagify_mp3(songpath, track)

        s.idle = True

    def queue_gp(s, tracklist):  # add tracks to the gp queue
        for i in tracklist:
            s.GpTracks.append(i)
            s.count_gptotal += 1
        s.refreshvalues()

    def queue_yt(s, tracklist):  # add tracks to the yt queue
        for i in tracklist:
            s.yttracks.append(i)
            s.count_yttotal += 1
        s.refreshvalues()
