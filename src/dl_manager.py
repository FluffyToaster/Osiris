import subprocess
import threading
import shutil
# third party libraries
from src.widgets.dl_widgets import *


class DownloadManager:
    def __init__(s, osi):
        s.osi = osi
        s.api = None
        s.rootdir = None
        s.single_progress_fraction = 0.0
        s.single_download_fraction = 0.0
        s.mainframe = tk.Frame(s.osi.dlframe, bg=COLOR_BUTTON, height=35, width=TK_PROGRESS_BAR_WIDTH)
        s.mainframe.pack_propagate(0)
        s.progress_bar_wrapper = tk.Frame(s.mainframe, bg=COLOR_BG_1)
        s.progress_bar_wrapper.place(width=TK_PROGRESS_BAR_WIDTH, height=3)
        s.progress_bar_wrapper.pack_propagate(0)
        s.progress_bar_done = tk.Frame(s.progress_bar_wrapper, bg="green", height=3, width=0, bd=0)
        s.progress_bar_downloaded = tk.Frame(s.progress_bar_wrapper, bg="#6FA76B", height=3, width=0, bd=0)
        s.progress_bar_busy = tk.Frame(s.progress_bar_wrapper, bg="#469bfc", height=3, width=0, bd=0)
        s.progress_bar_queued = tk.Frame(s.progress_bar_wrapper, bg="grey", height=3, width=0, bd=0)
        for i in [s.progress_bar_done, s.progress_bar_downloaded, s.progress_bar_busy, s.progress_bar_queued]:
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
        s.ytlabel = tk.Label(s.mainframe, bg=COLOR_BUTTON, fg=COLOR_TEXT, anchor="w", font=FONT_M, width=6,
                             text="  YT: ")
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
                for i in [s.progress_bar_done, s.progress_bar_downloaded, s.progress_bar_busy, s.progress_bar_queued]:
                    i.pack(side=LEFT)
                s.bars_packed = True
            else:
                s.progress_bar_done.configure(
                    width=TK_PROGRESS_BAR_WIDTH * ((max(0, (s.count_gpcomplete + s.count_ytcomplete)) +
                                                    s.single_progress_fraction) / dltotal))
                s.progress_bar_downloaded.configure(width=TK_PROGRESS_BAR_WIDTH * s.single_download_fraction / dltotal)
                s.progress_bar_busy.configure(width=TK_PROGRESS_BAR_WIDTH - s.single_progress_fraction -
                                              s.single_download_fraction / dltotal)
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
            s.osi.log("OSI: Nothing to download")

    def process_downloads(s):  # function that updates the downloading process
        # process the top of the gp queue
        if s.idle and len(s.GpTracks) + len(s.yttracks) > 0:
            if len(s.GpTracks) > 0:
                s.single_progress_fraction = 0
                s.single_download_fraction = 0
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
            s.osi.log("OSI: All downloads finished")
        else:  # if idle but converting: wait a bit longer
            s.osi.root.after(100, s.process_downloads)
        s.refreshvalues()

    def yt_download(s, track):  # download from youtube data to filename
        s.idle = False
        s.refreshvalues()
        url = track[3]
        track[1] = get_correct_channel_name(track)
        name = settings["dldir"] + "/YouTube/" + track[1] + "/" + track[0] + ".mp3"
        os.makedirs(os.path.dirname(name), exist_ok=True)
        if not os.path.isfile(name):
            if not is_video_blocked(url):
                # if not already downloaded and not blocked
                # step 1: use yt-download to get .m4a or .webm of given url
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                old_dl = 0.0
                popen = subprocess.Popen(DL_POPEN_ARGS + ["--"] + [url], startupinfo=startupinfo,
                                         stdout=subprocess.PIPE, cwd=s.rootdir, universal_newlines=True)
                for stdout_line in iter(popen.stdout.readline, ""):
                    if stdout_line.startswith("[download]") and "Destination:" not in stdout_line:
                        percent = stdout_line[10:].lstrip(" ").split()[0].rstrip("%")
                        try:
                            new_dl = float(percent) / 100
                            s.single_download_fraction += new_dl - old_dl
                            old_dl = new_dl
                            s.refreshvalues()
                        except ValueError:
                            pass
                popen.stdout.close()
                popen.wait()

                # download done
                s.idle = True # signal to download manager that next download can start
                s.count_convtotal += 1

                try:
                    filename = [x for x in os.listdir(s.rootdir) if x.endswith(url+".webm")][0]
                    new_filename = filename[:-4] + "mp3"
                except IndexError: # if yt-dl decided to download as m4a instead of webm
                    filename = [x for x in os.listdir(s.rootdir) if x.endswith(url + ".m4a")][0]
                    new_filename = filename[:-3] + "mp3"

                convert_args = DL_CONVERT_ARGS
                convert_args[5] = ""+filename
                convert_args[11] = ""+new_filename
                duration = None
                old_conv = 0.0
                os.chdir(s.rootdir)
                popen = subprocess.Popen(convert_args, startupinfo=startupinfo, stderr=subprocess.PIPE,
                                         universal_newlines=True, cwd=s.rootdir)
                for stderr_line in iter(popen.stderr.readline, ""):
                    if stderr_line.lstrip(" ").startswith("Duration") and not duration:
                        duration = ":".join(stderr_line.split(":")[1:4]).lstrip(" ")  # hrs:mins:secs.decimals
                        duration = parse_duration(duration)
                    elif stderr_line.startswith("size="):
                        new_conv = parse_duration(stderr_line.split("time=")[1].split()[0]) / duration
                        s.single_download_fraction -= (new_conv - old_conv)
                        s.single_progress_fraction += (new_conv - old_conv)
                        old_conv = new_conv
                        s.refreshvalues()

                popen.stderr.close()
                popen.wait()

                shutil.move(new_filename, name)
                imagepath = "/".join(name.split("/")[:-1]) + "/" + url + ".png"
                generate_image_data([track]).save(imagepath)
                dl_albumart_mp3(name, imagepath)
                file_data = [track[0], track[1], "YouTube", "", "01", "", "None", "None", "Unknown", "Educational"]
                dl_tagify_mp3(name, file_data)
                s.count_convtotal -= 1
                s.count_ytcomplete += 1
                s.single_progress_fraction -= 1
                s.refreshvalues()
                os.remove(filename)
                return
            else:
                s.osi.log("OSI: YT video blocked")
                s.idle = True
                s.refreshvalues()
                return
        else:
            s.osi.log("OSI: YT DL skipped")
            s.idle = True
            s.refreshvalues()
            return

    def idle_conv_watchdog(s, t_id, name, track, recursing=False):  # keeps UI up to date and renames file when done
        for i in os.listdir(s.rootdir):
            if i.endswith(t_id + ".mp3"):
                if recursing:
                    print("Conv size: " + str(os.path.getsize(i)))
                if os.path.getsize(i) < 100 and not recursing:  # found a match
                    s.idle = True
                    s.count_convtotal += 1
                    recursing = True
                elif os.path.getsize(i) > 1 and len([x for x in os.listdir(s.rootdir) if t_id in x]) == 1:
                    try:
                        shutil.move(i, name)
                        imagepath = "/".join(name.split("/")[:-1]) + "/" + t_id + ".png"
                        generate_image_data([track]).save(imagepath)
                        dl_albumart_mp3(name, imagepath)
                        file_data = [track[0], track[1], "YouTube", "", "01", "", "None", "None", "Unknown",
                                     "Educational"]
                        dl_tagify_mp3(name, file_data)
                        s.count_convtotal -= 1
                        s.refreshvalues()
                        return
                    except Exception as e:
                        print("Exception in idle converter watchdog:")
                        print(e)
        s.refreshvalues()
        s.osi.root.after(100, lambda: s.idle_conv_watchdog(t_id, name, track, recursing))  # else, keep looking

    def gp_download(s, track):  # download a single track
        s.idle = False
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

        folderpath, songpath = build_gp_track_path(track)
        
        if os.path.isfile(songpath) and os.path.getsize(songpath) > 0:
            print("Skipping (already downloaded)")
        else:
            dl_url2file(str(s.api.get_stream_url(track[5])), songpath, dlman=s)
            if "albumArt.png" not in os.listdir(folderpath):
                dl_url2file(track[3], (folderpath + "/albumArt.png"))
            dl_albumart_mp3(songpath, folderpath + "/albumArt.png")
            dl_tagify_mp3(songpath, track)

        s.count_gpcomplete += 1
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
