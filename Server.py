import socket
import os
import threading
from time import sleep, time
import struct
import random
import scapy.all

questionsList = [("2+2", 4), ("5-2", 3), ("9-7", 2), ("8+1", 9),
                 ("6-5", 1), ("9-9", 0), ("5+3", 8), ("3+4", 7)]
devNetwork = True
client1GameThread = None
client2GameThread = None
currQuestion = None
currAnswer = None
ANS_POS = 0
TIME_POS = 1
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5050
MAX_BUFFER_SIZE = 2048
ThreadCount = 0
UDP_PORT = 13117
FORMAT = 'utf-8'
MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE = 0x2
udpMsg = struct.pack('IbH', MAGIC_COOKIE, MESSAGE_TYPE,
                     SERVER_PORT)  # encoding udp message
broadcastIP = "255.255.255.255"
UDP_ADDR = (broadcastIP, UDP_PORT)
winningTeam = -1
needToOffer = True


clientSockets = []
clientNames = []
handleClientLock = threading.Lock()


def offerStage():
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while needToOffer:
        udpSocket.sendto(udpMsg, UDP_ADDR)
        sleep(1)
    udpSocket.close()


def read_name(conn):
    clientName = conn.recv(1024).decode()
    print("received name")
    clientNames.append(clientName)
    print(f"{clientName} has joined the game")
    return clientName


def handle_client(conn, clientIndex, question, answer):
    global winningTeam
    conn.send(question.encode())
    clientAns = conn.recv(1024).decode()
    if(clientAns == answer):  # correct answer
        handleClientLock.acquire()
        if winningTeam == -1:  # if no one has answered yet
            winningTeam = clientIndex
            sendGameSummary()
        handleClientLock.release()
    else:
        handleClientLock.acquire()
        if winningTeam == -1:
            winningTeam = 1-clientIndex
            sendGameSummary()
        handleClientLock.release()


def accept_clients(serverSocket):
    clientSocket1, addr1 = serverSocket.accept()
    print(addr1)
    read_name(clientSocket1)
    clientSocket2, addr2 = serverSocket.accept()
    read_name(clientSocket2)
    clientSockets.append(clientSocket1)
    clientSockets.append(clientSocket2)


def start_server():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((SERVER_IP, SERVER_PORT))
    serverSocket.listen()  # server is listening for client connection
    print("Server started, listening on IP address {}".format(SERVER_IP))
    return serverSocket


'''
returns a tuple of type (string,int) representing (question,answer)
'''


def generateRandomQuestion() -> tuple:
    return random.choice(questionsList)


def sendGameSummary():
    # generate summary string
    msg = "Game Over!\nThe correct answer was {}!\n\nCongratulations to the winner: {}".format(
        currAnswer, clientNames[winningTeam])

    # send summary to client
    clientSoc = clientSockets[0]
    clientSoc.send(msg)
    clientSoc = clientSockets[1]
    clientSoc.send(msg)


def printGameOver():
    print("Game over, sending out offer requests...")


def playGame():
    currQuestion, currAnswer = generateRandomQuestion()
    client1GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[0], 0, currQuestion, currAnswer))
    client2GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[1], 1, currQuestion,  currAnswer))
    client1GameThread.start()
    client2GameThread.start()
    client1GameThread.join(timeout=10.0)
    client2GameThread.join(timeout=10.0)

    # send summary to both clients
    sendGameSummary()

    printGameOver()


def closeConnections():
    clientSockets[0].close()
    clientSockets[1].close()


def Main():
    # if devNetwork:
    #     SERVER_IP = scapy.all.get_if_addr('eth1')
    # else:
    #     SERVER_IP = scapy.all.get_if_addr('eth2')

    global needToOffer
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
