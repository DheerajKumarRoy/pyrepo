from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.clipboard import Clipboard
from os.path import exists
import socket
import threading

# Default IP and port
ip = ''
port = ''
controll_switch = True
# Read from host.txt if it exists
if exists('host.txt'):
    with open('host.txt') as f:
        ip, port = f.read().split()

clipboard = []
clipboard_lock = threading.Lock()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class MyGrid(GridLayout, Screen):
    def __init__(self, **kwargs):
        super(MyGrid, self).__init__(**kwargs)
        self.cols = 1  # Set the number of columns in the GridLayout

        # Create inner window
        self.window = GridLayout(cols=5)

        # Add logo
        self.add_widget(Image(source='logo.png', size_hint=(1, 2)))

        # Title label
        self.title_label = Label(
            text='Clipboard Client',
            bold=True,
            color='#00FFCE')
        self.add_widget(self.title_label)

        # User input fields
        self.ip = TextInput(text=ip,
                            hint_text='IP',
                            multiline=False,
                            size_hint=(0.5, 0.5),
                            )
        self.ip.bind(text=self.on_text)

        self.port = TextInput(text=port,
                              hint_text='PORT',
                              multiline=False,
                              size_hint=(0.5, 0.5),
                              )
        self.port.bind(text=self.on_text)
        if ip and port:
            self.ip.text = ip
            self.port.text = port
        # Add button
        self.start = Button(text='connect',
                            size_hint=(0.5, 0.25),
                            bold=True,
                            disabled=True)
        self.start.bind(on_press=self.callback)

        for i in range(10):
            if i == 1:
                self.window.add_widget(self.ip)
            elif i == 3:
                self.window.add_widget(self.port)
            elif i == 7:
                self.window.add_widget(self.start)
            else:
                self.lab = Label(text='')
                self.window.add_widget(self.lab)
        self.add_widget(self.window)

        for i in range(2):
            i = Label(text='')
            self.add_widget(i)
        self.status = Label(text='')
        self.add_widget(self.status)
        for i in range(2):
            i = Label(text='')
            self.add_widget(i)

    def callback(self, instance):
        # Handle button press action here
        ip = self.ip.text
        port = self.port.text
        status = f"connecting to IP: {ip}, Port: {port}"
        self.status.text = status
        try:
            client_socket.connect((ip, int(port)))
            with open('host.txt', 'w') as f:
                f.write(f'{ip} {port}')
            self.manager.current = 'home'
            start_threads()
        except Exception as e:
            print(e)
            self.status.text = 'could not connect!'

    def on_text(self, instance, value):
        try:
            ip = self.ip.text
            port = self.port.text
            if ip and port.isdigit():  # Check if port is a valid integer
                port = int(port)
                self.start.disabled = False
            else:
                self.start.disabled = True
        except ValueError:
            self.ip.hint_text = "Invalid Values!"
            self.start.disabled = True

class Home(GridLayout, Screen):
    def __init__(self, **kwargs):
        super(Home, self).__init__(**kwargs)
        self.cols = 1  # Set the number of columns in the GridLayout

        # Create inner window
        self.window = GridLayout(cols=3)
        self.data = GridLayout(cols=1, size_hint_y=6)
        # Add logo
        self.add_widget(Image(source='logo.png', size_hint=(1, 2)))

        # Title label
        self.title_label = Label(
            text=f'Clipboard Client connected to {ip}',
            bold=True,
            color='#00FFCE')
        self.add_widget(self.title_label)

        # User input fields
        self.text_box = TextInput(
            hint_text='enter text here...',
            multiline=False,
            size_hint=(0.5, 0.5),
        )
        self.text_box.bind(text=self.on_text)
        self.add_widget(self.text_box)

        # Add button
        self.add = Button(text='ADD',
                          size_hint=(0.5, 2),
                          bold=True,
                          disabled=True)
        self.add.bind(on_press=self.callback)
        #stop/run button
        self.controll = Button(text='stop',
                          size_hint=(0.5, 2),
                          bold=True)
        self.controll.bind(on_press=self.cont_callback)
        #show received data
        self.received = Button(text='Received',
                          size_hint=(0.5, 2),
                          bold=True)
        self.received.bind(on_press=self.recv_callback)

        for i in range(9):
            if i == 4:
                self.window.add_widget(self.add)
            elif i ==6:
                self.window.add_widget(self.received)
            elif i ==8:
                self.window.add_widget(self.controll)
            else:
                i = Label(text='')
                self.window.add_widget(i)
        self.add_widget(self.window)
        # if clipboard:
        #     self.received.disabled=False

        self.scroll_view = ScrollView()
        self.label = Label(size_hint=(None, None),
                           text_size=(None, None),
                           padding=(20, 20),
                           halign='left',
                           valign='top',
                           markup=True,
                           # font_size=20
                           )
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll_view.add_widget(self.label)
        self.data.add_widget(self.scroll_view)
        self.add_widget(self.data)
        self.label.text = 'no data'

    def cont_callback(self, instance):
        global controll_switch
        controll_switch = not controll_switch
        if controll_switch:
            self.controll.text ='stop'
        else:
            self.controll.text ='run'
    def recv_callback(self,instance):
        if clipboard:
            self.label.text = '\n'.join(reversed(clipboard))
        else:
            self.label.text = 'nothing here!'


    def callback(self, instance):
        global controll_switch
        # Handle button press action here
        text_to_send = self.text_box.text
        if text_to_send and controll_switch:
            with clipboard_lock:
                # clipboard.append(text_to_send)
                client_socket.sendall(text_to_send.encode())
                self.label.text = '..sent..\n'+text_to_send
                # self.label.text = '\n'.join(reversed(clipboard))
            self.text_box.text = ''

    def on_text(self, instance, value):
        try:
            if self.text_box.text:  # Check if there is any text to send
                self.add.disabled = False
            else:
                self.add.disabled = True
        except ValueError:
            self.text_box.hint_text = "Invalid Value!"
            self.add.disabled = True

def handle_receive():
    global controll_switch
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data and controll_switch:
                with clipboard_lock:
                    Clipboard.copy(data)
                    # print(Clipboard.paste())
                    clipboard.append(data)
                print(f"Received from server: {data}")
        except Exception as e:
            print(f"Receive error: {e}")
            break

def handle_send():
    global controll_switch
    last_text = ''
    while True:
        try:
            text = Clipboard.paste()
            if text and controll_switch:
                if text!=last_text:
                    with clipboard_lock:
                        last_text = text
                        # clipboard.append(text)
                        client_socket.sendall(text.encode())
        except Exception as e:
            print(f"Send error: {e}")
            break

def start_threads():
    threading.Thread(target=handle_receive, daemon=True).start()
    threading.Thread(target=handle_send, daemon=True).start()

class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MyGrid(name='connect_screen'))
        sm.add_widget(Home(name='home'))
        return sm

if __name__ == '__main__':
    MyApp().run()
