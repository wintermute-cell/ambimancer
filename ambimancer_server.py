import threading
import socket
import time

host = '192.168.178.28'
port = 30000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
uids = []

def cmd_broadcast(cmd):
    for client in clients:
        client.send(("CMD@" + cmd).encode())

def cmd_send(client, cmd):
    client.send(("CMD@" + cmd).encode())

def trnsf_music(file):
    print("trnsf clients: ".join(str(e) for e in clients))
    cmd_broadcast("trnsfbegin_newfile_mp3")
    packet = file.read(1020)
    packet = "TRN@".encode() + packet
    sentsize = 0
    while(packet):
        for client in clients:
            client.send(packet)
        print(f"sent: {packet}")
        time.sleep(0.05)
        sentsize += 1020
        packet = file.read(1020)
        packet = "TRN@".encode() + packet
    print("file sent! " + str(sentsize))

def handle(client):
    while True:
        try:
            message = client.recv(1024)
            #print(message.decode())
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
        uid = client.recv(1024).decode()
        uids.append(uid)
        clients.append(client)
        print(f"Nickname for client is {uid}!")
        cmd_send(client, "connected to the server!")
        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

receive_thread = threading.Thread(target=receive)
receive_thread.start()
time.sleep(6)
print("done waiting")

tosend = open("tosendfile.mp3", "rb")
trnsf_music(tosend)
