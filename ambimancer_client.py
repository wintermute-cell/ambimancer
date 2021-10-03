import socket
import threading
import pyaudio

PACKET_SIZE = 1024

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
        # Make sure a packet of size PACKET_SIZE is received.
        chunks = []
        bytes_recd = 0
        while(bytes_recd < PACKET_SIZE):
            chunk = client.recv(min(PACKET_SIZE - bytes_recd, PACKET_SIZE))
            if(chunk == ''):
                raise RuntimeError("Socket connection broken!")
            chunks.append(chunk)
            bytes_recd += len(chunk)
        packet = b''.join(chunks)

        # Split the packet in target-prefix and data
        target = packet[:3].decode()
        data = packet[4:]
        if(target == "CMD"): # A command was received; assume "data" is utf-8 encoded text
            data = data.decode().rstrip("\x00")
            print(f"CMD: {data}")
            if(data == "uid"):
                print("get there")
                client.send(uid.encode())
            elif(data.startswith("trnsfbegin_")):
                _, name, ftype = data.split("_")
                curr_targetfile = open(f"{name}.{ftype}", "wb")
            elif(data == "trnsfend"):
                curr_targetfile.close()
            else:
                print("Unknown command received, discarding!")
        if(target == "TRN"):
            if(not curr_targetfile):
                print("No current targetfile, trnsfbegin may be missing!")
            else:
                data = data.rstrip(b'\x00')
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
