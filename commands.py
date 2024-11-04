import socket
import keyboard  # Requires the `keyboard` library
import time

# Initial state (binary: 0000)
state = 0b0000
# Define server IP address and port
server_ip = '192.168.100.37'  # Update this to your server's IP
server_port = 8889

# Define each key with its respective bit position
key_map = {
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
server_socket.listen(1)
print(f"Listening for connections on {server_ip}:{server_port}...")

# Accept a single incoming connection
client_socket, client_address = server_socket.accept()
print(f"Connected to {client_address}")

# Function to update the state when a key is pressed
def press_key(key):
    global state
    if key in key_map:
        state |= key_map[key]  # Set the bit for the key
        client_socket.sendall((format(state, '04b') + '\n').encode('utf-8'))
        time.sleep(0.1)
        print(f"Message {state} was sent")

# Function to update the state when a key is released
def release_key(key):
    global state
    if key in key_map:
        state &= ~key_map[key]  # Clear the bit for the key
        client_socket.sendall((format(state, '04b') + '\n').encode('utf-8'))
        time.sleep(0.1)
        print(f"Message {state} was sent")
        
def code_moves(all_key):
    # Set up event listeners for each key
    for key in all_key.keys():
        keyboard.on_press_key(key, lambda e, k=key: press_key(k))
        keyboard.on_release_key(key, lambda e, k=key: release_key(k))

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




