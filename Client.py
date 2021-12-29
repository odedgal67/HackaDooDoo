from select import select
import socket
import struct
import sys

#Colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#Global varibales
bufferSize = 1024
udpSocket = None
tcpSocket = None

teamName = "Google Chromosome"
UDP_PORT = 13117

#----------------------------------------------------------------functions-----------------------------------------------------------------
"""
    Description:
        gets the udp offer message, checks its validity and returns server port

    Params:
        (msg:String)
    Returns:
        server port if msg is valid or -1 if invalid 
"""
def getServerPort(msg):
    try:
        msgParts = struct.unpack("IbH", msg)
        magic = msgParts[0]
        msgType = msgParts[1]
        serverPort = msgParts[2]
        if magic == 0xABCDDCBA and msgType == 0x2:
            return serverPort
        else:
            return -1
    except Exception:
        return -1

"""
    Description:
        Initiating client udp and tcp sockets
    Params:
        ()
    Returns: void
"""
def initiateSockets():
    global udpSocket,tcpSocket
    try:
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except Exception as e:
        print(f"{bcolors.FAIL}Opening socket failed with error message : {e}{bcolors.ENDC}")

"""
    Description:
        Tries to connect to the sever through tcp socket
    Params:
        (serverAddr:tuple(serverIP, serverPort))
    Returns:
        true if connceted succesfully, false if failed
"""
def initTcpConnection(serverAddr):
    try:
        tcpSocket.connect(serverAddr)
        tcpSocket.send((teamName + "\n").encode())
        return True
    except Exception:
        tcpSocket.close()
        return False

"""
    Description:
        the game handler - handles the game logic
    Params:
        ()
    Returns:
        void
"""
def handleGame():
    try:
        welcomeMsg = tcpSocket.recv(bufferSize).decode()
        print("{}{}{}".format(bcolors.OKCYAN,welcomeMsg,bcolors.ENDC))
    except Exception:
        tcpSocket.close()

    #using select to receive input from user and server messages simultaneously
    inputs, _, _ = select([tcpSocket, sys.stdin], [], [])
    if sys.stdin in inputs:  # client answered
        answer = sys.stdin.readline()[0]  # only 1 digit (ignoring the other characters if there are any)
        try:
            tcpSocket.send(answer.encode())
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print("{}{}{}".format(bcolors.OKGREEN,summaryMsg,bcolors.ENDC))
        except Exception as e:
            tcpSocket.close()
            print("{}{}{}".format(bcolors.FAIL,e,bcolors.ENDC))

    else:  # other client answered or no one answered
        try:
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print("{}{}{}".format(bcolors.OKBLUE,summaryMsg,bcolors.ENDC))
        except Exception as e:
            tcpSocket.close()
            print("{}{}{}".format(bcolors.FAIL,e,bcolors.ENDC))

"""
    Description:
        closes the opened tcp and udp sockets
    Params:
        ()
    Returns:
        void
    Raises:
"""
def closeConnections():
    tcpSocket.close()
    udpSocket.close()


def Main():
    global udpSocket, tcpSocket
    while True:
        initiateSockets()
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind(("", UDP_PORT))
        print(f"{bcolors.OKBLUE}Client started, listening for offer requests...{bcolors.ENDC}")

        serverMsg, serverIP = udpSocket.recvfrom(bufferSize)
        serverIP = serverIP[0]
        serverPort = getServerPort(serverMsg)
        if serverPort != -1:
            print("{}Received offer from {},attempting to connect...{}".format(bcolors.OKGREEN,serverIP,bcolors.ENDC))
            serverAddr = (serverIP, serverPort)
            initSuccess = initTcpConnection(serverAddr)
            if initSuccess:
                handleGame()
        else:
            print(f"{bcolors.FAIL}bad offer message or some other socket error{bcolors.ENDC}")
        closeConnections()


if __name__ == "__main__":
    Main()
