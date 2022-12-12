import email
import imaplib
import os
import shutil
import queue
import random
import threading
import time
from tkinter import Canvas, Label, Tk, Menu
from PIL import Image, ImageTk


def clean(text):    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


def get_body(msg):  # get email content i.e body
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


def get_emails(result_bytes):  # get list of emails under label
    msgs = []  # all the email data are pushed inside an array
    for num in result_bytes[0].split():
        type, data = imap.fetch(num, '(RFC822)')
        msgs.append(data)
    return msgs


def scale_img(image, size):
    '''Scales image to fit largest dimention into size while maintaining aspect ratio'''

    dim = image.size

    # find scale ratio
    if dim[0] > dim[1]:
        scale = size[0] / dim[0]
    else:
        scale = size[1] / dim[1]

    # scale image and return it
    return image.resize((int(dim[0]*scale), int(dim[1]*scale)))


def process_image(file_name, size=(800, 480), dir=''):
    '''Converts image in path to PhotoImage object for tkinter and scales the image to fit the screen size'''

    img_path = os.path.join(dir, 'images', file_name)

    # if given file path does not end with .[image_type]
    if not img_path.endswith('.\\*'):
        img = default_img_path

    raw_image = Image.open(img_path)  # open original image
    resized_img = scale_img(raw_image, size)  # resize the image to fit window

    # processed_image = ImageTk.PhotoImage(resized_img)

    # convert the image for use with tkinter
    # Note: PhotoImage() can only be used after running Tk()
    return ImageTk.PhotoImage(resized_img)


def label_display_image(next_frame):
    global new_img_timeout, new_timeout_count

    if new_timeout_count > new_img_timeout:
        new_timeout_count = 0

    if new_timeout_count < 1:
        try:
            next_frame = img_queue.get(False)
            new_timeout_count = 1
        except queue.Empty:
            image_list = os.listdir(os.path.join(home, 'images'))
            image_list.sort()
            image_paths = [os.path.join(home, 'images', file) for file in image_list]
            # last_img = max(image_paths, key=os.path.getctime)
            # print('newest image file:', last_img)

            message_list = os.listdir(os.path.join(home, 'messages'))
            message_list.sort()
            message_paths = [os.path.join(home, 'messages', file) for file in message_list]
            # last_msg = max(message_paths, key=os.path.getctime)
            # print('newest message file:', last_msg)

            sel = random.randint(0, len(image_paths) - 1)
            # print(len(image_paths) - 1)

            img_path = os.path.join(home, 'images', image_paths[sel])
            next_img = process_image(img_path, dir=home)

            msg_path = os.path.join(home, 'messages', message_paths[sel])
            msg_reader = open(msg_path, 'r')
            next_msg = msg_reader.read()
            msg_reader.close()

            next_frame = (next_img, next_msg)
    else:
        new_timeout_count += 1

    # uncomment to display the current frame in the queue
    #print(f'frame in queue:\n{str(next_frame[0])}\n{next_frame[1]}')
    pic_frame.configure(image=next_frame[0], text=next_frame[1])

    window.after(disp_timeout, label_display_image, next_frame)


