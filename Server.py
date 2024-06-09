import socket  
import os  
import tensorflow as tf  
import numpy as np  
from PIL import Image  
import hashlib  
import re  
import threading



model = tf.keras.models.load_model("G:\\My Drive\\OfekModel\\ofek1.tf")
IMG_SIZE = (224, 224)  

class_names = ['Bacterial Spot', 'Black Rot', 'Early Blight', 'INaturalList', 'Late Blight', 'Powdery Mildew', 'Yellow Leaf Carl virus', 'healthy', 'not healthy']  # הגדרת הקטגוריות שהמודל יכול לזהות

def predict(filename , email):
    img = Image.open(filename)
    img = img.resize(IMG_SIZE)
    img = np.array(img)
    img = np.expand_dims(img, axis=0)
    prediction = model.predict(img)
    percentages = tf.nn.softmax(prediction).numpy()[0]
    sorted_indices = np.argsort(percentages)[::-1]
    results = [(class_names[idx], f"{percentages[idx] * 100:.2f}%") for idx in sorted_indices]
    save_prediction_stats(email, results)  
    top_prediction = class_names[tf.argmax(percentages)]
    save_prediction(email, top_prediction)  
    return top_prediction



def save_prediction_stats(email, results):
    print(f"Saving stats for {email}")
    try:
        with open(f"{email}_prediction_stats.txt", "w") as file:
            for result in results:
                line = f"{result[0]} [{result[1]}]\n"
                print(f"Writing to file: {line}")
                file.write(line)
    except Exception as e:
        print(f"Failed to write to file: {e}")


def send_last_prediction_stats(client_socket, email):
    try:
        with open(f"{email}_prediction_stats.txt", "r") as file:
            stats = file.read()
            print(f"Sending stats: {stats}")
        client_socket.send(stats.encode())
    except FileNotFoundError:
        print("No prediction stats available.")
        client_socket.send("No prediction stats available.".encode())
    except Exception as e:
        print(f"Error reading file: {e}")
        client_socket.send("Error reading stats.".encode())


connected_clients = []

def broadcast_message(message, sender_socket=None):
    for client in connected_clients:
        try:
            client.send(message.encode())
        except Exception as e:
            print(f"Failed to send message to {client.getpeername()}: {e}")



def save_prediction(email, prediction):
    with open("predictions_history.txt", "a") as file:
        file.write(f"{email},{prediction}\n")

def send_history(client_socket, email):
    try:
        with open("predictions_history.txt", "r") as file:
            history = [line.strip() for line in file if line.startswith(email)]
        history_str = "\n".join(history)
        client_socket.send(history_str.encode())
    except FileNotFoundError:
        client_socket.send("No history available.".encode())

def is_email_valid(email):
    pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
    return re.match(pattern, email) is not None

def is_password_valid(password):
    return len(password) >= 8

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def handle_client_connection(client_socket, addr):
    connected_clients.append(client_socket)

    try:
        while True:
            command = client_socket.recv(1024).decode()  
            if command == "EXIT":
                print("Closing connection")
                break

            elif command.startswith("chatclose"):
                client_socket.send("chatclose".encode())  

            elif command.startswith("LOGIN") or command.startswith("REGISTER"):
                handle_login_register(client_socket, command)

            elif command.startswith("SEND_IMAGE"):
                client_socket.send("ACK".encode()) 
                handle_image_reception(client_socket)

            elif command.startswith("LAST_PREDICTION_STATS"):
                email = command.split()[1]
                send_last_prediction_stats(client_socket, email)

            elif command.startswith("GET_HISTORY"):
                email = command.split()[1]
                send_history(client_socket, email)

            elif command == "GET_CONNECTED_USERS":
                connected_emails = [client['email'] for client in connected_clients if 'email' in client]
                client_socket.send(','.join(connected_emails).encode())


            elif command.startswith("CHAT"):
                _, chat_message = command.split(maxsplit=1)
                chat_message_to_broadcast = f"{addr}: {chat_message}"
                broadcast_message(chat_message_to_broadcast)



            else:
                client_socket.send("UNKNOWN_COMMAND".encode())

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        connected_clients.remove(client_socket)
        client_socket.close()
        print(f"Connection closed with {addr}")


def client_thread(client_socket, addr):
    handle_client_connection(client_socket, addr)

def handle_login_register(client_socket, command):
    if command.startswith("LOGIN"):
        name, email, password = command.split()
        if validate_user(email, password):
            client_socket.send("SUCCESS".encode())
        else:
            client_socket.send("FAIL".encode())
    elif command.startswith("REGISTER"):
        _, name, email, password = command.split()
        if not is_email_valid(email) or not is_password_valid(password):
            client_socket.send("FAIL".encode())
            return
        if register_user(name, email, password):
            client_socket.send("SUCCESS".encode())
        else:
            client_socket.send("FAIL".encode())

def validate_user(email, password):
    hashed_password = hash_password(password)
    try:
        with open("users.txt", "r") as file:
            for line in file:
                stored_email, stored_hashed_password = line.strip().split(", ")
                if stored_email == email and stored_hashed_password == hashed_password:
                    return True
        return False
    except FileNotFoundError:
        return False

def register_user( email, password):
    print(f"Attempting to register user: {email}")
    if not is_email_valid(email) or not is_password_valid(password):
        print("Registration failed: Invalid email or password")
        return False
    if user_exists(email):
        print("Registration failed: User already exists")
        return False

    hashed_password = hash_password(password) 
    try:
        with open("users.txt", "a") as file:
            file.write(f"{email}, {hashed_password}\n")
            print("User registered successfully")
        return True
    except Exception as e:
        print(f"Error when registering user: {e}")
        return False

def user_exists(email):
    try:
        with open("users.txt", "r") as file:
            for line in file:
                stored_email, _ = line.strip().split(", ")
                if stored_email == email:
                    return True
        return False
    except FileNotFoundError:
        return False

def handle_image_reception(client_socket):
    email = client_socket.recv(1024).decode()  
    file_size = client_socket.recv(1024).decode()  
    print(f"Preparing to receive an image of size: {file_size} bytes from {email}")
    client_socket.send("ACK".encode()) 

    with open("received_image.jpg", "wb") as file:
        bytes_received = 0
        file_size = int(file_size)
        while bytes_received < file_size:
            data = client_socket.recv(1024)
            if not data:
                break
            file.write(data)
            bytes_received += len(data)

    if bytes_received == file_size:
        print("File has been received successfully.")
        prediction = predict("received_image.jpg",email)
        client_socket.send(f"Prediction: {prediction}".encode())
        save_prediction(email, prediction)  


    else:
        print("File was not received successfully.")



while True:
    server_socket = socket.socket()
    host = "0.0.0.0"
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Listening at {host}:{port}")
    client_socket, addr = server_socket.accept()
    print(f"Got a connection from {addr}")
    thread = threading.Thread(target=client_thread, args=(client_socket, addr))
    thread.start()
