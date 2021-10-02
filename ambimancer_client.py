import socket
import threading
import pyaudio

# Init networking
uid = input("uid: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('winter-mute.xyz', 30000))

# Init audio
music_queue = []

# Networking functions
def receive():
    curr_targetfile = None
    while True:
        packet = client.recv(1024)
        target = packet[:3].decode()
        data = packet[4:]
        print(f"recieved instruction: {target}")
        if(target == "CMD"):
            data = data.decode()
            print(f"CMD: {data}")
            if(data == "uid"):
                client.send(uid.encode())
            elif(data.startswith("trnsfbegin_")):
                _, name, ftype = data.split("_")
                curr_targetfile = open(f"{name}.{ftype}", "wb")
            elif(data == "trnsfend"):
                curr_targetfile.close()
        if(target == "TRN"):
            if(not curr_targetfile):
                print("No current targetfile, trnsfbegin may be missing!")
            else:
                curr_targetfile.write(data)

def write():
    while True:
        message = f'{uid}: {input("")}'
        client.send(message.encode())

# Begin networking
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

# Audio functions
#def music_queue():

#def music_start():

#def music_pause():
