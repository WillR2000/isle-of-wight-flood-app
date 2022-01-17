import os
import csv
import tkinter.messagebox
import smtplib
from tkinter import *
from ERROR import CheckError
from PIL import Image, ImageTk
from tkinter.filedialog import askdirectory
from plotter_additional_features import Plotter
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from classes_additional_features import UserInput, NearestItn, HighestPoint, ShortestPath, Transform


class Window:

    # Construct the window frame.
    def __init__(self):
        self.root = Tk()

        # Beautify the background with UCL logo.
        self.im_root = ImageTk.PhotoImage(Image.open('ucl.png'))
        self.canvas_root = Canvas(self.root, width=360, height=300)
        self.canvas_root.create_image(320, 260, image=self.im_root)
        self.canvas_root.pack()

        # Set attributes of some variables.
        self.v1 = StringVar()
        self.v2 = StringVar()
        self.v3 = StringVar()
        self.v4 = IntVar()
        self.folderpath = StringVar()

        # Set the default path.
        self.folderpath.set(os.path.abspath("."))

        # Limit users to only enter numbers.
        self.testCMD = self.root.register(self.test)

        # Set the style and function of each component.
        self.l1 = Label(self.root, text='Easting:')
        self.l2 = Label(self.root, text='Northing:')
        self.l3 = Label(self.root, text="Path:")
        self.l4 = Label(self.root, text='Mail address:')
        self.e1 = Entry(self.root, width=25, textvariable=self.v1, validate='key',
                        validatecommand=(self.testCMD, '%P'))
        self.e2 = Entry(self.root, width=25, textvariable=self.v2, validate='key',
                        validatecommand=(self.testCMD, '%P'))
        self.e3 = Entry(self.root, textvariable=self.v3, validate='key')
        self.e4 = Entry(self.root, textvariable=self.folderpath, state="readonly")
        self.b1 = Button(self.root, text='Find Path', fg="red", cursor='man',
                         command=lambda: self.run())
        self.b2 = Button(self.root, text='History', cursor='man', command=lambda: self.history())
        self.b3 = Button(self.root, text='Select Dir', command=self.select_path)
        self.c = Checkbutton(self.root, text='Want to send the result to your mail?', variable=self.v4,
                             cursor='exchange', onvalue=1, offvalue=0, command=self.mail)

        # Display all components in the main window.
        self.e1.place(x=120, y=80)
        self.e2.place(x=120, y=120)
        self.e4.place(x=100, y=40)
        self.l1.place(x=50, y=80)
        self.l2.place(x=50, y=120)
        self.l3.place(x=50, y=40)
        self.c.place(x=50, y=160)
        self.b1.place(x=50, y=240)
        self.b2.place(x=180, y=240)
        self.b3.place(height=20, x=250, y=40)

    # Allow user to select a file path when they have moved the polygon file.
    def select_path(self):
        a = tkinter.messagebox.askyesno('Warning', 'If you have not changed the contents of the folder, the default '
                                        'path already contains the required files. This function is only used when you '
                                        'have moved the folder and know what files are needed. Changing the default '
                                        'path arbitrarily may cause an error report. If an error occurs due to '
                                        'changing the path, please restart the program.')
        if a:
            path_ = askdirectory()
            if path_ == '':
                self.folderpath.get()
            else:
                path_ = path_.replace('/', '\\')
                self.folderpath.set(path_)
        else:
            pass

    # Test and limit users input a correct number.
    def test(self, content):
        check = CheckError()
        x = check.isnum(content)
        return x

    # Allow users to send the result via email.
    def mail(self):
        if self.v4.get() == 1:
            self.e3.place_configure(width=160, x=140, y=200)
            self.l4.place_configure(x=50, y=200)
        elif self.v4.get() == 0:
            self.e3.place_forget()
            self.l4.place_forget()

    # Allow users to check their search history.
    def history(self):
        po = []
        hp = []
        png = []
        image = []

        # Judge if there is no history before.
        if not os.path.exists("./history/output.csv") or os.path.getsize("./history/output.csv") == 0:
            tkinter.messagebox.showinfo('Info', 'There is no history.')
        else:
            # Show the history in a new window.
            history = Tk()
            history.title('Searched history')
            Label(history, text="Location Point").grid(row=0, column=0)
            Label(history, text="Highest Point").grid(row=0, column=1)
            Label(history, text="Path Map").grid(row=0, column=2)

            # Read the recording file.
            with open("./history/output.csv", "r") as f:
                list_of_items = f.readlines()
                for each_item in list_of_items:
                    point, hpo, png1 = each_item.split(',')
                    po.append(point.strip())
                    hp.append(hpo.strip())
                    png.append(png1.strip())
                    image.append('./history/' + png1.strip())

            # Display the information in the search history on the window.
            length = len(po)
            for i in range(length):
                Label(history, text=po[i]).grid(row=i + 1, column=0)
                Label(history, text=hp[i]).grid(row=i + 1, column=1)
                Button(history, text=png[i], cursor='heart',
                       command=lambda arc=image[i]: self.openim(arc)).grid(row=i + 1, column=2)

            # Allow users to clear all history.
            Button(history, text='clear history', cursor='heart',
                   command=lambda: self.clearhis(history, image)).grid(row=length + 1, column=1)

    # Open an image in a new window.
    def openim(self, im):
        img = Image.open(im)
        img.show()

    # Allow users to clear their search history.
    def clearhis(self, window, png):
        a = tkinter.messagebox.askyesno('Warning', 'History cannot recover! Are you sure to clear history?')

        # Clear all contents of the recording files.
        if a:
            with open("./history/count.txt", "w") as f:
                f.write("0")
                f.close()
            with open("./history/output.csv", "w") as f:
                f.write("")
                f.close()
            for i in range(len(png)):
                os.remove(png[i])
            window.destroy()

    # Main function: find the fastest path between the user location and the nearest highest point.
    def run(self):
        folder = self.folderpath.get().replace('\\', '/')
        check = CheckError()

        # Judge if users input unexpected content.
        if self.v1.get() == '' or self.v2.get() == '':
            tkinter.messagebox.showerror('Error', 'Please input a valid coordinate!')
        elif not check.isinisle(self.v1.get(), self.v2.get()):
            tkinter.messagebox.showerror('Error', 'You are not near the Isle of Wight :)')
        else:
            try:
                # Test if the user input is within the Isle of Wight, returning the user location as a point.
                easting = float(self.v1.get())
                northing = float(self.v2.get())
                point = "(" + self.v1.get() + " " + self.v2.get() + ")"
                user_loc = UserInput(easting, northing, folder).location()
                buffer = user_loc.buffer(5000)

                # Identify the highest point of land within a 5km radius of the user location.
                out_transform = Transform(user_loc, folder).get_transform()
                destination = HighestPoint(out_transform, buffer, folder).find_highest_point()

                # Identify the nearest Integrated Transport Network (ITN) node to the user and to the highest point.
                start, end = NearestItn(user_loc, destination, buffer, folder).nearest_itn()

                # Identify the shortest route between the user location and highest point using Naismith's rule.
                shortest_path, mine_time = ShortestPath(start, end, buffer, out_transform, folder).shortest_path()

                # Plot all components for the user.
                map_background = os.path.join('background', 'raster-50k_2724246.tif')

                # Record the search.
                with open("./history/count.txt", "r") as f:
                    count = f.read()
                    count = str(int(count) + 1)
                    f.close()

                with open("./history/count.txt", "w") as f:
                    f.write(count)
                    f.close()

                outputpng = 'png' + count + '.png'

                with open("./history/output.csv", "a+", newline="") as f:
                    output = csv.writer(f)
                    datas = [[point, str(destination).strip("POINT"), outputpng]]
                    output.writerows(datas)
                    f.close()

                # Show the information after finding the path.
                information = 'The nearest highest point within the radius of 5km from your current location is ' \
                              + str(destination) + '. And the walking time of the path is ' + str(round(mine_time, 2)) \
                              + 's. It is time to move!'
                tkinter.messagebox.showinfo('Info', information)

                # Plot the map and save the image.
                Plotter(map_background, user_loc, destination, shortest_path, outputpng, folder).plot_graph()

                # Send the result to user's mail if they want it.
                if self.v4.get() == 1:
                    # Judge if user input a wrong email.
                    try:
                        s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
                        s.starttls()
                        s.login('additional_feature@outlook.com', 'Isntthiscool')
                        address = self.v3.get()
                        msg = MIMEMultipart()
                        msg['From'] = 'additional_feature@outlook.com'
                        msg['To'] = address
                        msg['Subject'] = "There is an incoming flood, it is time to move!"
                        msg.attach(MIMEText(information))

                        with open('./history/' + outputpng, 'rb') as fp:
                            img = MIMEImage(fp.read())
                            img.add_header('Content-Disposition', 'attachment', filename="final_map.jpg")
                            msg.attach(img)
                        s.send_message(msg)

                    except Exception:
                        tkinter.messagebox.showwarning('Warning', 'Failed to send the result to your mail. Your '
                                                                  'mail address is empty or incorrect!')

                elif self.v4.get() == 0:
                    pass

                # Open the map in a new window.
                self.openim('./history/' + outputpng)

            except Exception:
                tkinter.messagebox.showinfo('Error happened', 'Please try again!')

    # Supplementary the window framework information and run it in a loop.
    def win(self):
        self.root.title('Flood Emergency Planning')
        self.root.geometry("360x300+10+10")
        self.root.mainloop()
