import socket
import threading
import signal
import sys
import time
import subprocess
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.clipboard import Clipboard

command = 'ipconfig'
ip = ''
try:
    # out_put = subprocess.run(command,shell=True,check=True)
    out_put = subprocess.check_output(command,shell=True,stderr=subprocess.STDOUT).decode('utf-8').split('Wi-Fi')
    for line in out_put[1].splitlines():
        if 'IPv4' in line:
            ip = line.split(':')[1].strip()
            break
except Exception as e:
    ip = 'connect to LAN'
    print('Oops, connect to LAN first!')
clipboard = []
clipboard_lock = threading.Lock()

# Server details
SERVER_IP = '0.0.0.0'
SERVER_PORT = 12345

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Global variables
clients = []
running = True
client_ip = ''

def handle_client(client_socket, client_address):
    global running,client_ip
    print(f"Connection from {client_address} has been established.")
    client_ip = f'connected to:{client_address}'
    last_text = ''
    while running:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            # print(f"Received from {client_address}: {data}")
            if last_text!=data:
                last_text=data
                with clipboard_lock:
                    clipboard.append(data)
                    Clipboard.copy(data)
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    if client_socket in clients:
        clients.remove(client_socket)
    print(f"Connection from {client_address} has been closed.")
    client_ip=f'disconnected:{client_address}'
    
def server_thread():
    global running
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    while running:
        try:
            client_socket, client_address = server_socket.accept()
            clients.append(client_socket)
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_handler.start()
        except Exception as e:
            if running:
                print(f"Server error: {e}")

def signal_handler(sig, frame):
    global running
    print("Shutting down server...")
    running = False
    server_socket.close()
    for client in clients:
        client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Home(GridLayout, Screen):
    def __init__(self, **kwargs):
        super(Home, self).__init__(**kwargs)
        self.cols = 1

        self.window = GridLayout(cols=3)
        self.data = GridLayout(cols=1, size_hint_y=6)

        self.add_widget(Image(source='logo.png', size_hint=(1, 2)))

        self.title_label = Label(
            text=f"server listening on ('{ip}', 12345)",
            bold=True,
            color='#00FFCE'
        )
        self.add_widget(self.title_label)

        self.text_box = TextInput(
            hint_text='enter text here...',
            multiline=True,
            size_hint=(0.5, 0.5),
        )
        self.text_box.bind(text=self.on_text)
        self.add_widget(self.text_box)

        self.add = Button(text='ADD',
                          size_hint=(0.5, 2),
                          bold=True,
                          disabled=True)
        self.add.bind(on_press=self.callback)

        self.controll = Button(text='stop',
                               size_hint=(0.5, 2),
                               bold=True)
        self.controll.bind(on_press=self.cont_callback)

        self.received = Button(text='Received',
                               size_hint=(0.5, 2),
                               bold=True)
        self.received.bind(on_press=self.recv_callback)

        for i in range(9):
            if i == 4:
                self.window.add_widget(self.add)
            elif i == 6:
                self.window.add_widget(self.received)
            elif i == 8:
                self.window.add_widget(self.controll)
            else:
                i = Label(text='')
                self.window.add_widget(i)
        self.add_widget(self.window)

        self.conn_status= Label(text=client_ip)
        self.add_widget(self.conn_status)

        self.scroll_view = ScrollView()
        self.label = Label(size_hint=(None, None),
                           text_size=(None, None),
                           padding=(20, 20),
                           halign='left',
                           valign='top',
                           markup=True)
        self.label.bind(texture_size=self.label.setter('size'))
        self.scroll_view.add_widget(self.label)
        self.data.add_widget(self.scroll_view)
        self.add_widget(self.data)
        self.label.text = 'no data'

        # Start threads for receiving and sending data
        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.send_thread = threading.Thread(target=self.send_data)
        self.send_thread.daemon = True
        self.send_thread.start()

    def cont_callback(self, instance):
        global running
        running = not running
        if running:
            self.controll.text = 'stop'
        else:
            self.controll.text = 'run'

    def recv_callback(self, instance):
        if clipboard:
            self.label.text = '\n'.join(reversed(clipboard))
        else:
            self.label.text = 'nothing here!'

    def callback(self, instance):
        last_text = ''
        global running
        text_to_send = self.text_box.text
        if text_to_send and running:
            if last_text!=Clipboard.paste():
                last_text=Clipboard.paste()
                with clipboard_lock:
                    for client in clients:
                        client.sendall(text_to_send.encode())
                    self.label.text = '..sent..\n' + text_to_send
            self.text_box.text = ''

    def on_text(self, instance, value):
        try:
            self.conn_status.text = str(client_ip)
            if self.text_box.text:
                self.add.disabled = False
            else:
                self.add.disabled = True
        except ValueError:
            self.text_box.hint_text = "Invalid Value!"
            self.add.disabled = True

    def receive_data(self):
        while running:
            if clipboard:
                self.label.text = '\n'.join(reversed(clipboard))

    def send_data(self):
        global client_ip
        last_text = ""
        while running:
            current_text = Clipboard.paste()
            if current_text != last_text:
                last_text = current_text
                with clipboard_lock:
                    for client in clients:
                        client.sendall(current_text.encode())
                        # self.title_label.text=str(client_ip)

            # To avoid busy-waiting, you can sleep for a short duration
            time.sleep(0.3)

class MyApp(App):
    def build(self):
        return Home()

if __name__ == '__main__':
    server_thread = threading.Thread(target=server_thread)
    server_thread.start()
    MyApp().run()
    running = False
    server_socket.close()
    for client in clients:
        client.close()
    server_thread.join()
