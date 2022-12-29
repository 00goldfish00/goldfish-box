import email
from io import BytesIO
# import rfc822
import poplib
import os
import shutil
import queue
import random
import string
import threading
import time
from tkinter import Canvas, Label, Tk, Menu
from PIL import Image, ImageTk
import base64


def scale_img(image, size):
    '''Scales image to fit the largest dimention into size while maintaining the images aspect ratio.'''
    dim = image.size

    if dim[0] > dim[1]:  # find scale ratio
        scale = size[0] / dim[0]
    else:
        scale = size[1] / dim[1]

    # scale image and return it
    return image.resize((int(dim[0]*scale), int(dim[1]*scale)))


def process_image(file_name, size=(800, 480), dir=''):
    '''Converts image in path to PhotoImage object for tkinter and scales the image to fit the window.'''
    if not file_name.endswith('.\\*'):
        img_path = default_img_path  # if given file does not have a file extension
    else:
        img_path = os.path.join(dir, 'images', file_name)

    raw_image = Image.open(img_path)  # open original image
    resized_img = scale_img(raw_image, size)  # resize the image to fit window

    # NOTE: PhotoImage() can only be used after running Tk()
    return ImageTk.PhotoImage(resized_img)  # convert the image for use with tkinter


def get_next_frame():
    '''Select the next Tk image object and message text to display.'''
    if new_mail_queue.not_empty:
        return new_mail_queue.get(False)

    map_reader = open(os.path.join(HOME, 'mapping.txt'))
    mapping_list = [line.split(',') for line in map_reader.readlines()]
    sel = random.randint(0, len(mapping_list) - 1)

    img_path = os.path.join(HOME, 'imgs', mapping_list[sel][0])
    next_img = process_image(img_path, dir=HOME)

    msg_path = os.path.join(HOME, 'msgs', mapping_list[sel][1])
    msg_reader = open(msg_path, 'r')
    next_msg = msg_reader.read()
    msg_reader.close()

    return (next_img, next_msg)


def update_display(frame: tuple):
    '''Update the screen with the Tk image object and message text given.'''
    pic_frame.configure(image=frame[0], text=frame[1])


def scrape_email():
    '''Download images and messages from any new emails and add them to the new email queue.'''
    # check inbox
    message_count, mailbox_size = pop3.stat()
    print('Message Count:', message_count, 'Inbox Size:', mailbox_size, 'bytes')

    # total number of emails
    response, mesg_num_octets, octets = pop3.list()
    print(f'Response: {response}')
    print('Number of messages:', len(mesg_num_octets), '\n', mesg_num_octets)
    # download a random message
    id, size = random.choice(mesg_num_octets).split()
    print(id, size)
    resp, text, octets = pop3.retr(int(id))
    bytes_cat = b''.join(text)
    # bytes_obj = BytesIO()
    message = email.message_from_bytes(bytes_cat)

    for part in message.walk():
        print(part.get_content_type())


    # message = rfc822.Message(file)

    # for k, v in message.items():
    #     print(k, "=", v)

    # print(message.fp.read())
    return
    # for i in range(1): #range(len(mesg_num_octets)):
    #     print('Number of bytes objects:', len(pop3.retr(i+1)[1]))
    #     for j in pop3.retr(i+1)[1]:
    #         try:
    #             # print(j)#, type(j), len(j))
    #             # b64code = j.decode("utf-8")
    #             # code_with_padding = j.strip() + (b'====')  # * (4 - len(j.strip()) % 4)
    #             # print(code_with_padding, len(code_with_padding))
    #             decoded_msg = base64.b64decode(j).decode("utf-8")
    #             print(decoded_msg)
    #         except base64.binascii.Error:
    #             print("Error")
    #             pass

    
    # # fetch emails from all users
    # # key, data = pop3.search(None, 'UNSEEN')
    # # mail_ids = data[0].split()

    # # read through all new emails and download contents
    # # for m in range(len(mesg_num_octets)):

    # #     mail_data = pop3.retr(m+1)
    # #     print('Mail Data:\n', mail_data, '\n')
    #     # raw_email = mail_data[0][1]

    #     # raw_strings = raw_email.decode('utf-8')
    #     message = email.message_from_bytes(raw_strings)

    #     for part in message.walk():

    #     #     # check for a file in the email
    #     #     img_file_name = part.get_filename()
    #     #     if bool(img_file_name):
    #     #         img_file_path = os.path.join(HOME, 'imgs', f'{img_file_name}')
    #     #         if not os.path.isfile(img_file_path):
    #     #             # if file does not exist download it
    #     #             fp = open(img_file_path, 'wb')
    #     #             fp.write(part.get_payload(decode=True))
    #     #             fp.close()
    #     #     else:
    #     #         # if there is no file then use the default image
    #     #         img_file_name = 'default_img.png'
    #     #         img_file_path = os.path.join(HOME, 'imgs', img_file_name)

    #     #     # check for a message in the email
    #     #     if part.get_content_type() == 'text/plain':
    #     #         # ignore image file names
    #     #         if img_file_name:
    #     #             continue
    #     #         payload = part.get_payload()
    #     #         if payload.find('.jpg') > -1 or payload.find('.png') > -1:
    #     #             continue

    #     #         # if text is found then create a message file
    #     #         msg_file_name = f'msg_{msg_file_count}.txt'
    #     #         msg_file_path = os.path.join(HOME, 'msgs', msg_file_name)
    #     #         msg_path = open(msg_file_path, 'w')
    #     #         msg_path.write(payload)
    #     #         msg_path.close()
    #     #         txt_file_count += 1
    #     #     else:
    #     #         # if there is no message then use the empty message file
    #     #         msg_file_name = 'empty_msg.txt'
    #     #         msg_file_path = os.path.join(HOME, 'msgs', msg_file_name)

    #     # map_files(img_file_name, msg_file_name)
    #     # next_img = process_image(img_file_path, dir=HOME)
    #     # msg_reader = open(msg_file_path, 'r')
    #     # next_msg = msg_reader.read()
    #     # msg_reader.close()
    #     # new_mail_queue.put((next_img, next_msg))


