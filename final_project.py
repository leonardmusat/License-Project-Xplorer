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
ip = "192.168.100.37"  # Listen on all available interfaces
state_for_commands = 0b00
state_for_commands_1 = 0b00
repeat = datetime.now()
stop_flag = False
AI_flag = False

# def reconnect_client(client_socket_f, client_address_f, client_connected_f, server_socket_f):
#     while not client_connected_f:
#         try:
#             print("Waiting for client to reconnect...")
#             client_socket_f, client_address_f = server_socket_f.accept()
#             print(f"Reconnected to {client_address_f}")
#             client_connected_f = True
#         except Exception as e:
#             print(f"Reconnection failed: {e}")
#             time.sleep(1)  # Wait before retrying

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
    server_port = 8888
    CHUNK_LENGTH = 1460  # Size of each chunk, matching ESP32 code
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
            image_chunks = []  # Clear the list at the start of a new image

        # Append the received data chunk to the list
        image_chunks.append(data)

        # Check for the end of a JPEG image (FFD9)
        if len(data) >= 2 and data[-2] == 255 and data[-1] == 217:
            # Concatenate all chunks into a single byte array
            image_buffer = b''.join(image_chunks)

            # Decode the complete image
            jpg_data = np.frombuffer(image_buffer, dtype=np.uint8)
            frame = cv2.imdecode(jpg_data, cv2.IMREAD_COLOR)

            # Display the image if it was decoded successfully
            if frame is not None:
                if AI_flag:
                    # Perform inference
                    results = model(frame)
                    detections = results.xyxy[0].numpy()  # Get the detections as a NumPy array

                    for detection in detections:
                        x1, y1, x2, y2, confidence, class_idx = detection
                        class_name = model.names[int(class_idx)]

                        if class_name == target_object:
                            # Convert bounding box coordinates to integers
                            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                            print(x1, x2, y1, y2)

                            # Draw a bounding box for the target object
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(frame, f"{class_name} {confidence:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                            
                            # Show the frame
                            cv2.imshow("Object Detection", frame)

                            height, width, _ = frame.shape  # height is the number of rows, width is the number of columns

                            # The boundaries are:
                            center_frame = (width/2, height/2)
                            center_object = ((x1+x2)/2, (x2+y2)/2)

                            surface_frame = width * height
                            surface_object = (x2-x1) * (y2-y1)  

                            global state_for_commands
                                # Determine the position
                            if center_object[0] < center_frame[0] and 0.7* surface_frame == surface_object:
                                state_for_commands = 0b0100 #left
                            elif center_object[0] > center_frame[0] and 0.7* surface_frame == surface_object:
                                state_for_commands = 0b0001 #right
                            elif center_object[0] == center_frame[0] and 0.7* surface_frame > surface_object:
                                state_for_commands = 0b1000 #forward
                            elif center_object[0] == center_frame[0] and 0.7* surface_frame < surface_object:
                                state_for_commands = 0b0010 #backward
                            elif center_object[0] < center_frame[0] and 0.7* surface_frame > surface_object:
                                state_for_commands = 0b1100 #left-forward
                            elif center_object[0] < center_frame[0] and 0.7* surface_frame < surface_object:
                                state_for_commands = 0b0110 #left-backwards
                            elif center_object[0] > center_frame[0] and 0.7* surface_frame > surface_object:
                                state_for_commands = 0b1100 #right-forward
                            elif center_object[0] > center_frame[0] and 0.7* surface_frame < surface_object:
                                state_for_commands = 0b0011 #right-backwards
                            elif center_object[0] - center_frame[0] and 0.7* surface_frame < surface_object:
                                state_for_commands = 0b0000
                        else:
                            state_for_commands = 0b0000
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
        'w': 0b1000,  # 1st bit
        'a': 0b0100,  # 2nd bit
        's': 0b0010,  # 3rd bit
        'd': 0b0001   # 4th bit 
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
    def press_key(key = None):
        global state_for_blitz
        global state_for_commands
        global state_for_commands_1 
        nonlocal client_connected
        global repeat
        if key in key_map_commands or AI_flag == True:
            if AI_flag == False:
                state_for_commands |= key_map_commands[key]  # Set the bit for the key
            duration = timedelta(seconds=0.2) #schimbat de curand 
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
                    client_socket.close() # Remove invalid client
                    client_connected = False
                    reconnect_client()
                    #reconnect_client(client_socket, client_address, client_connected, server_socket)
            #time.sleep(1)  # Adjust the frequency as needed
 
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

    def code_moves(key1):
        # Set up event listeners for each key       
        for key in key1.keys():
                keyboard.on_press_key(key, lambda e, k=key: press_key(k))
                keyboard.on_release_key(key, lambda e, k=key: release_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

   # Main loop
    try:

        while not stop_flag:
            if AI_flag == True:
                press_key()
                time.sleep(0.1)
            else:
                code_moves(key_map_commands)
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

    image1 = Image.open("up_arrow.jpg")
    image1 = image1.resize((100, 100))
    image2 = Image.open("down_arrow.jpg")
    image2 = image2.resize((100, 100))
    image3 = Image.open("left_arrow.jpg")
    image3 = image3.resize((100, 100))
    image4 = Image.open("right_arrow.jpg")
    image4 = image4.resize((100, 100))

    # Convert the image to a PhotoImage object for use in Tkinter
    photo1 = ImageTk.PhotoImage(image1)
    photo2 = ImageTk.PhotoImage(image2)
    photo3 = ImageTk.PhotoImage(image3)
    photo4 = ImageTk.PhotoImage(image4)

    # Define button actions
    def button1_action():
        print("Up button pressed")

    def button2_action():
        print("Down button pressed")

    def button3_action():
        print("Left button pressed")

    def button4_action():
        print("Right button pressed")

    # Create buttons with actions
    image_button1 = tk.Button(root, image=photo1, command=button1_action)
    image_button2 = tk.Button(root, image=photo2, command=button2_action)
    image_button3 = tk.Button(root, image=photo3, command=button3_action)
    image_button4 = tk.Button(root, image=photo4, command=button4_action)

    # Position the button at a specific location (optional)
    image_button1.place(x=425, y=100)
    image_button2.place(x=425, y=700)
    image_button3.place(x=100, y=400)
    image_button4.place(x=800, y=400)

    # Bind specific keys to button actions
    root.bind('<w>', lambda event: button1_action())  # W key for Up button
    root.bind('<s>', lambda event: button2_action())  # S key for Down button
    root.bind('<a>', lambda event: button3_action())  # A key for Left button
    root.bind('<d>', lambda event: button4_action())  # D key for Right button

    # Redirect stdout to a Text widget
    class TextRedirector:
        def __init__(self, widget):
            self.widget = widget

        def write(self, string):
            self.widget.insert(tk.END, string)  # Insert text at the end
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