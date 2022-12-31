import email
import imaplib
import csv
import os
import queue
import random
import time
from tkinter import Label, Tk, Menu
from PIL import Image, ImageTk


def scale_img(image, size):
    '''Scales image to fit the largest dimention into size while maintaining the images aspect ratio.'''
    dim = image.size

    if dim[0] > dim[1]:  # find scale ratio
        scale = size[0] / dim[0]
    else:
        scale = size[1] / dim[1]

    # scale image and return it
    return image.resize((int(dim[0]*scale), int(dim[1]*scale)))


def process_image(file_path, size=(800, 480)):
    '''Converts image in path to PhotoImage object for tkinter and scales the image to fit the window.'''
    raw_image = Image.open(file_path)  # open original image
    resized_img = scale_img(raw_image, size)  # resize the image to fit window

    # NOTE: PhotoImage() can only be used after running Tk()
    return ImageTk.PhotoImage(resized_img)  # convert the image for use with tkinter


def get_next_frame():
    '''Select the next Tk image object and message text to display.'''
    try:
        # return the next frame in the queue and True for the new flag
        return new_mail_queue.get(False), True
    except queue.Empty:
        mapping_list = []
        with open(os.path.join(HOME, 'mapping.csv'), newline='') as mapping_file:
            map_reader = csv.reader(mapping_file)
            for frame_row in map_reader:
                mapping_list.append(frame_row)

        # print(f'mapping list: {mapping_list}')
        sel = random.randint(0, len(mapping_list) - 1)

        img_path = os.path.join(HOME, 'imgs', mapping_list[sel][0])
        next_img = process_image(img_path)

        msg_path = os.path.join(HOME, 'msgs', mapping_list[sel][1].strip())
        msg_reader = open(msg_path, 'r')
        next_msg = msg_reader.read()
        msg_reader.close()

        # return the a random frame and False for the new flag
        return (next_img, next_msg), False


def update_display(frame: tuple):
    '''Update the screen with the Tk image object and message text given.'''
    pic_frame.configure(image=frame[0], text=frame[1])


