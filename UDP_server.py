import socket
import cv2
import numpy as np

# Set the server IP and port
server_ip = "192.168.100.40"  # Listen on all available interfaces
server_port = 8888
CHUNK_LENGTH = 1460  # Size of each chunk, matching ESP32 code

# Create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind((server_ip, server_port))

print(f"UDP server is listening on {server_ip}:{server_port}")

# Buffer to hold the image data (using a list to avoid resizing issues)
image_chunks = []

# Variables for FPS calculation
nb_frames = 0
fps_last_time = cv2.getTickCount()

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

        # FPS calculation and display
        nb_frames += 1
        current_time = cv2.getTickCount()
        time_diff = (current_time - fps_last_time) / cv2.getTickFrequency()
        if time_diff >= 1.0:
            print(f"FPS: {nb_frames}")
            nb_frames = 0
            fps_last_time = current_time

        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Clean up resources
udp_socket.close()
cv2.destroyAllWindows()