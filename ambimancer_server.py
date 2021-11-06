import threading
import socket
import os
# import vlc
# import time
import PySimpleGUI as sgui
import base64
from PIL import Image
import json

# development parameters
host = '192.168.178.28'
port = 30000
debug_text = 'all kinds of information can be put in this string'

# configuration parameters
PACKET_SIZE = 1024
THUMBNAIL_SIZE = 64
sgui.theme('DarkAmber')


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


ambiences = [1, 2, 3, 4]
ambience_buttons = []

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


# ------------- #
# GUI Functions #
# ------------- #

# from a user given image, generate base64 image data,
# appropriate for a button thumbnail
def gui_generate_thumb(image_path):
    # crop the image with pil
    raw_path = image_path.encode('unicode_escape')
    pil_img = Image.open(raw_path)

    # crop and scale if required
    width, height = pil_img.size
    if(width > THUMBNAIL_SIZE or height > THUMBNAIL_SIZE):
        # crop the image to quadratic format
        if(width > height):
            abundant_pixels = width - height
            left = abundant_pixels//2
            right = width - (abundant_pixels//2)
            pil_img = pil_img.crop((left, 0, right, height))
        elif(height > width):
            abundant_pixels = height - width
            top = abundant_pixels//2
            bott = height - (abundant_pixels//2)
            pil_img = pil_img.crop((0, top, width, bott))

        # scale down to THUMBNAIL_SIZExTHUMBNAIL_SIZE
        # taken from https://stackoverflow.com/a/451580/16886761
        basewidth = THUMBNAIL_SIZE
        wpercent = (basewidth/float(pil_img.size[0]))
        hsize = int((float(pil_img.size[1])*float(wpercent)))
        pil_img = pil_img.resize((basewidth, hsize), Image.ANTIALIAS)
        pil_img.save(raw_path.decode('utf-8'))

    with open(raw_path, 'rb') as image_file:
        return base64.b64encode(image_file.read())


# first construct the layout, then the complete window, then return the latter
def gui_construct(location=None):
    global ambiences

    top_row = [
        sgui.Column(  # empty column as a spacer
            [[]],
            pad=(0, 0),
            size=(120, 20)
        ),
        sgui.Frame('Search by Name', [[sgui.Input(key='search_name')]]),
        sgui.Frame('Search by Tag', [[sgui.Input(key='search_tag')]])
    ]

    # pregenerate a list of lists with a total of 256 buttons
    def pregen_buttons(layout):
        global ambience_buttons
        for row in range(32):
            rowlist = []
            for b in range(8):
                default_thumb = gui_generate_thumb('./resources/nothumb.png')
                # TODO: scrolling works properly when buttons are
                # initialized as visible
                new_button = sgui.Button(image_size=(64, 64),
                                         image_data=default_thumb,
                                         visible=False)
                ambience_buttons.append(new_button)
                rowlist.append(sgui.Frame('', [[new_button]], border_width=0))
            layout.append(rowlist)
        return

    ambi_button_layout = []
    pregen_buttons(ambi_button_layout)

    mid_row = [
        sgui.Column(
            [[sgui.Frame('', [
                [sgui.Button('Create\nnew', size=(8, 2))],
                [sgui.Button('bttn2')],
                [sgui.Button('bttn3')],
            ])]],
            pad=(0, 0),
            size=(120, 200),
            vertical_alignment='top'
        ),
        sgui.Column(ambi_button_layout,
                    scrollable=True,
                    expand_x=True,
                    size=(600, 900)),
    ]
    global debug_text
    bot_row = [
        sgui.Text(debug_text)
    ]
    layout = [
        [top_row],
        [mid_row],
        [bot_row]
    ]

    window = sgui.Window('Ambimancer Server', layout)
    return window


# run the GUI interaction loop until the window closes or the user quits
def gui_run(window):
    test = True
    while True:
        event, values = window.read(timeout=100)
        if(event == sgui.WIN_CLOSED or event == 'Exit'):
            break

        # the read attempt has timed out, ergo no button was pressed.
        elif(event == '__TIMEOUT__'):
            # run search function
            if(values['search_name'] or values['search_tag']):
                print(values)
                # TODO: remember to strip whitespaces
                # off of the values before using
        else:
            if(event == 'Create\nnew'):
                test = not test
                for button in ambience_buttons:
                    button.update(visible=test)

    # terminate window
    window.close()


# ---- #
# Main #
# ---- #

def load_local_data():
    global ambiences
    # TODO: load ambiences from json


def write_ambience_to_json(ambience):
    testambient = Ambience()
    testambient.b64thumb = gui_generate_thumb('./resources/nothumb.png')
    testambient.tags = ['test', 'debug']
    trackpath = "./soundfiles/Assassin's Creed 3/02 An Uncertain Present.mp3"
    testambient.add_music(trackpath)

    with open('./ambiences.json', 'a') as file:
        dic = testambient.__dict__
        dic['b64thumb'] = dic['b64thumb'].decode('ascii')
        file.write(json.dumps(dic))


if (__name__ == "__main__"):
    #receive_thread = threading.Thread(target=receive)
    #receive_thread.daemon = True
    #receive_thread.start()

    # construct and then run the GUI on the main thread
    gui_run(gui_construct())

    # debug information if all still running threads are deamons, ergo
    # if they terminate automatically with the main thread
    if(len(threading.enumerate()) > 1):
        print("The following threads were still running, are they daemons?")
        for th in threading.enumerate():
            if(th.name == "MainThread"):
                continue
            print(f"{th.name} :: {th.isDaemon()}")
