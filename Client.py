from select import select
import socket
import struct
import sys

bufferSize = 1024
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
teamName = "sasha"
UDP_PORT = 13117


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
        print(welcomeMsg)
    except Exception:
        tcpSocket.close()

    inputs, _, _ = select([tcpSocket, sys.stdin], [], [])
    if sys.stdin in inputs:  # client answered
        answer = sys.stdin.readline()[0]  # only 1 digit
        try:
            tcpSocket.send(answer.encode())
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print(summaryMsg)
        except Exception as e:
            tcpSocket.close()
            print(e)

    else:  # other client answered or no one answered
        try:
            summaryMsg = tcpSocket.recv(bufferSize).decode()
            print(summaryMsg)
        except Exception as e:
            tcpSocket.close()
            print(e)


def closeConnections():
    tcpSocket.close()
    udpSocket.close()


def Main():
    global udpSocket, tcpSocket
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udpSocket.bind(("", UDP_PORT))
    print("Client started, listening for offer requests...")

    serverMsg, serverIP = udpSocket.recvfrom(bufferSize)
    serverIP = serverIP[0]
    serverPort = getServerPort(serverMsg)
    if serverPort != -1:
        print("Received offer from {},attempting to connect...".format(serverIP))
        serverAddr = (serverIP, serverPort)
        initSuccess = initTcpConnection(serverAddr)
        if initSuccess:
            handleGame()
    else:
        print("bad offer message or some other socket error")
    closeConnections()


if __name__ == "__main__":
    Main()