def email_scraper():

    global txt_file_count, img_file_count, new_img_timeout, new_timeout_count

    while True:
        # calling function to check inbox
        status, emails = imap.select("Inbox")
        # print('"emails" variable:', emails)

        # total number of emails
        msg_count = int(emails[0])
        # print('total message count:', msg_count)

        # fetch emails from all users
        key, data = imap.search(None, 'UNSEEN')
        mail_ids = data[0].split()
        #print('new e-mails:', len(mail_ids))

        # Uncomment to see raw data
        #messages = get_emails(data)
        #print('get_emails(data):\n', messages, '\nend of message output\n')

        # read through all emails and collect contents
        for ids in mail_ids:

            mail_type, mail_data = imap.fetch(ids, '(RFC822)')
            raw_email = mail_data[0][1]

            raw_strings = raw_email.decode('utf-8')
            message = email.message_from_string(raw_strings)

            for part in message.walk():
                img_file_name = part.get_filename()
                img_file_path = ''

                msg_file_name = f'{txt_file_count}_message.txt'
                msg_file_path = ''
                msg_contents = ''
                
                if bool(img_file_name):
                    img_file_path = os.path.join(home, 'images', f'{img_file_count}_{img_file_name}')
                    if not os.path.isfile(img_file_path):
                        # if file does not exist download it
                        fp = open(img_file_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                        # uid=ids.decode('utf-8')
                        #print(f'Downloaded "{img_file_name}"')
                        img_file_count += 1
                    else:
                        img_file_path = ''

                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get_content_type() == 'text/plain':
                    if img_file_name:
                        continue
                    payload = part.get_payload()
                    if payload.find('.jpg') > -1 or payload.find('.png') > -1:
                        continue
                    
                    msg_file_path = os.path.join(home, 'messages', msg_file_name)
                    msg_path = open(msg_file_path, 'w')
                    msg_path.write(payload)
                    msg_path.close()
                    msg_contents = payload
                    #print(f'Created message file "{msg_file_name}"')
                    txt_file_count += 1

            if bool(img_file_path):
                tmp_img = process_image(img_file_path)
                img_queue.put((tmp_img, msg_contents))
            else:
                tmp_path = os.path.join(home, 'images', f'{txt_file_count}_black.png')
                shutil.copyfile(default_img_path, tmp_path)

                tmp_img = process_image(default_img_path)
                img_queue.put((tmp_img, msg_contents))

        #print('sleeping for:', 5, 'seconds')
        time.sleep(disp_timeout/2000)


def on_close():
    print('closing email connection and logging out')
    imap.close()
    imap.logout()
    print('closing window')
    window.quit()


if __name__ == '__main__':

    # user settings
    screen_size = 800, 480
    disp_timeout = 3600000
    new_img_timeout = 3
    username = 'sendcutedogstogf@gmail.com'
    password = 'i<3Uc45S!E'

    # sender email addresses for filtering spam
    phone_email = '+14847565113@tmomail.net'
    personal_email = 'dp53899@gmail.com'

    # program settings
    home = '//home//pi//GoldfishBox'
    default_img_path = os.path.join(home, 'images', 'black.png')
    default_msg_path = os.path.join(home, 'messages', 'message.txt')
    default_msg = 'hi <3'
    search_label = 'Inbox'
    screen_cen = screen_size[0]/2, screen_size[1]/2
    new_timeout_count = 0

    # init images folder and default image
    try:
        images_path = os.path.join(home, 'images')
        os.makedirs(images_path)

        black_img = Image.new(mode = "RGB", size = screen_size)
        black_img.save(default_img_path)
        print('created "images" folder')
    except (FileExistsError, FileNotFoundError) as e:
        print('"images" folder already exists')

    # init messages folder and default message
    try:
        messages_path = os.path.join(home, 'messages')
        os.makedirs(messages_path)

        creator = open(default_msg_path, mode='wt')
        creator.write(default_msg)
        creator.close()
        print('created "messages" folder')
    except(FileExistsError, FileNotFoundError) as e:
        print('"messages" folder already exists')

    # get number of images/messages already sent
    img_file_count = len(os.listdir(os.path.join(home, 'images')))
    txt_file_count = len(os.listdir(os.path.join(home, 'messages')))

    # make SSL connection with GMAIL for collecting emails
#    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    # log in the user
#    imap.login(username, password)

    # create window for display
    window = Tk(screenName=None, baseName=None, className='main window')

    # window settings
    window.title('HeartBox Display Window')  # sets window title
    window.geometry(f'{screen_size[0]}x{screen_size[1]}+{0}+{0}')  # sets windows initial size in top left
    #window.resizable(0, 0)  # disables window resizing in x and y directions
    window.overrideredirect(1)  # 0 = normal window, 1 = borderless window

    exit_menu = Menu(window, tearoff=False)
    exit_menu.add_command(label="quit program", command=on_close)

    def rclick_menu(e):
        exit_menu.tk_popup(e.x_root, e.y_root)

    window.bind('<Button-3>', rclick_menu)

    # convert default image to PhotoImage for tkinter and scale image to screen size
    default_img_tk = process_image(default_img_path, dir=home)

    # create label to diplay images and text
    pic_frame = Label(window, compound='center', font='Helvetica 52 bold', fg='#FFFFFF', bg='#00090F', height=screen_size[1], width=screen_size[0])
    pic_frame.pack()

    # init image/message queue
    img_queue = queue.Queue()

    # download images and collect messages form emails
#    download_thread = threading.Thread(target=email_scraper, args=())
#    download_thread.daemon = True
#    download_thread.start()

    window.after(1000, label_display_image, (default_img_tk, default_msg))

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
