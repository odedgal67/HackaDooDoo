import socket
import os
import threading
from time import sleep, time
import struct
import random


questionsList = [("2+2", 4), ("5-2", 3), ("9-7", 2), ("8+1", 9),
                 ("6-5", 1), ("9-9", 0), ("5+3", 8), ("3+4", 7)]
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
broadcastIP = "255.255.255.255"
UDP_ADDR = (broadcastIP, UDP_PORT)
udpMsg = struct.pack('IbH', MAGIC_COOKIE, MESSAGE_TYPE,
                     SERVER_PORT)  # encoding udp message

udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

clientThreads = []
clientSockets = []
clientNames = []
clientAnswers = []  # list of tuples (answer, time)


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


def handle_client(conn, question, clientIndex, otherThread):
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


'''
    *
    return value - 
        0   - client 1 won
        1   - client 2 won
       -1   - Draw
    *
'''


def calculateWinner() -> int:
    c1Ans = clientAnswers[0][ANS_POS]
    c1Time = float(clientAnswers[0][TIME_POS])
    c2Ans = clientAnswers[1][ANS_POS]
    c2Time = float(clientAnswers[1][TIME_POS])

    if(c1Ans == currAnswer):
        if(c2Ans == currAnswer):
            # both are correct
            if(c1Time < c2Time):  # c1 is first
                return 0
            elif (c1Time > c2Time):  # c2 is first
                return 1
            else:
                return -1  # both at the same time - draw
        else:
            # only c1 is correct
            return 0
    else:
        #c1 is wrong
        if(c2Ans == currAnswer):
            # only c2 is correct
            return 1
        else:
            # both are wrong
            return -1


'''
returns a tuple of type (string,int) representing (question,answer)
'''


def generateRandomQuestion() -> tuple:
    return random.choice(questionsList)


def sendGameSummary(clientIndex):
    # generate summary string
    winnerIndex = calculateWinner()
    msg = "Game Over!\nThe correct answer was {}!\n\nCongratulations to the winner: {}".format(
        currAnswer, clientNames[winnerIndex])

    # send summary to client
    clientSoc = clientSockets[clientIndex]
    clientSoc.send(msg)


def playGame():
    client2GameThread = None  # temp value
    currQuestion, currAnswer = generateRandomQuestion()
    client1GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[0], currQuestion, 0, client2GameThread))
    client2GameThread = threading.Thread(
        target=handle_client, args=(clientSockets[1], currQuestion, 1, client1GameThread))
    clientThreads.append(client1GameThread)
    clientThreads.append(client2GameThread)
    client1GameThread.start()
    client2GameThread.start()
    client1GameThread.join(timeout=10.0)
    client2GameThread.join(timeout=10.0)

    # send summary to both clients
    sendGameSummary(0)
    sendGameSummary(1)


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
