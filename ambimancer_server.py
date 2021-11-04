import threading
import socket
import os
import vlc
import time

# development parameters
host = '192.168.178.28'
port = 30000

# configuration parameters
PACKET_SIZE = 1024


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


soundscapes = []

# try to make soundfiles dir if it doesn't already exist
try:
    os.mkdir("./soundfiles")
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


if (__name__ == "__main__"):
    # receive_thread = threading.Thread(target=receive)
    # receive_thread.daemon = True
    # receive_thread.start()

    # debug information if all still running threads are deamons, ergo
    # if they terminate automatically with the main thread
    if(len(threading.enumerate()) > 1):  # if more threads than just main thread
        print("The following threads were still running, are they daemons?")
        for th in threading.enumerate():
            if(th.name == "MainThread"):
                continue
            print(f"{th.name} :: {th.isDaemon()}")
