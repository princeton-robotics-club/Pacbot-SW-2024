import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
print("Running UDP echo server on: " + UDP_IP + ":" + str(UDP_PORT))

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print(data.decode("ascii"), end="", flush=True)
