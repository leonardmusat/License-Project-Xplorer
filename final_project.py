import socket
import cv2
import numpy as np
import threading
import keyboard
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import sys
import torch

# Set the server IP and port
ip = "192.168.0.149"  # Listen on all available interfaces
state_for_commands = 0b00
state_for_commands_1 = 0b00
repeat = datetime.now()
stop_flag = False
AI_flag = False

def on_esc(e):
    global stop_flag
    stop_flag = True
    print("Escape key pressed. Stopping the server...")

def on_space(e):
    global AI_flag
    if AI_flag == False:
        AI_flag = True
    else:
        AI_flag = False

keyboard.on_press_key('esc', on_esc)
keyboard.on_press_key('space', on_space)

def udp_stream(server_ip):
    global AI_flag
    server_port = 8888
    CHUNK_LENGTH = 1460  
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    target_object = "person"

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_ip, server_port))

    print(f"UDP server is listening on {server_ip}:{server_port}")

    # Buffer to hold the image data (using a list to avoid resizing issues)
    image_chunks = []

    while not stop_flag:
        # Receive data from the UDP socket
        data, addr = udp_socket.recvfrom(CHUNK_LENGTH)

        # Check for the start of a JPEG image (FFD8FF)
        if len(data) >= 3 and data[0] == 255 and data[1] == 216 and data[2] == 255:
            image_chunks = [] 

        image_chunks.append(data)

        # Check for the end of a JPEG image (FFD9)
        if len(data) >= 2 and data[-2] == 255 and data[-1] == 217:
            image_buffer = b''.join(image_chunks)

            # Decode the complete image
            jpg_data = np.frombuffer(image_buffer, dtype=np.uint8)
            frame = cv2.imdecode(jpg_data, cv2.IMREAD_COLOR)

            if frame is not None:
                if AI_flag:
                    # Perform inference
                    results = model(frame)
                    detections = results.xyxy[0].numpy()  # Get the detections as a NumPy array

                    person_detections = [detection for detection in detections if model.names[int(detection[5])] == target_object]

                    if person_detections:
                        best_detection = max(person_detections, key=lambda x: x[4])  # Sort by confidence score

                        x1, y1, x2, y2, confidence, class_idx = best_detection
                        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                        # Draw a bounding box for the most confident cat detection
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        cv2.putText(frame, f"{target_object} {confidence:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                        # Perform your logic with the single detection (e.g., calculate state_for_commands)
                        height, width, _ = frame.shape
                        center_frame = (width / 2, height / 2)
                        center_object = ((x1 + x2) / 2, (y1 + y2) / 2)
                        surface_frame = width * height
                        surface_object = (x2 - x1) * (y2 - y1)

                        global state_for_commands
                        if center_object[0] < center_frame[0] - 0.25 * width and 0.4 * surface_frame > surface_object > 0.3 * surface_frame:
                            state_for_commands = 0b0100  # left
                        elif center_object[0] > center_frame[0] + 0.25 * width and 0.4 * surface_frame > surface_object > 0.3 * surface_frame:
                            state_for_commands = 0b0001  # right
                        elif center_frame[0] - 0.25 * width < center_object[0] < center_frame[0] + 0.25 * width and 0.3 * surface_frame > surface_object:
                            state_for_commands = 0b1000  # forward
                        elif center_frame[0] - 0.25 * width < center_object[0] < center_frame[0] + 0.25 * width and 0.4 * surface_frame < surface_object:
                            state_for_commands = 0b0010  # backward
                        elif center_object[0] < center_frame[0] - 0.25 * width and 0.3 * surface_frame > surface_object:
                            state_for_commands = 0b1100  # left-forward
                        elif center_object[0] < center_frame[0] + 0.25 * width and 0.4 * surface_frame < surface_object:
                            state_for_commands = 0b0110  # left-backwards
                        elif center_object[0] > center_frame[0] - 0.25 * width and 0.3 * surface_frame > surface_object:
                            state_for_commands = 0b1001  # right-forward
                        elif center_object[0] > center_frame[0] + 0.25 * width and 0.4 * surface_frame < surface_object:
                            state_for_commands = 0b0011  # right-backwards
                        elif center_frame[0] - 0.25 < center_object[0] < center_frame[0] + 0.25 * width and 0.4 * surface_frame > surface_object > 0.3 * surface_frame:
                            state_for_commands = 0b0000
                    else:
                        state_for_commands = 0b0000  # No cat detected
                    cv2.imshow("Object Detection", frame)
                else:
                    cv2.imshow('Received Image', frame)


            # Exit the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Clean up resources
    udp_socket.close()
    cv2.destroyAllWindows()

def commands(server_ip):
    server_port = 8889

    # Define each key with its respective bit position
    key_map_commands = {
        'w': 0b1000,  # forward
        'a': 0b0100,  # keft
        's': 0b0010,  # backward
        'd': 0b0001,   # right 
        'p': 0b1111, # modify speed
    }

    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((server_ip, server_port))

    # Listen for incoming connections
    server_socket.listen(3)
    print(f"Listening for connections on {server_ip}:{server_port}...")

    # Accept a single incoming connection
    client_socket, client_address = server_socket.accept()
    print(f"Connected to {client_address}")
    client_connected = True

    def reconnect_client():
        nonlocal client_socket, client_connected
        while not client_connected:
            try:
                print("Waiting for client to reconnect...")
                client_socket, client_address = server_socket.accept()
                print(f"Reconnected to {client_address}")
                client_connected = True
            except Exception as e:
                print(f"Reconnection failed: {e}")
                time.sleep(1)  # Wait before retrying


    # Function to update the state when a key is pressed
    def press_key(key):
        global state_for_commands
        global state_for_commands_1 
        nonlocal client_connected
        global repeat
        if key in key_map_commands: 
            state_for_commands |= key_map_commands[key]  # Set the bit for the key
            duration = timedelta(seconds=0.2) 
            now = datetime.now()
            if state_for_commands != state_for_commands_1 or now - repeat > duration:
                repeat = now
                state_for_commands_1 = state_for_commands
                try:
                    if client_connected:
                        client_socket.sendall((format(state_for_commands, '04b') + '\n').encode('utf-8'))
                        time.sleep(0.1)
                        print(f"Message {state_for_commands} was sent")
                    else:
                        print("Client not connected; cannot send data.")
                except (BrokenPipeError, ConnectionResetError):
                    print("Removing disconnected client.")
                    client_socket.close() 
                    client_connected = False
                    reconnect_client()
 
    def release_key(key):
        global state_for_commands
        nonlocal client_connected
        if key in key_map_commands:
            state_for_commands &= ~key_map_commands[key]  # Clear the bit for the key
            try:
                if client_connected:
                    client_socket.sendall((format(state_for_commands, '04b') + '\n').encode('utf-8'))
                    time.sleep(0.2)
                    print(f"Message {state_for_commands} was sent")
            except (BrokenPipeError, ConnectionResetError):
                print("Client disconnected during release_key.")
                client_connected = False
                client_socket.close()
                reconnect_client()
                #reconnect_client(client_socket, client_address, client_connected, server_socket)

    def AI_move():
        global state_for_commands
        global state_for_commands_1 
        nonlocal client_connected
        global AI_flag
        global repeat
        if AI_flag == True:
            if state_for_commands != state_for_commands_1:
                state_for_commands_1 = state_for_commands
                # print(state_for_commands)
                try:
                    if client_connected:
                        client_socket.sendall((format(state_for_commands, '04b') + '\n').encode('utf-8'))
                        time.sleep(0.1)
                        print(f"Message {state_for_commands} was sent")
                    else:
                        print("Client not connected; cannot send data.")
                except (BrokenPipeError, ConnectionResetError):
                    print("Removing disconnected client.")
                    client_socket.close() # Remove invalid client
                    client_connected = False
                    reconnect_client()

    def code_moves(key1):
        # Set up event listeners for each key       
        for key in key1.keys():
                keyboard.on_press_key(key, lambda e, k=key: press_key(k))
                keyboard.on_release_key(key, lambda e, k=key: release_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

   # Start key listener thread
    threading.Thread(target=code_moves, args=(key_map_commands,), daemon=True).start()

# Main loop
    try:
        while not stop_flag:
            if AI_flag:
                AI_move()
                time.sleep(0.1)
            else:
                time.sleep(0.1)  # Prevent high CPU usage

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the connections
        client_socket.close()
        server_socket.close()
        print("Connections closed.")

def blitz(server_ip):
    server_port = 8887
    trigger = 0b1111

    # Define each key with its respective bit position
    key_map = ['k'] 

    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((server_ip, server_port))

    # Listen for incoming connections
    server_socket.listen(3)
    print(f"Listening for connections on {server_ip}:{server_port}...")

    # Accept a single incoming connection
    client_socket, client_address = server_socket.accept()
    print(f"Connected to {client_address}")

    # Function to update the state when a key is pressed
    def press_key(key):
        nonlocal client_socket
        try:
            if key in key_map:
                client_socket.sendall((format(trigger, '04b') + '\n').encode('utf-8'))
                time.sleep(0.1)
                print(f"Message {trigger} was sent")
        except (BrokenPipeError, ConnectionResetError):
            print("Client disconnected during release_key.")
            client_socket.close()
            client_socket, client_address = server_socket.accept()
            print(f"Reconnected to {client_address}")

    def code_moves(key1):
        # Set up event listeners for each key
        for key in key1:
            keyboard.on_press_key(key, lambda e, k=key: press_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

    try:
        while not stop_flag:
            code_moves(key_map)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the connection
        client_socket.close()
        server_socket.close()
        print("Connection closed.")

def user_interfaceP():

    root = tk.Tk()

    # Set the window to full screen
    root.attributes('-fullscreen', True)

    # Load the background image
    background_image = Image.open("green_image2.jpg")  # Replace with your image path
    background_image = background_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.Resampling.LANCZOS)
    background_photo = ImageTk.PhotoImage(background_image)

    # Create a label to display the background image
    background_label = tk.Label(root, image=background_photo)
    background_label.place(relwidth=1, relheight=1)

    # Function to close the window
    def close_window():
        root.destroy()

    # Create an "Exit" button
    exit_button = tk.Button(root, text="Exit", command=close_window, font=('Arial', 16), bg='red', fg='white')
    exit_button.pack(pady=20)  # Position the button with some padding
    exit_button.place(x=1300, y=800)

    # Redirect stdout to a Text widget
    class TextRedirector:
        def __init__(self, widget):
            self.widget = widget

        def write(self, string):
            self.widget.insert(tk.END, string)  
            self.widget.see(tk.END)  # Automatically scroll to the bottom

        def flush(self):
            pass  # Required for compatibility with some systems

    # Create a scrolled text box to display logs
    log_box = ScrolledText(root, width=40, height=40, font=("Arial", 12), bg="black", fg="white")
    log_box.place(x=1100, y=50)

    # Redirect standard output to the text box
    sys.stdout = TextRedirector(log_box)

    # Run the main loop
    root.mainloop()

thread1 = threading.Thread(target=udp_stream, args=(ip,))
thread2 = threading.Thread(target=commands, args=(ip,))
thread3 = threading.Thread(target=blitz, args=(ip,))
thread4 = threading.Thread(target=user_interfaceP, args=())

thread4.start()
time.sleep(0.5)
thread1.start()
thread2.start()
thread3.start()

thread4.join()
thread1.join()
thread2.join()
thread3.join()