def scrape_email():
    '''Download images and messages from any new emails and add them to the new email queue.'''
    global msg_file_count
    sel_resp = imap.select()
    # print total number of emails in INBOX
    # print('INBOX size:', sel_resp)
    
    # retreive the IDs of unread emails
    resp, unseen_ids = imap.search(None, 'UNSEEN')
    mail_ids = unseen_ids[0].split()
    # print(f'Unread Mail IDs: {mail_ids}\n')

    # print the email content types present in each of the unread emails
    for id in mail_ids:
        # fetch all data from email specified by id
        resp, fetch_data = imap.fetch(id, '(RFC822)')
        # convert the byte data in the email into an email object
        message = email.message_from_bytes(fetch_data[0][1])

        img_file_name = ''
        msg_file_name = ''

        # print out the content type of each part of the email
        # print(f'Email Number: {int(id)}')
        for part in message.walk():
            # print(f'\t{part.get_content_type()}')

            # check for an image file in the email
            if part.get_content_maintype() == 'image':
                img_file_name = part.get_filename()
                # create an image path with the chosen file name
                img_file_path = os.path.join(HOME, 'imgs', img_file_name)
                # if file path does not exist download the new image
                if not os.path.isfile(img_file_path):
                    fp = open(img_file_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

            # check for a plain text message in the email
            if part.get_content_type() == 'text/plain':
                # print(f'\tPayload: {part.get_payload()}')
                msg_file_name = f'msg_{msg_file_count}.txt' # create a message file name
                msg_file_path = os.path.join(HOME, 'msgs', msg_file_name) # create a message file path
                msg_path = open(msg_file_path, 'w')
                msg_path.write(part.get_payload()) # get plain text payload and write to file
                msg_path.close()
                msg_file_count += 1

        if not img_file_name:
            img_file_name = 'default_img.png' # if there is no image then use the default image
            img_file_path = os.path.join(HOME, 'imgs', img_file_name)

        if not msg_file_name:
            msg_file_name = 'empty_msg.txt' # if there is no message then use the empty message file
            msg_file_path = os.path.join(HOME, 'msgs', msg_file_name)

        map_files(img_file_name, msg_file_name)
        next_img = process_image(img_file_path)
        msg_reader = open(msg_file_path, 'r')
        next_msg = msg_reader.read()
        msg_reader.close()
        new_mail_queue.put((next_img, next_msg))


def map_files(img_name, msg_name):
    '''Add the names of an image file and its corresponding message file to the mapping file.'''
    with open(os.path.join(HOME, 'mapping.csv'), 'a', newline='', encoding='UTF-8') as mapper:
        map_writer = csv.writer(mapper)
        map_writer.writerow([img_name, msg_name])


def collect_display_loop():
    '''Main loop which scrapes emails and then displays the collected messages and images on the screen.'''
    scrape_email()
    frame, new = get_next_frame()
    update_display(frame)
    if new:
        for i in range(TIMEOUT_REP-1):
            time.sleep(TIMEOUT/1000)
    window.after(TIMEOUT, collect_display_loop)


def rclick_menu(e):
    exit_menu.tk_popup(e.x_root, e.y_root)


def on_close():
    print('Closing email connection.')
    imap.close()
    imap.logout()
    print('Closing application window.')
    window.quit()


if __name__ == '__main__':
    # user settings
    screen_size = (800, 480)
    TIMEOUT = 20000   # in milliseconds
    TIMEOUT_REP = 3  # in number of loops to repeat
    USERNAME = str("sendcutedogstogf@gmail.com")
    # PASSWORD = str("i<3Uc45S!E")
    IMAP_APP_PASSWORD = str("snirgcrgpvlrqxkk")

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
        # print('imgs folder already exists.')
        pass

    try:  # init messages folder and default message
        os.makedirs(os.path.join(HOME, 'msgs'))  # try to create msgs folder
        creator = open(default_msg_path, mode='wt')
        creator.write('hi <3')
        creator.close()
        creator = open(empty_msg_path, mode='wt')
        creator.close()
        print('Created msgs folder.')
    except(FileExistsError, FileNotFoundError) as e:
        # print('msgs folder already exists.')
        pass

    if 'mapping.csv' in os.listdir(HOME):
        # print('mapping file already exists.')
        pass
    else:
        map_files('default_img.png', 'default_msg.txt')
        print('Created mapping file.')

    # get number of images/messages already sent
    img_file_count = len(os.listdir(os.path.join(HOME, 'imgs')))
    msg_file_count = len(os.listdir(os.path.join(HOME, 'msgs')))

    # log in the user and make connection with gmail
    imap = imaplib.IMAP4_SSL('imap.gmail.com', 993, timeout=120)
    pass_resp = imap.login(USERNAME, IMAP_APP_PASSWORD)
    # print('Login Response:', pass_resp)

    # create window for display
    window = Tk(screenName=None, baseName=None, className='main window')

    # window settings
    window.title('HeartBox Display Window')  # sets window title
    window.geometry(f'{screen_size[0]}x{screen_size[1]}+{0}+{0}')  # sets windows initial size in top left
    window.resizable(0, 0)  # disables window resizing in x and y directions
    window.overrideredirect(0)  # 0 = normal window, 1 = borderless window

    # create a menu obejct and assign it the quit command button
    exit_menu = Menu(window, tearoff=False)
    exit_menu.add_command(label="quit program", command=on_close)

    # bind right click to the quit menu created
    window.bind('<Button-3>', rclick_menu)

    # convert default image to PhotoImage for tkinter and scale image to screen size
    default_img_tk = process_image(default_img_path)

    # create label to diplay images and text
    pic_frame = Label(window, compound='center', font='Helvetica 52 bold', fg='#FFFFFF', bg='#00090F', height=screen_size[1], width=screen_size[0])
    pic_frame.pack()

    # init image/message queue
    new_mail_queue = queue.Queue()

    update_display((default_img_tk, 'hi <3'))

    window.after(1000, collect_display_loop)

    # print('Starting Program Window')
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
