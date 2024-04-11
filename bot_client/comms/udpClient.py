import sys
import socket
import fileinput
from enum import IntEnum
from struct import pack, unpack
# UDP_IP = "10.9.70.103"
# UDP_PORT = 8081
UDP_PORT = 5005
UDP_IP = "127.0.0.1"
running = True


class CommandType(IntEnum):
    NONE=-1
    START=0
    STOP=1
    FLUSH=2
    MESSAGE=3

class CommandDirection(IntEnum):
    NONE=-1
    NORTH=0
    EAST=1
    SOUTH=2
    WEST=3
    
START_BYTE = ord("{")
NULL_BYTE = ord("\0")
STOP_BYTE = ord("}")
GARBAGE = 1

class Command:
    """
    Start(1) Null(1) Seqno(2) Type(1) Misc(2) Stop(1)

    Misc:
    Message: Direction(1) Distance(1)
    Flush:  X(1) Y(1)
    """

    def __init__(self):
        self.seqno = -1
        self.type = CommandType.NONE

        # messages
        self.dir = CommandDirection.NONE
        self.dist: int = -1

        # flush
        self.x: int = -1
        self.y: int = -1

    def serialize(self):
        self.checkState()
        msg_arr = [
            START_BYTE,
            NULL_BYTE,
            (self.seqno >> 8) & (0b11111111),
            (self.seqno >> 0) & (0b11111111),
            self.type,
            GARBAGE,
            GARBAGE,
            STOP_BYTE
        ]

        return bytes(msg_arr)
    
    def checkState(self):

        if (self.type == CommandType.NONE):
            raise Exception("Invalid State")
        
        elif (self.type == CommandType.FLUSH):
            if (self.x == -1 or self.y == -1): 
                raise Exception()
            
        elif (self.type == CommandType.MESSAGE):
            if (self.dir == CommandDirection.NONE or self.dist == -1):
                raise Exception()

    # def checkCommand(self, message):
    #     if message[0] != START_BYTE:
    #         raise Exception("Invalid Start Byte")
    #     if message[1] != NULL_BYTE:
    #         raise Exception("Invalid Null Byte")
    #     if message[2] == CommandDirection.NONE or message[3] == CommandDirection.NONE:
    #         raise Exception("Invalid Direction Bytes")
    #     if message[4]== CommandType.NONE:
    #         raise Exception("Invalid Command Type")
    #     if message[5]
        

if __name__ == '__main__':
    print("Running Udp Client target:" + UDP_IP + ":" + str(UDP_PORT))
    while running:
        try :
            MESSAGE = ""
            inputString = input("Input: ")
            inputString = inputString + '\n'

            MESSAGE = bytes(inputString, "ascii")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # (Internet, UDP)
            sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        
        except:
            running = False