def map_files(img_name, msg_name):
    '''Add the names of an image file and its corresponding message file to the mapping file.'''
    # Update this to use the 'with' operator
    mapper = open(os.path.join(HOME, 'mapping.txt'), mode='wt', encoding='UTF-8')
    mapper.write(f'{img_name}, {msg_name}\n')
    mapper.close()


def collect_display_loop():
    '''Main loop which scrapes emails and then displays the collected messages and images on the screen.'''
    scrape_email()
    frame, new = get_next_frame()
    update_display(frame)
    if new:
        for i in range(TIMEOUT_REP):
            time.sleep(TIMEOUT/1000)
            update_display(frame)
    window.after(TIMEOUT, collect_display_loop)


def rclick_menu(e):
    exit_menu.tk_popup(e.x_root, e.y_root)


def on_close():
    print('Closing email connection.')
    pop3.quit()
    print('Closing application window.')
    window.quit()


if __name__ == '__main__':
    # user settings
    screen_size = (800, 480)
    TIMEOUT = 3600000   # in milliseconds
    TIMEOUT_REP = 3  # in number of loops to repeat
    USERNAME = str("sendcutedogstogf@gmail.com")
    # PASSWORD = str("i<3Uc45S!E")
    PASSWORD = str("hcuxitpskrovjkkn")

    # sender email addresses for filtering spam
    phone_email = '+14847565113@tmomail.net'
    personal_email = 'dp53899@gmail.com'

    # program settings
    HOME = os.curdir  # path.join(os.curdir, 'GoldfishBox')
    default_img_path = os.path.join(HOME, 'imgs', 'default_img.png')
    default_msg_path = os.path.join(HOME, 'msgs', 'default_msg.txt')
    empty_msg_path = os.path.join(HOME, 'msgs', 'empty_msg.txt')
    search_label = 'Inbox'
    screen_cen = screen_size[0]/2, screen_size[1]/2
    new_timeout_count = 0

    try:  # init images folder and default image
        os.makedirs(os.path.join(HOME, 'imgs'))  # try to create imgs folder
        black_img = Image.new(mode = "RGB", size = screen_size)
        black_img.save(default_img_path)
        print('Created imgs folder.')
    except (FileExistsError, FileNotFoundError) as e:
        print('imgs folder already exists.')

    try:  # init messages folder and default message
        os.makedirs(os.path.join(HOME, 'msgs'))  # try to create msgs folder
        creator = open(default_msg_path, mode='wt')
        creator.write('hi <3')
        creator.close()
        creator = open(empty_msg_path, mode='wt')
        creator.close()
        print('Created msgs folder.')
    except(FileExistsError, FileNotFoundError) as e:
        print('msgs folder already exists.')

    if 'mapping.txt' in os.listdir(HOME):
        print('mapping file already exists.')
    else:
        map_files('default_img.png', 'default_msg.txt')
        print('Created mapping file.')

    # get number of images/messages already sent
    img_file_count = len(os.listdir(os.path.join(HOME, 'imgs')))
    msg_file_count = len(os.listdir(os.path.join(HOME, 'msgs')))

    # log in the user and make connection with gmail for scraping emails
    pop3 = poplib.POP3_SSL('pop.gmail.com', 995, timeout=120, )
    pass_req = pop3.user(USERNAME)
    print('Username Response:', pass_req)
    if pass_req:
        print('Sending Password')
        pop3.pass_(PASSWORD)
    else:
        print("Error logging in.")
        pop3.quit()
        quit()

    # create window for display
    window = Tk(screenName=None, baseName=None, className='main window')

    # window settings
    window.title('HeartBox Display Window')  # sets window title
    window.geometry(f'{screen_size[0]}x{screen_size[1]}+{0}+{0}')  # sets windows initial size in top left
    #window.resizable(0, 0)  # disables window resizing in x and y directions
    window.overrideredirect(1)  # 0 = normal window, 1 = borderless window01

    # create a menu obejct and assign it the quit command button
    exit_menu = Menu(window, tearoff=False)
    exit_menu.add_command(label="quit program", command=on_close)

    # bind right click to the quit menu created
    window.bind('<Button-3>', rclick_menu)

    # convert default image to PhotoImage for tkinter and scale image to screen size
    default_img_tk = process_image(default_img_path, dir=HOME)

    # create label to diplay images and text
    pic_frame = Label(window, compound='center', font='Helvetica 52 bold', fg='#FFFFFF', bg='#00090F', height=screen_size[1], width=screen_size[0])
    pic_frame.pack()

    # init image/message queue
    new_mail_queue = queue.Queue()

    update_display((default_img_tk, 'hi <3'))

    scrape_email()

    # window.after(1000, collect_display_loop)

    print('Starting Program Window')
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
