from select import select
import socket
import struct
import sys

bufferSize = 1024
udpSocket = None
tcpSocket = None

teamName = "sasha"
UDP_PORT = 13117

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

def initiateSockets():
    global udpSocket,tcpSocket
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def initTcpConnection(serverAddr):
    try:
        tcpSocket.connect(serverAddr)
        tcpSocket.send((teamName + "\n").encode())
        return True
    except Exception:
        tcpSocket.close()
        return False


def handleGame():
    try:
        welcomeMsg = tcpSocket.recv(bufferSize).decode()
        print("{}{}".format(bcolors.OKCYAN,welcomeMsg))
    except Exception:
        tcpSocket.close()

    inputs, _, _ = select([tcpSocket, sys.stdin], [], [])
    if sys.stdin in inputs:  # client answered
        answer = sys.stdin.readline()[0]  # only 1 digit
        try:
            tcpSocket.send(answer.encode())
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print("{}{}".format(bcolors.OKGREEN,summaryMsg))
        except Exception as e:
            tcpSocket.close()
            print("{}{}".format(bcolors.FAIL,e))

    else:  # other client answered or no one answered
        try:
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print("{}{}".format(bcolors.OKBLUE,summaryMsg))
        except Exception as e:
            tcpSocket.close()
            print("{}{}".format(bcolors.FAIL,e))


def closeConnections():
    tcpSocket.close()
    udpSocket.close()


def Main():
    global udpSocket, tcpSocket
    while True:
        initiateSockets()
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind(("", UDP_PORT))
        print(f"{bcolors.OKBLUE}Client started, listening for offer requests...")

        serverMsg, serverIP = udpSocket.recvfrom(bufferSize)
        serverIP = serverIP[0]
        serverPort = getServerPort(serverMsg)
        if serverPort != -1:
            print("{}Received offer from {},attempting to connect...".format(bcolors.OKGREEN,serverIP))
            serverAddr = (serverIP, serverPort)
            initSuccess = initTcpConnection(serverAddr)
            if initSuccess:
                handleGame()
        else:
            print(f"{bcolors.FAIL}bad offer message or some other socket error")
        closeConnections()


if __name__ == "__main__":
    Main()
