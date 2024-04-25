# Library for UDP sockets
import socket

# Enums for command info
from enum import IntEnum

# Game state for event handlers
from serverMessage import ServerMessage
from gameState import GameModes, Location # type: ignore

from collections import deque

class CommandType(IntEnum):
    STOP=0
    START=1
    FLUSH=2
    MOVE=3

class CommandDirection(IntEnum):
    NONE=-1
    NORTH=0
    EAST=1
    WEST=2
    SOUTH=3

dirMap = {
    b'w': CommandDirection.NORTH,
    b'a': CommandDirection.WEST,
    b's': CommandDirection.SOUTH,
    b'd': CommandDirection.EAST
}

class RobotSocket:

    def __init__(self, robotIP: str, robotPort: int, pbClient) -> None: # type: ignore

        # Robot address
        self.robotIP = robotIP
        self.robotPort = robotPort

        # UDP Socket
        self.sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self.sock.setblocking(False)

        # Received sequence number and data
        self.recvSeq: int = -1
        self.recvData: bytes = bytes([0,0,0,0,0,0])

        # Data
        self.NULL: int = 0
        self.seq0: int = 1
        self.seq1: int = 0
        self.typ:  int = int(CommandType.FLUSH)
        self.row: int = 0
        self.col: int = 0
        self.dir: int = 0
        self.dist: int = 0

        self.initEventHandlers(pbClient) # type: ignore

    def initEventHandlers(self, pbClient): # type: ignore
        # set up event handlers
        pbClient.subscribeToGameModeStartStopChange(self.handleGameModeStartStopChange) # type: ignore

    def moveNoCoal(self, serverCommand: ServerMessage, row: int, col: int, buffer: deque[ServerMessage]) -> None:
        command: bytes = serverCommand.getBytes()
        dist: int = serverCommand.getDist()
        print('sending command ', command, ' dist:', dist, ' row:', row, ' col:', col)

        if command == b'.':
            return

        # if we changed our mind, return
        if command == b"f":
            self.flush(row, col)
            return
        self.flush(row,col)

        # get the target row and col
        cvRow = row
        cvCol = col
        row = serverCommand.getRow()
        col = serverCommand.getCol()

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a move command
        self.typ  = int(CommandType.MOVE)
        self.dir = dirMap[command]
        self.dist = dist

        # update the location to match target location
        self.row = row
        self.col = col


        # if self.dir == CommandDirection.NORTH:
        #     targetRow = row - self.dist
        #     targetCol = col
        # elif self.dir == CommandDirection.WEST:
        #     targetRow = row
        #     targetCol = col - self.dist
        # elif self.dir == CommandDirection.SOUTH:
        #     targetRow = row + self.dist
        #     targetCol = col
        # elif self.dir == CommandDirection.EAST:
        #     targetRow = row
        #     targetCol = col + self.dist
        # else: # NONE
        #     print("Hey telling robot to move in no direction...") # this shouldn't happen
        #     targetRow = row
        #     targetCol = col


        # self.row = targetRow
        # self.col = targetCol

        # drop if doesn't line up with cv
        if self.dir == CommandDirection.NORTH:
            backtrackRow = row + self.dist
            backtrackCol = col
        elif self.dir == CommandDirection.WEST:
            backtrackRow = row
            backtrackCol = col + self.dist
        elif self.dir == CommandDirection.SOUTH:
            backtrackRow = row - self.dist
            backtrackCol = col
        elif self.dir == CommandDirection.EAST:
            backtrackRow = row
            backtrackCol = col - self.dist
        else: # NONE
            print("Hey telling robot to move in no direction...") # this shouldn't happen
            backtrackRow = row
            backtrackCol = col

        print("target destination: ", self.row, ' ', self.col)
        if not(self.row == 32 and self.col == 32):
            assert(31 >= self.row >= 0)
            assert(28 >= self.col >= 0)


        if backtrackRow != cvRow or backtrackCol != cvCol:

            # cv row, col is also what gamestate believe row, col to be
            print(f"sent dist: {self.dist}\ncv says:    {cvRow} {cvCol}\nmsg thinks: {backtrackRow} {backtrackCol}\n[!] dropping msg ...")
            print("current msg buffer (head is first):")
            for msg in buffer:
                msg_cmd  = msg.getBytes()
                msg_dist = msg.getDist()
                msg_row  = msg.getRow()
                msg_col  = msg.getCol()
                print(f"    cmd: {msg_cmd} d: {msg_dist} r: {msg_row} c: {msg_col}")


            #for msg in self.state.writeServerBuf:
            #    print(msg)


            #print('dist: ', self.dist)
            #print("cv: ", cvRow, ' ', cvCol, ' instead backtracked to: ', backtrackRow, ' ', backtrackCol)
            #print("Dropping message...")
            return



        # Dispatch the message
        print('-- msg dispatched ...')
        self.dispatch()

    def flush(self, row: int, col: int) -> None:

        print('flush ---------------- ', row, col)

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.FLUSH)
        self.row = row
        self.col = col
        self.dir = 0
        self.dist = 0

        # Dispatch the message
        self.dispatch()

    def handleGameModeStartStopChange(self, isRunning: bool, pbLoc: Location) -> None:
        if (isRunning):
            self.start(pbLoc.row, pbLoc.col)
        else:
            self.stop(pbLoc.row, pbLoc.col)

    def start(self, row: int, col: int) -> None:
        print('start', row, col)

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.START)
        self.row = 0
        self.col = 0
        self.dir = 0
        self.dist = 0

        # Dispatch the message
        self.dispatch()

    def stop(self, row: int, col: int) -> None:

        print('stop', row, col)

        # Update the sequence number, if applicable
        self.updateSeq()

        # Overwrite the output for a flush
        self.seq0 = self.recvData[2]
        self.seq1 = self.recvData[1]
        self.typ  = int(CommandType.STOP)
        self.row = 0
        self.col = 0
        self.dir = 0
        self.dist = 0

        # Dispatch the message
        self.dispatch()

    def wait(self) -> None:
        try:
            while True:
                # format: "{,#,#,row,col,}"
                self.recvData, _ = self.sock.recvfrom(1024) # type: ignore
        except:
            pass

        # Received sequence number
        self.recvSeq = (self.recvData[1] << 8 | self.recvData[2]) # type: ignore

        # TODO: Check if bot says our message told it to do illegal move


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

    def dispatch(self) -> None:

        message = ""
        inputString = "{{[{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}]}}".format(
            self.NULL, self.seq1, self.seq0, self.typ, self.row, self.col, self.dir, self.dist
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

        # print("message: " + str(message))

        self.sock.sendto(message, (self.robotIP, self.robotPort))