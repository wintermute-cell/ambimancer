import threading
import socket
import os
import tkinter as tk
from tkinter import *
from tkinter import ttk
import vlc
import time


class Soundscape():
    name = ""

    music = {}  # track_path | id
    music_vol = {}  # id | volume

    ambient = {}  # track_path | id
    ambient_vol = {}  # id | volume
    ambient_prob = {}  # id | propability

    def __init__(self, name):
        self.name = name

    def add_music(track_orig_path):
        pass


PACKET_SIZE = 1024

host = '192.168.178.28'
port = 30000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
uids = []

soundscapes = []

try:
    os.mkdir("./soundfiles")
except Exception:
    pass


def cmd_broadcast(cmd):
    buffrd_cmd = ("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    for client in clients:
        client.send(buffrd_cmd)


def cmd_send(client, cmd):
    buffrd_cmd = ("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    client.send(buffrd_cmd)


def trnsf_music(file):
    print(len(clients))
    cmd_broadcast("trnsfbegin_newfile_mp3")
    packet = file.read(PACKET_SIZE - 4)
    sentsize = 0
    while(packet):
        packet = "TRN@".encode() + packet
        packet = packet + bytes(PACKET_SIZE - len(packet))  # Make sure even
        # the last packet
        # is PACKET_SIZE in size.
        for client in clients:
            client.send(packet)
        sentsize += PACKET_SIZE - 4  # Leave 4 bytes space for target-prefix
        packet = file.read(PACKET_SIZE - 4)
    cmd_broadcast("trnsfend")
    print("file sent! " + str(sentsize))


def handle(client):
    while True:
        try:
            message = client.recv(PACKET_SIZE)
            print(message.decode())
        except Exception:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            uid = uids[index]
            cmd_broadcast(f'{uid} left.')
            uids.remove(uid)
            break


def receive():
    while True:
        client, adress = server.accept()
        print(f"{str(adress)} has connected.")
        cmd_send(client, "uid")
        uid = client.recv(PACKET_SIZE).decode()
        uids.append(uid)
        clients.append(client)
        print(f"Nickname for client is {uid}!")
        cmd_send(client, "connected to the server!")
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

#tosend = open("tosendfile.mp3", "rb")
#trnsf_music(tosend)

def guitab_files(tab_files):
    folders = os.listdir("soundfiles")
    folders_list = tk.StringVar(value=folders)
    folders_listbox = tk.Listbox(tab_files,
                                 exportselection=False,
                                 listvariable=folders_list,
                                 height=50,
                                 width=36)
    folders_listbox.grid(column=0, row=0, sticky="nwes")
    folders_scroll = tk.Scrollbar(tab_files)

    preview_inst = vlc.Instance()
    preview_player = vlc.MediaPlayer()

    def folder_selected(event):
        folders_selection_index = folders_listbox.curselection()
        if(not folders_selection_index == ""):
            folders_selection = folders_listbox.get(folders_selection_index)

        allfiles = os.listdir(f"soundfiles/{folders_selection}")
        audiofiles = []
        for file in allfiles:
            if(file.endswith(".mp3")):
                audiofiles.append(file)
        audiofiles.sort()
        allfiles.clear()

        def file_selected(event):
            if(preview_player.is_playing()):
                preview_player.stop()
            files_selection_index = files_listbox.curselection()
            if(not files_selection_index == ""):
                files_selection = files_listbox.get(files_selection_index)
            fileinfo_text = tk.Text(tab_files, height=2, width=50)
            fileinfo_text.insert(INSERT, f"{folders_selection}:\n{files_selection}")
            fileinfo_text.grid(column=2, row=0, sticky="n")
            selectedpath = f"soundfiles/{folders_selection}/{files_selection}"

            time_slider = tk.Scale(tab_files,
                                   from_=0, to=100,
                                   orient=tk.HORIZONTAL,
                                   length=220)
            time_slider.grid(column=2, row=0, sticky="n", pady=80)

            # This controls the progress bar
            def keeptrack():
                restart_keeptrack = False
                while preview_player.get_length() == 0:
                    time.sleep(0.1)
                progress = 0
                # this is to stop the when track changes
                while progress < 100 and restart_keeptrack == False:
                    progress = preview_player.get_time() / preview_player.get_length()
                    progress *= 100
                    time_slider.set(progress)

            def pressed_button_listen():
                if(selectedpath == ""):
                    pass
                else:
                    preview_media = preview_inst.media_new(selectedpath)
                    preview_player.set_media(preview_media)
                    preview_player.play()
                    t = threading.Thread(target=keeptrack)
                    t.daemon = True
                    t.start()

            def pressed_button_stop():
                if(selectedpath == ""):
                    pass
                else:
                    if(preview_player.is_playing()):
                        restart_keeptrack = True
                        preview_player.stop()

            def pressed_button_fwd():
                if(selectedpath == ""):
                    pass
                else:
                    curtime = preview_player.get_time()
                    if(curtime + 10000 <= preview_player.get_length()):
                        preview_player.set_time(preview_player.get_time() + 10000)
                    else:
                        preview_player.set_time(preview_player.get_length())

            def pressed_button_bck():
                if(selectedpath == ""):
                    pass
                else:
                    curtime = preview_player.get_time()
                    if(curtime - 10000 >= 0):
                        preview_player.set_time(preview_player.get_time() - 10000)
                    else:
                        preview_player.set_time(0)

            button_listen = tk.Button(tab_files,
                                      text="Listen",
                                      command=pressed_button_listen)
            button_listen.grid(column=2, row=0, sticky="nw", pady=48, padx=50)

            button_stop = tk.Button(tab_files,
                                    text="Stop",
                                    command=pressed_button_stop)
            button_stop.grid(column=2, row=0, sticky="ne", pady=48, padx=50)

            button_fwd = tk.Button(tab_files,
                                   text="+>>",
                                   command=pressed_button_fwd)
            button_fwd.grid(column=2, row=0, sticky="ne", pady=128, padx=50)

            button_bck = tk.Button(tab_files,
                                   text="<<-",
                                   command=pressed_button_bck)
            button_bck.grid(column=2, row=0, sticky="nw", pady=128, padx=50)

        files_list = tk.StringVar(value=audiofiles)
        files_listbox = tk.Listbox(tab_files,
                                   exportselection=False,
                                   listvariable=files_list,
                                   height=50,
                                   width=36)
        files_listbox.grid(column=1, row=0, sticky="nwse")
        files_listbox.bind('<<ListboxSelect>>', file_selected)

    folders_listbox.bind('<<ListboxSelect>>', folder_selected)

    tab_files.grid_columnconfigure(0, weight=1)
    tab_files.grid_columnconfigure(1, weight=1)
    tab_files.grid_columnconfigure(2, weight=1)
    tab_files.grid_columnconfigure(3, weight=1)
    tab_files.grid_columnconfigure(4, weight=1)
    tab_files.grid_rowconfigure(0, weight=1)
    tab_files.grid_rowconfigure(1, weight=1)
    tab_files.grid_rowconfigure(2, weight=1)
    tab_files.grid_rowconfigure(3, weight=1)
    tab_files.grid_rowconfigure(4, weight=1)


def guitab_main(tab_main):
    # TODO: plan and implement main tab
    pass


def guitab_edit_create(tab_edit_create):
    # Create Folder list
    folders = os.listdir("soundfiles")
    folders_list = tk.StringVar(value=folders)
    folders_listbox = tk.Listbox(tab_edit_create,
                                 exportselection=False,
                                 listvariable=folders_list,
                                 height=50,
                                 width=36)
    folders_listbox.grid(column=0, row=0, sticky="nwes")
    folders_scroll = tk.Scrollbar(tab_edit_create)

    # Precreate an the empty file list.
    audiofiles = []
    # If there are folders, open the first one
    if(len(folders) > 0):
        folders_selection = folders_listbox.get(0)
        allfiles = os.listdir(f"soundfiles/{folders_selection}")
        audiofiles = []
        for file in allfiles:
            if(file.endswith(".mp3")):
                audiofiles.append(file)
        audiofiles.sort()
        allfiles.clear()
    files_list = tk.StringVar(value=audiofiles)
    files_listbox = tk.Listbox(tab_edit_create,
                               selectmode="multiple",
                               exportselection=False,
                               listvariable=files_list,
                               height=50,
                               width=36)
    files_listbox.grid(column=1, row=0, sticky="nwse")

    # Create control elements on the right
    # Dropdown
    soundscape_names = ["---"]
    for soundscape in soundscapes:
        soundscape_names.append(soundscape.name)
    soundscape_droplist = tk.StringVar(value=soundscape_names)
    if(len(soundscapes) > 0):
        soundscape_droplist.set(soundscapes[0].name)
    else:
        soundscape_droplist.set("---")

    soundscape_drop = tk.OptionMenu(
        tab_edit_create,
        soundscape_droplist,
        *soundscape_names)
    soundscape_drop.grid(column=2, row=0, sticky="nwe")

    def pressed_button_stop():
        if(selectedpath == ""):
            pass
        else:
            if(preview_player.is_playing()):
                restart_keeptrack = True
                preview_player.stop()
    button_stop = tk.Button(tab_edit_create,
                            text="Stop",
                            command=pressed_button_stop)
    button_stop.grid(column=2, row=0, sticky="ne", pady=48, padx=50)

    def folder_selected(event):
        folders_selection_index = folders_listbox.curselection()
        if(not folders_selection_index == ""):
            folders_selection = folders_listbox.get(folders_selection_index)

        # Fetch all filenames from the folder, clear the file list, and then add
        # all the new files to the file list
        allfiles = os.listdir(f"soundfiles/{folders_selection}")
        audiofiles = []
        for file in allfiles:
            if(file.endswith(".mp3")):
                audiofiles.append(file)
        audiofiles.sort()
        allfiles.clear()
        files_listbox.delete(0, tk.END)
        for file in audiofiles:
            files_listbox.insert(tk.END, file)

        def file_selected(event):
            files_selection_index = files_listbox.curselection()
            if(not files_selection_index == ""):
                files_selection = files_listbox.get(files_selection_index)
            selectedpath = f"soundfiles/{folders_selection}/{files_selection}"

        files_listbox.bind('<<ListboxSelect>>', file_selected)

    folders_listbox.bind('<<ListboxSelect>>', folder_selected)

    tab_edit_create.grid_columnconfigure(0, weight=1)
    tab_edit_create.grid_columnconfigure(1, weight=1)
    tab_edit_create.grid_columnconfigure(2, weight=1)
    tab_edit_create.grid_columnconfigure(3, weight=1)
    tab_edit_create.grid_columnconfigure(4, weight=1)
    tab_edit_create.grid_rowconfigure(0, weight=1)
    tab_edit_create.grid_rowconfigure(1, weight=1)
    tab_edit_create.grid_rowconfigure(2, weight=1)
    tab_edit_create.grid_rowconfigure(3, weight=1)
    tab_edit_create.grid_rowconfigure(4, weight=1)


def run_gui(*argv):
    # CONSTRUCT BASIC FRAME AND TABS
    root = tk.Tk()
    root.title("Ambimancer - Server")
    root.geometry("1280x720")
    myLabel = tk.Label(root, text="Ambimancer - Server")
    myLabel.pack()

    tab_container = ttk.Notebook(root)
    tab_main = ttk.Frame(tab_container)
    tab_edit_create = ttk.Frame(tab_container)
    tab_files = ttk.Frame(tab_container)

    tab_container.add(tab_main, text="Main")
    tab_container.add(tab_edit_create, text="Edit/Create")
    tab_container.add(tab_files, text="Files")

    tab_container.pack(expand=1, fill="both")

    # CONSTRUCT FILES TAB
    guitab_files(tab_files)

    # CONSTRUCT MAIN TAB
    guitab_main(tab_main)

    # CONSTRUCT EDIT/CREATE TAB
    guitab_edit_create(tab_edit_create)

    root.mainloop()
    print("terminated")


if (__name__ == "__main__"):
    #receive_thread = threading.Thread(target=receive)
    #receive_thread.daemon = True
    #receive_thread.start()

    run_gui()

    if(len(threading.enumerate()) > 1): # if more threads than just main thread
        print("The following threads were still running, are they daemons?")
        for th in threading.enumerate():
            if(th.name == "MainThread"):
                continue
            print(f"{th.name} :: {th.isDaemon()}")
