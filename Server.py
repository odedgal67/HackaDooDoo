import socket
import os
import threading
from time import sleep, time
import struct

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5050
MAX_BUFFER_SIZE = 2048
ThreadCount = 0
UDP_PORT = 13117
FORMAT = 'utf-8'
MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE = 0x2
broadcastIP = "255.255.255.255"
UDP_ADDR = (broadcastIP, UDP_PORT)
udpMsg = struct.pack('IbH', MAGIC_COOKIE, MESSAGE_TYPE,
                     SERVER_PORT)  # encoding udp message

udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

clientThreads = []
clientSockets = []
clientNames = []
clientAnswers = []


def offerStage():
    while needToOffer:
        udpSocket.sendto(udpMsg, UDP_ADDR)
        sleep(1)
    udpSocket.close()


def read_name(conn):
    clientName = conn.recv(1024).decode()
    clientNames.append(clientName)
    print(f"{clientName} has joined the game")
    return clientName


def handle_client(conn, addr, question, answer, clientIndex, otherThread):
    conn.send(question.encode())
    clientAns = conn.recv(1024).decode()
    clientAnswers[clientIndex] = (clientAns, time())
    clientThreads[1-clientIndex].raise_exception()


def accept_clients(serverSocket):
    clientSocket1, addr1 = serverSocket.accept()
    read_name(clientSocket1)
    #threading.Thread(target=handle_client, args=(clientSocket1, addr1)).start()
    clientSockets.append(clientSocket1)
    clientSocket2, addr2 = serverSocket.accept()
    read_name(clientSocket2)

    #threading.Thread(target=handle_client, args=(clientSocket2, addr2)).start()
    clientSockets.append(clientSocket2)


def start_server():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    serverSocket.bind((SERVER_IP, SERVER_PORT))
    serverSocket.listen()  # server is listening for client connection
    return serverSocket


def calculateWinner():
    client1Time = clientAnswers[0]


def sendGameStats():
    winnerIndex = calculateWinner()


def playGame():
    client1GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[0]))
    client2GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[1]))
    clientThreads.append(client1GameThread)
    clientThreads.append(client2GameThread)
    client1GameThread.start()
    client2GameThread.start()
    client1GameThread.join(timeout=10.0)
    client2GameThread.join(timeout=10.0)
    sendGameStats()


def Main():
    global needToOffer
    needToOffer = True
    serverSocket = start_server()
    offer_thread = threading.Thread(target=offerStage)
    offer_thread.start()
    accept_clients(serverSocket)
    needToOffer = False
    offer_thread.join()
    sleep(10)
    playGame()
    closeConnections()


# def accept_clients(server):
#     while True:
#         client, client_address = server.accept()


# def send_offer_message:


# start_server()
# while True:


if __name__ == '__main__':
    Main()
