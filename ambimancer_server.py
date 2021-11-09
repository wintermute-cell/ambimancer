import threading
import socket
import os
# import vlc
# import time
import PySimpleGUI as sgui
import base64
from PIL import Image
import pickle
import copy

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


def gui_init_buttons():
    global ambience_buttons
    global ambiences

    curr_num_buttons = 0
    max_num_buttons = len(ambiences)

    # make a button visible for each loaded ambience_buttons
    # and apply the saved thumbnail to it
    for button in ambience_buttons:
        if(curr_num_buttons >= max_num_buttons):
            break
        button.update(image_data=ambiences[curr_num_buttons].b64thumb,
                      visible=True)
        curr_num_buttons += 1


# first construct the layout, then the complete window, then return the latter
def gui_construct(location=None):
    global ambiences

    # BEGIN main layout
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

        button_idx = 0
        for row in range(32):
            rowlist = []
            for b in range(8):
                default_thumb = gui_generate_thumb('./resources/nothumb.png')
                rcm = ['', [f'Edit::{button_idx}',
                            f'Duplicate::{button_idx}',
                            f'Remove::{button_idx}']]
                new_button = sgui.Button(image_size=(64, 64),
                                         image_data=default_thumb,
                                         visible=True,
                                         right_click_menu=rcm)
                ambience_buttons.append(new_button)
                rowlist.append(sgui.Frame('', [[new_button]], border_width=0))
                button_idx += 1
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
    main_layout = [
        top_row,
        mid_row,
        bot_row
    ]
    # END main layout

    # BEGIN edit layout
    edit_layout = [[sgui.Button('Edit::1')]]
    # TODO: implement edit view layout.
    # END edit layout

    window = sgui.Window('Ambimancer Server', [[
                          sgui.Column(main_layout, k='main'),
                          sgui.Column(edit_layout, k='edit', visible=False)]],
                         finalize=True)

    # this is a hacky workaround for the issue that when the buttons get
    # initialized as invisible (even with frame parent), the layout
    # is broken.
    for button in ambience_buttons:
        button.update(visible=False)

    return window


def gui_enter_editmode(window, ambience_index):
    window['main'].update(visible=False)
    window['edit'].update(visible=True)


def gui_exit_editmode(window):
    window['main'].update(visible=True)
    window['edit'].update(visible=False)


def gui_handle_rightclick(event, button_id, window):
    global ambiences
    global ambience_buttons

    if(event == 'Edit'):
        if(window['main'].visible):
            gui_enter_editmode(window, 0)
        else:
            gui_exit_editmode(window)

    elif(event == 'Duplicate'):
        clone_ambience(ambiences[button_id])
        for button in ambience_buttons:
            if(not button.visible):
                button.update(visible=True,
                              image_data=ambiences[button_id].ImageData)
                break

    elif(event == 'Remove'):
        # first confirm user intent with a popup
        confirmation = sgui.popup_ok_cancel('Permanently remove Ambience?')
        if(confirmation != 'OK'):
            return

        # try to remove the file
        try:
            os.remove(f'./ambiences/{ambiences[button_id].name}')
        except Exception:
            print(f'file with name {ambiences[button_id].name} already gone!')

        # remove the ambience from memory
        del ambiences[button_id]

        # correct the buttons
        for idx in range(button_id, len(ambience_buttons)-2):

            # if this is the last visible button,
            # just remove its thumbnail and make it invisible
            if(not ambience_buttons[idx+1].visible):
                nothumb = gui_generate_thumb('./resources/nothumb.png')
                ambience_buttons[idx].update(visible=False,
                                             image_data=nothumb)
                break

            # shift the thumbnail data from the next button
            # to this one
            else:
                image_data = ambience_buttons[idx+1].ImageData
                ambience_buttons[idx].update(image_data=image_data)


# run the GUI interaction loop until the window closes or the user quits
def gui_run(window):
    global ambience_buttons
    global ambiences

    # initialize gui state
    gui_init_buttons()

    # main gui loop
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
            print(event)
            # extract the id from the event if necessary
            if('::' in event):
                event, button_id = event.split('::')
                button_id = int(button_id)

            if(event == 'Create\nnew'):
                create_new_ambience()
                for button in ambience_buttons:
                    if(not button.visible):
                        button.update(visible=True)
                        break
            elif(event in ['Edit', 'Duplicate', 'Remove']):
                gui_handle_rightclick(event, button_id, window)

    # terminate window
    window.close()


# ---- #
# Main #
# ---- #

if (__name__ == "__main__"):
    #receive_thread = threading.Thread(target=receive)
    #receive_thread.daemon = True
    #receive_thread.start()

    load_ambiences_from_file()

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
