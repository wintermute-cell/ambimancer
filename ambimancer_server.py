import threading
import socket
import npyscreen as nps
import os

class Soundscape():
    name = ""

    music = {} # track_path | id
    music_vol = {} # id | volume

    ambient = {} # track_path | id
    ambient_vol = {} # id | volume
    ambient_prob = {} # id | propability

    def __init__(self, name):
        self.name = name

    def add_music(track_orig_path):



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
except:
    pass

def cmd_broadcast(cmd):
    buffrd_cmd =("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    for client in clients:
        client.send(buffrd_cmd)

def cmd_send(client, cmd):
    buffrd_cmd =("CMD@" + cmd).encode() + bytes(PACKET_SIZE - len(cmd) - 4)
    client.send(buffrd_cmd)

def trnsf_music(file):
    print(len(clients))
    cmd_broadcast("trnsfbegin_newfile_mp3")
    packet = file.read(PACKET_SIZE - 4)
    sentsize = 0
    while(packet):
        packet = "TRN@".encode() + packet
        packet = packet + bytes(PACKET_SIZE - len(packet)) # Make sure even the last packet
                                                    # is PACKET_SIZE in size.
        for client in clients:
            client.send(packet)
        sentsize += PACKET_SIZE - 4 # Leave 4 bytes space for the target-prefix
        packet = file.read(PACKET_SIZE - 4)
    cmd_broadcast("trnsfend")
    print("file sent! " + str(sentsize))

def handle(client):
    while True:
        try:
            message = client.recv(PACKET_SIZE)
            print(message.decode())
        except:
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

def run_gui(*argv):
    soundscapes_names = []
    for i in range(100):
        soundscapes_names.append(f"yeet nigga {i}")

    form = nps.Form(name="Ambimancer - Server")
    wid_soundscapes = form.add(nps.TitleSelectOne,
            max_height=None,
            value = [1,],
            name="Scapes:",
            values = soundscapes_names,
            scroll_exit=True)

    #t = nps.selectFile("~/")
    #nps.notify_confirm(title="Selfile", message=t)
    form.edit()

if (__name__ == "__main__"):
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    nps.wrapper_basic(run_gui)
