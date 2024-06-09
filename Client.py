import tkinter as tk
from tkinter import *
from tkinter import  messagebox, simpledialog, filedialog, Label, PhotoImage
from tkinter.scrolledtext import ScrolledText
import os
import socket
import re  
import threading


class ClientApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Client Application")

        self.server_address = "127.0.0.1"
        self.server_port = 12345
        self.client_socket = socket.socket()
        self.connect_to_server()


        self.background_image = PhotoImage(file="E:\\pythonProject2\\background.png")
        self.background_label = Label(root, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)  

        self.welcome_label = tk.Label(root, text="Welcome to Flora Vision",
                                      font=("Helvetica", 24, "bold"), bg="white", fg="green")
        self.welcome_label.pack(pady=20)

        self.login_btn = tk.Button(root, text="LOGIN", command=self.login)
        self.login_btn.pack(pady=5)

        self.register_btn = tk.Button(root, text="REGISTER", command=self.register)
        self.register_btn.pack(pady=5)

        self.chat_running = False



    def get_last_prediction_stats(self):
        self.send_to_server(f"LAST_PREDICTION_STATS {self.logged_in_email}")
        stats = self.receive_from_server()
        messagebox.showinfo("Last Prediction Stats", stats)

    def start_receiving_messages(self):
        thread = threading.Thread(target=self.receive_messages_loop)
        thread.daemon = True
        thread.start()

    def setup_chat_interface(self):
        self.chat_window = Toplevel(self.root)
        self.chat_window.title("Chat")

        self.chat_text = ScrolledText(self.chat_window, state=DISABLED, height=10, width=50)
        self.chat_text.pack(padx=20, pady=10)

        self.message_entry = Entry(self.chat_window, width=40)
        self.message_entry.pack(side=LEFT, padx=(20, 10))

        send_button = Button(self.chat_window, text="Send", command=self.send_chat)
        send_button.pack(side=RIGHT, padx=(10, 20))

        close_button = Button(self.chat_window, text="Close", command=self.on_closing_chat)
        close_button.pack(pady=5)

        self.chat_running = True
        threading.Thread(target=self.receive_chat_messages, daemon=True).start()

        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing_chat)

    def send_chat(self):
        message = self.message_entry.get()
        if message:
            self.send_to_server(f"CHAT {message}")
            self.message_entry.delete(0, END)

    def receive_chat_messages(self):
        while self.chat_running:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    if message == "chatclose":
                        break
                    self.update_chat_text(message)
            except OSError as e:
                print("Error receiving chat message:", e)
                break

    def update_chat_text(self, message):
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_text.config(state=NORMAL)
            self.chat_text.insert(END, message + '\n')
            self.chat_text.config(state=DISABLED)
            self.chat_text.yview(END)

    def on_closing_chat(self):
        self.chat_running = False
        self.chat_window.destroy()
        self.chat_window = None
        self.client_socket.send("chatclose".encode())

    def open_chat(self):
        if not hasattr(self, 'chat_window') or not self.chat_window:
            self.setup_chat_interface()


    def connect_to_server(self):
        try:
            self.client_socket.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            messagebox.showerror("Connection Error", "Could not connect to the server.")
            self.root.destroy()

    def send_to_server(self, message):
        self.client_socket.send(message.encode())

    def receive_from_server(self):
        return self.client_socket.recv(1024).decode()

    def login(self):
        email = simpledialog.askstring("Login", "Enter your email:")
        password = simpledialog.askstring("Login", "Enter your password:", show="*")
        if not email or not password:  
            messagebox.showerror("Login Failed", "Email or password cannot be empty.")
            return
        self.send_to_server(f"LOGIN {email} {password}")
        response = self.receive_from_server()
        if response == "SUCCESS":
            self.logged_in_email = email  
            self.login_success()  
        else:
            messagebox.showerror("Login Failed", "Incorrect email or password.")

    def login_success(self):
        self.login_btn.pack_forget()
        self.register_btn.pack_forget()

        self.select_images_btn = tk.Button(root, text="Select Images", command=self.select_images)
        self.select_images_btn.pack(pady=10)

        self.stats_btn = tk.Button(self.root, text="Last Prediction Stats", command=self.get_last_prediction_stats)
        self.stats_btn.pack(pady=10)

        self.history_btn = tk.Button(root, text="HISTORY", command=self.get_history)
        self.history_btn.pack(pady=5)

        self.chat_btn = tk.Button(self.root, text="Open Chat", command=self.open_chat)
        self.chat_btn.pack(pady=10)

        self.exit_btn = tk.Button(root, text="EXIT", command=self.exit_app)
        self.exit_btn.pack(pady=10)



    def get_history(self):
        self.send_to_server(f"GET_HISTORY {self.logged_in_email}")
        history = self.receive_from_server()
        messagebox.showinfo("Prediction History", history)

    def send_image_to_server(self, image_path):
        self.send_to_server("SEND_IMAGE")
        self.send_to_server(self.logged_in_email)  
        ack = self.client_socket.recv(1024).decode()
        if ack != "ACK":
            print("Failed to receive ACK from server for email")
            return

        file_size = os.path.getsize(image_path)
        self.client_socket.send(str(file_size).encode())
        ack = self.client_socket.recv(1024).decode()
        if ack != "ACK":
            print("Server did not acknowledge file size")
            return

        with open(image_path, 'rb') as file:
            data = file.read(1024)
            while data:
                self.client_socket.send(data)
                data = file.read(1024)

        response = self.client_socket.recv(1024).decode()
        messagebox.showinfo("Server Response", response)

    def select_images(self):
        file_paths = filedialog.askopenfilenames(title="Select files",
                                                 filetypes=(("jpeg files", "*.jpg"), ("all files", "*.*")))
        for file_path in file_paths:
            self.send_image_to_server(file_path)

    def exit_app(self):
        self.client_socket.send("EXIT".encode())
        self.client_socket.close()
        self.root.destroy()

    def register(self):
        name = simpledialog.askstring("Register", "Enter your name:")
        email = simpledialog.askstring("Register", "Enter your email:")
        password = simpledialog.askstring("Register", "Enter your password:", show="*")
        if not name or not email or not password:  
            messagebox.showerror("Register Failed", "Name, email, or password cannot be empty.")
            return
        self.send_to_server(f"REGISTER {name} {email} {password}")
        response = self.receive_from_server()
        if response == "SUCCESS":
            messagebox.showinfo("Register", "Registration successful. Please login.")
        else:
            messagebox.showerror("Register Failed", "Registration failed. Try again.")

    def show_main_app(self):
        pass

    def exit_app(self):
        self.send_to_server("EXIT")
        self.client_socket.close()
        self.root.destroy()

root = tk.Tk()
app = ClientApp(root)
root.mainloop()
