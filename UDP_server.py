import socket
import cv2
import numpy as np
import threading
import keyboard
import time

# Set the server IP and port
ip = "192.168.100.40"  # Listen on all available interfaces
state_for_blitz = 0b00
state_for_commands = 0b00

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

def blitz(server_ip):
    server_port = 8889

    # Define each key with its respective bit position
    key_map_blitz = {
        'k': 0b1111,  # 1st bit
    }

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
    server_socket.listen(2)
    print(f"Listening for connections on {server_ip}:{server_port}...")

    # Accept a single incoming connection
    client_socket, client_address = server_socket.accept()
    print(f"Connected to {client_address}")

    # Function to update the state when a key is pressed
    def press_key(key):
        global state_for_blitz
        global state_for_commands
        if key in key_map_blitz:
            state_for_blitz = key_map_blitz[key]  # Set the bit for the key
            client_socket.sendall((format(state_for_blitz, '02b') + '\n').encode('utf-8'))
            time.sleep(0.1)
            print(f"Message {state_for_blitz} was sent")
        elif key in key_map_commands:
            state_for_commands |= key_map_commands[key]  # Set the bit for the key
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

    def code_moves(key1, key2):
        # Set up event listeners for each key
        for key in key1.keys():
            keyboard.on_press_key(key, lambda e, k=key: press_key(k))
        for key in key2.keys():
            keyboard.on_press_key(key, lambda e, k=key: press_key(k))
            keyboard.on_release_key(key, lambda e, k=key: release_key(k))

        # Wait for 'esc' to exit
        keyboard.wait('esc')

    try:
        while True:
            code_moves(key_map_blitz, key_map_commands)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the connectionkkk
        client_socket.close()
        server_socket.close()
        print("Connection closed.")

thread1 = threading.Thread(target=udp_stream, args=(ip,))
thread2 = threading.Thread(target=blitz, args=(ip,))

thread1.start()
thread2.start()

thread1.join()
thread2.join()
