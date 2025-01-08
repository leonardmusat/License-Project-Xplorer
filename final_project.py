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

# Set the server IP and port
ip = "192.168.100.81"  # Listen on all available interfaces
state_for_commands = 0b00
state_for_commands_1 = 0b00
repeat = datetime.now()

def udp_stream(server_ip):
    server_port = 8888
    CHUNK_LENGTH = 1460  # Size of each chunk, matching ESP32 code

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((server_ip, server_port))

    print(f"UDP server is listening on {server_ip}:{server_port}")

    # Buffer to hold the image data (using a list to avoid resizing issues)
    image_chunks = []

    while True:
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

    # Function to update the state when a key is pressed
    def press_key(key):
        global state_for_blitz
        global state_for_commands
        global state_for_commands_1 
        global repeat
        if key in key_map_commands:
            state_for_commands |= key_map_commands[key]  # Set the bit for the key
            duration = timedelta(seconds=0.1) #schimbat de curand 
            now = datetime.now()
            if state_for_commands != state_for_commands_1 or now - repeat > duration:
                repeat = now
                state_for_commands_1 = state_for_commands
                client_socket.sendall((format(state_for_commands, '04b') + '\n').encode('utf-8'))
                time.sleep(0.1)
                print(f"Message {state_for_commands} was sent")
 
    def release_key(key):
        global state_for_commands
        if key in key_map_commands:
            state_for_commands &= ~key_map_commands[key]  # Clear the bit for the key
            client_socket.sendall((format(state_for_commands, '04b') + '\n').encode('utf-8'))
            time.sleep(0.1)
            print(f"Message {state_for_commands} was sent")

    def code_moves(key1):
        # Set up event listeners for each key
        for key in key1.keys():
            keyboard.on_press_key(key, lambda e, k=key: press_key(k))
            keyboard.on_release_key(key, lambda e, k=key: release_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

    try:
        while True:
            code_moves(key_map_commands)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the connectionkkk
        client_socket.close()
        server_socket.close()
        print("Connection closed.")

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
        if key in key_map:
            client_socket.sendall((format(trigger, '04b') + '\n').encode('utf-8'))
            time.sleep(0.1)
            print(f"Message {trigger} was sent")

    def code_moves(key1):
        # Set up event listeners for each key
        for key in key1:
            keyboard.on_press_key(key, lambda e, k=key: press_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

    try:
        while True:
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