

import socket


# Command types
from shared import CommandType, CommandDirection

# For checking coordinates
from gameState import GameState

UDP_IP = "127.0.0.1"
UDP_PORT = 5005


class PacSimSocket:

    def __init__(self):

        # Robot address
        self.botClientIP = "localhost"
        self.botClientPort = robotPort

        # UDP Socket
        self.sock = socket.socket(socket.AF_INET, # Internet
                            socket.SOCK_DGRAM) # UDP
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)

        # Gamestate for checking bounds
        self.gameState: GameState = GameState()

        # Received sequence number and data
        self.recvSeq: int = 0
        self.recvData: bytes = bytes([0,0,0,0,0,0,0,0])

        # Data
        self.NULL: int = 0
        self.seq0: int = -1
        self.seq1: int = -1
        self.typ : int = int(CommandType.FLUSH)
        self.row : int = -1
        self.col : int = -1
        self.val1: int = -1
        self.val2: int = -1

        # finished executing command
        self.done: bool = False

        # # Previous values for checking
        # self.lastRecvSeq: int = -1
        # self.lastTyp : int = int(CommandType.FLUSH)
        # self.lastRow : int = -1
        # self.lastCol : int = -1
        # self.lastVal1: int = -1
        # self.lastVal2: int = -1

    # '''
    # Records all current state values
    # '''
    # def recordState(self) -> None:
    #     self.lastSeq0 = self.seq0
    #     self.lastSeq1 = self.seq1
    #     self.lastTyp  = self.typ 
    #     self.lastRow  = self.row 
    #     self.lastCol  = self.col 
    #     self.lastVal1 = self.val1
    #     self.lastVal2 = self.val2

    '''
    Returns true if the new state is valid
    '''
    def validateState(self,
            recvSeq,
            typ,
            row,
            col,
            val1,
            val2) -> bool:
        
        # check valid seqno TODO: Double check logic
        if recvSeq < self.recvSeq and not (recvSeq == 0 and self.recvSeq == 65535):
            print("Dropping datagram: invalid sequence number")
            return False

        # check type
        if typ > 3:
            print("Dropping datagram: got invalid typ " + str(typ))
            return False

        # check row col in bounds
        if (row < 0 or row >= 31) or (col < 0 or col >= 28):
            print("Dropping datagram: row,col not in bounds: " + str(row) + "," + str(col))
            return False

        # check row col no wall at
        if self.gameState.wallAt(row, col):
            print("Dropping datagram: given a row,col in a wall: " + str(row) + "," + str(col))
            return False

        # movement commands only
        if typ == CommandType.MOVE:

            # simulate pacbot movement
            checkRow = self.row
            checkCol = self.col
            collisions = []
            if val1 == int(CommandDirection.NORTH):
                checkRow = self.row - val2
                collisions = [(x, checkCol) for x in range(checkRow, self.row) if self.gameState.wallAt(x, checkCol)]
            elif val1 == int(CommandDirection.SOUTH):
                checkRow = self.row + val2
                collisions = [(x, checkCol) for x in range(self.row+1, checkRow+1) if self.gameState.wallAt(x, checkCol)]
            elif val1 == int(CommandDirection.EAST):
                checkCol = self.col + val2
                collisions = [(checkRow, x) for x in range(self.col+1, checkCol+1) if self.gameState.wallAt(checkRow, x)]
            elif val1 == int(CommandDirection.WEST):
                checkCol = self.col - val2
                collisions = [(checkRow, x) for x in range(checkCol, self.col) if self.gameState.wallAt(checkRow, x)]
            elif val1 == int(CommandDirection.NONE):   # no direction
                pass
            else:
                print("Dropping datagram: received an unknown command direction: " + str(val1))

            # check direction dist end up at row col valid move or any collisions
            if len(collisions) > 0 or (checkRow != row or checkCol != col):
                falseRow = row
                falseCol = col
                if val1 == int(CommandDirection.NORTH):
                    falseRow = row + val2
                elif val1 == int(CommandDirection.SOUTH):
                    falseRow = row - val2
                elif val1 == int(CommandDirection.EAST):
                    falseCol = col - val2
                elif val1 == int(CommandDirection.WEST):
                    falseCol = col + val2

                print("Dropping datagram:",end="") 
                if len(collisions) > 0:
                    print(" collisions at ", end="")
                    for coll in collisions:
                        print(str(coll[0])+","+str(coll[1]), end="")
                    print()

                print("\t(row,col) pb client wanted: " + str(falseRow) + "," + str(falseCol) + "->" + str(row) + "," + str(col) + " in reality would be: " + str(self.row) + "," + str(self.col) + "->" + str(checkRow) + "," + str(checkCol))

                return False

        return True

    '''
    Update State according to message
    '''
    def updateState(self) -> None:
        # Check first is null byte
        if int(self.recvData[0]) != 0:
            print("Dropping datagram: first byte is not null byte")
            return

        # Received sequence number
        recvSeq = (self.recvData[1] << 8 | self.recvData[2]) # type: ignore
        # TODO: check that seqno in order

        # command type
        typ = self.recvData[3]

        # location
        row = self.recvData[4]
        col = self.recvData[5]

        # values
        val1 = self.recvData[6]
        val2 = self.recvData[7]

        if not self.validateState(recvSeq, typ, row, col, val1, val2):
            print("invalid state!")
            return
        
        self.recvSeq = recvSeq
        self.typ = typ
        self.row = row
        self.col = col
        self.val1 = val1
        self.val2 = val2


    '''
    Generate a response message
    '''
    def generateResponse(self):

        # TODO: have a randomizer for generating done

        message = ""
        inputString = "{{[{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}][{:02x}]}}".format(
            0, self.seq1, self.seq0, 0, 0, self.done, 0
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

        print(message)
        return message

    '''
    Handle communications with BotClient
    '''
    def start(self) -> None:
        try:
            while True:
                # handle incoming data
                self.recvData, _ = self.sock.recvfrom(1024) # type: ignore
                # TODO: add a check that address is correct
                # self.recordState()
                self.updateState()

                # respond with ack
                message = self.generateResponse()
                self.sock.sendto(message, (self.botClientIP, self.botClientPort))
        except:
            pass



def main():
    pass

if __name__ == '__main__':
    main()