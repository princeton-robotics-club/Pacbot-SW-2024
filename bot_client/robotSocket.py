# Library for UDP sockets
import socket

# Enums for command info
from enum import IntEnum

# Terminal colors
from terminalColors import *

# Command types
from shared import CommandType, CommandDirection


dirMap = {
    b'w': CommandDirection.NORTH,
    b'a': CommandDirection.WEST,
    b's': CommandDirection.SOUTH,
    b'd': CommandDirection.EAST
}

class RobotSocket:

    def __init__(self, robotIP: str, robotPort: int) -> None:

        # Robot address
        self.robotIP = robotIP
        self.robotPort = robotPort

        # UDP Socket
        self.sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self.sock.setblocking(False)

        # Received sequence number and data
        self.recvSeq: int
        self.recvData: bytes = bytes([0,0,0,0,0,0,0])

        # Data
        self.NULL: int = 0
        self.seq0: int = 1
        self.seq1: int = 0
        self.typ:  int = int(CommandType.FLUSH)
        self.val1: int = 0
        self.val2: int = 0
        self.done: bool = False

    def moveNoCoal(self, command: bytes, row: int, col: int, dist: int, updateSeq:bool=True) -> None:


        if command == b'.':
            return

        # Update the sequence number, if applicable
        if updateSeq:
            self.updateSeq()

        # Overwrite the output for a move command
        self.typ  = int(CommandType.MOVE)
        self.val1 = dirMap[command]
        self.val2 = dist

        # Dispatch the message
        self.dispatch(row, col)

        print(f'{CYAN}sending command{NORMAL}', ' command:', command, ' dist', dist, '->', row, col, " #", int(self.seq1 << 8 | self.seq0))

    def flush(self, row: int, col: int) -> None:

        print('flush', row, col)

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.FLUSH)
        self.val1 = 0
        self.val2 = 0

        # Dispatch the message
        self.dispatch(row, col)

    def start(self) -> None:

        print('start')

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.START)
        self.val1 = 0
        self.val2 = 0

        # Dispatch the message
        self.dispatch(0, 0)

    def stop(self) -> None:

        print('stop')

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.STOP)
        self.val1 = 0
        self.val2 = 0

        # Dispatch the message
        self.dispatch(0, 0)

    """ Wait returns if the robot needs a new command
    - when: recvSeq == most recent sent seqno and robot says its done
    """
    def wait(self) -> bool:
        try:
            while True:
                self.recvData, _ = self.sock.recvfrom(1024) # type: ignore
        except:
            pass

        # Received sequence number
        recvSeq = (self.recvData[1] << 8 | self.recvData[2]) # type: ignore

        # Is done
        done = not bool(self.recvData[5])

        # debug
        if done != self.done:
            if done:
                print(f'{RED}robot just told us it\'s done{NORMAL} #', int(recvSeq))
            else:
                print(f'{GREEN}robot has started executing{NORMAL} #', int(recvSeq))

        # update
        needsNewCommand = (self.seq1 << 8 | self.seq0) == recvSeq and self.done
        self.recvSeq = recvSeq
        self.done = done

        return needsNewCommand

    def updateSeq(self) -> None:

        # Send the message only if up to date
        if self.recvSeq == (self.seq1 << 8 | self.seq0):

            # Increment the sequence number
            self.seq0 += 1

            # First overflow
            if self.seq0 > 127:
                self.seq0 = 0
                self.seq1 += 1

            # Second overflow
            if self.seq1 > 127:
                self.seq1 = 0

    def dispatch(self, row: int, col: int) -> None:

        message = ""
        inputString = "{{[{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}]}}".format(
            self.NULL, self.seq1, self.seq0, self.typ, row, col, self.val1, self.val2
        )
        inputString = inputString + '\n'
        i = 0

        while i < len(inputString):
            currentChar = inputString[i]
            if (currentChar == "["):
                currentChar = chr(int("0x" + inputString[i+1:i+3], 16))
                i += 3
            message += currentChar
            i += 1

        message = bytes(message, "ascii")

        # print(message)

        self.sock.sendto(message, (self.robotIP, self.robotPort))