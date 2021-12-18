import threading
import socket
import os
# import vlc
# import time
import pickle
import copy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout

# development parameters
host = '192.168.178.28'
port = 30000
debug_text = 'all kinds of information can be put in this string'

# configuration parameters
PACKET_SIZE = 1024
THUMBNAIL_SIZE = 64


class Ambience():
    name = ""
    b64thumb = None
    tags = []

    music = {}  # track_path | id
    music_vol = {}  # id | volume

    ambient = {}  # track_path | id
    ambient_vol = {}  # id | volume
    ambient_prob = {}  # id | probability

    def __init__(self, name='New Ambience'):
        self.name = name

    def add_music(self, track_orig_path):
        curridx = len(self.music.keys())
        self.music[track_orig_path] = curridx
        self.music_vol[curridx] = 1

    def add_ambient(self, track_orig_path):
        curridx = len(self.ambient.keys())
        self.ambient[track_orig_path] = curridx
        self.ambient_vol[curridx] = 1
        # TODO: properly calculate probability (and possibly)
        # recalculate probability for all other tracks
        self.ambient_prob[curridx] = 1


ambiences = []
ambience_buttons = []

# initialize directories
try:
    os.mkdir("./soundfiles/")
    os.mkdir("./ambiences/")
except Exception:
    pass

# initialize networking
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
uids = []


# -------------------- #
# Networking Functions #
# -------------------- #

# sends a command with content 'cmd' to every connected client
def cmd_broadcast(cmd):
    buffrd_cmd = ("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    for client in clients:
        client.send(buffrd_cmd)


# sends a command with content 'cmd' to the specified client
def cmd_send(client, cmd):
    buffrd_cmd = ("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    client.send(buffrd_cmd)


# transfers a music file to every connected client
def trnsf_music(file):
    print(f"sending file {file} to {len(clients)} clients!")
    cmd_broadcast("trnsfbegin_newfile_mp3")
    packet = file.read(PACKET_SIZE - 4)
    sentsize = 0
    while(packet):
        packet = "TRN@".encode() + packet

        # Make sure even the last packet is PACKET_SIZE in size.
        packet = packet + bytes(PACKET_SIZE - len(packet))
        for client in clients:
            client.send(packet)
        sentsize += PACKET_SIZE - 4  # Leave 4 bytes space for target-prefix
        packet = file.read(PACKET_SIZE - 4)
    cmd_broadcast("trnsfend")
    print("file sent! " + str(sentsize))


# handle an ongoing connection with a client
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


# receive incoming connection attempts by getting identification data,
# and starting a new thread to handle the client
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
        thread.deamon = True
        thread.start()

# tosend = open("tosendfile.mp3", "rb")
# trnsf_music(tosend)


# -------------- #
# Data Functions #
# -------------- #

def write_ambience_to_file(ambience):
    # first resolve duplicate filenames, since filename is based
    # on ambience name
    if(os.path.isfile(f'./ambiences/{ambience.name}')):
        idx = 1
        while True:
            if(os.path.isfile(f'./ambiences/{ambience.name}_{idx}')):
                idx += 1
                continue
            else:
                ambience.name = f'{ambience.name}_{idx}'
                break

    # write to file when a non-duplicate filename is found
    with open(f'./ambiences/{ambience.name}', 'ab') as file:
        pickle.dump(ambience, file)
        print(f'wrote ambience to file ./ambiences/{ambience.name}.')


def load_ambiences_from_file():
    global ambiences
    ambiences.clear()
    counter = 0
    for filename in os.listdir('./ambiences/'):
        with open(f'./ambiences/{filename}', 'rb') as file:
            ambience = pickle.load(file)
            ambiences.append(ambience)
            print(f'loaded ambience with name: {ambience.name}.')
        counter += 1
    print(f'loaded a total of {counter} ambiences!')


def create_new_ambience():
    global ambiences

    new_ambience = Ambience()
    ambiences.append(new_ambience)
    write_ambience_to_file(new_ambience)
    print(f'created and saved new ambience with name: {new_ambience.name}')


def clone_ambience(ambience):
    global ambiences

    new_ambience = copy.deepcopy(ambience)
    ambiences.append(new_ambience)
    write_ambience_to_file(new_ambience)
    print(f'cloned ambience to: {new_ambience.name}')


# ------------- #
# GUI Functions #
# ------------- #

class MainWidget(Widget):
    pass


class MASTER_MainAnchor(AnchorLayout):
    pass


# ---- #
# Main #
# ---- #

class AmbimancerServerApp(App):
    pass


if (__name__ == "__main__"):
    #receive_thread = threading.Thread(target=receive)
    #receive_thread.daemon = True
    #receive_thread.start()

    load_ambiences_from_file()

    # construct and then run the GUI on the main thread
    AmbimancerServerApp().run()

    # debug information if all still running threads are deamons, ergo
    # if they terminate automatically with the main thread
    if(len(threading.enumerate()) > 1):
        print("The following threads were still running, are they daemons?")
        for th in threading.enumerate():
            if(th.name == "MainThread"):
                continue
            print(f"{th.name} :: {th.isDaemon()}")
