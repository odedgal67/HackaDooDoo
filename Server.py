import socket
import os
import threading
from time import sleep, time
import struct
import random
import scapy.all

questionsList = [("2+2", "4"), ("5-2", "3"), ("9-7", "2"), ("8+1", "9"),
                 ("6-5", "1"), ("9-9", "0"), ("5+3", "8"), ("3+4", "7")]
devNetwork = True
client1GameThread = None
client2GameThread = None
currQuestion = None
currAnswer = None
ANS_POS = 0
TIME_POS = 1
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = random.randrange(5000,7000)
MAX_BUFFER_SIZE = 1024
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
    try:
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while needToOffer:
            udpSocket.sendto(udpMsg, UDP_ADDR)
            sleep(1)
        udpSocket.close()
    except Exception as e:
        print("From offerStage" + e)   
        udpSocket.close()    


def read_name(conn):
    try:
        clientName = conn.recv(MAX_BUFFER_SIZE).decode() #recv is returning the name with \n at the end
        clientName = clientName[ : -1] #removing \n in the end of the name
        clientNames.append(clientName)
        print("{} has joined the game".format(clientName))
        return clientName
    except Exception as e:
        print("From read_name" + e)   
        conn.close()


def handle_client(conn, clientIndex, question, answer):
    global winningTeam
    msg = "Welcome to Quick Maths. \nPlayer 1: {} \nPlayer 2: {} \n== \nPlease answer the following question as fast as you can: \nHow much is {}?".format(clientNames[0], clientNames[1],question)
    try:
        conn.send(msg.encode())
        clientAns = conn.recv(MAX_BUFFER_SIZE).decode()

        if(clientAns == answer and clientAns != ""):  # correct answer
            handleClientLock.acquire()
            if winningTeam == -1:  # if no one has answered yet
                winningTeam = clientIndex
                sendGameSummary()
                closeConnections()
            handleClientLock.release()
        elif (clientAns != ""):
            handleClientLock.acquire()
            if winningTeam == -1:
                winningTeam = 1-clientIndex
                sendGameSummary()
                closeConnections()
            handleClientLock.release()
    except Exception as e:
        print("From handle_client" + e)   
        conn.close()


def accept_clients(serverSocket):
    try:
        clientSocket1, addr1 = serverSocket.accept()
        read_name(clientSocket1)
        clientSocket2, addr2 = serverSocket.accept()
        read_name(clientSocket2)
        clientSockets.append(clientSocket1)
        clientSockets.append(clientSocket2)
    except Exception as e:
        print("From accept_clients" + e)    


def start_server():
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSocket.bind((SERVER_IP, SERVER_PORT))
        serverSocket.listen()  # server is listening for client connection
        print("Server started, listening on IP address {}".format(SERVER_IP))
        return serverSocket
    except Exception as e:
        print("From start_server" + e)       


'''
returns a tuple of type (string,int) representing (question,answer)
'''


def generateRandomQuestion() -> tuple:
    return random.choice(questionsList)


def sendGameSummary():
    try:
        msg = ""
        if winningTeam != -1:
            # generate summary string
            msg = "Game Over!\nThe correct answer was {}!\n\nCongratulations to the winner: {}".format(
                currAnswer, clientNames[winningTeam]).encode()
        else:
            msg = "Game Over!\nThe correct answer was {}!\n\nThe game ended with a tie".format(
                currAnswer).encode()

            # send summary to client
        clientSoc = clientSockets[0]
        clientSoc.send(msg)
        clientSoc = clientSockets[1]
        clientSoc.send(msg)
    except Exception as e:
        print("From sendGameSummary" + e)

        


def printGameOver():
    print("Game over, sending out offer requests...")


def playGame():
    try:
        global currQuestion, currAnswer
        currQuestion, currAnswer = generateRandomQuestion()
        client1GameThread = threading.Thread(
            target=handle_client, args=(clientSockets[0], 0, currQuestion, currAnswer))
        client2GameThread = threading.Thread(
            target=handle_client, args=(clientSockets[1], 1, currQuestion,  currAnswer))
        client1GameThread.start()
        client2GameThread.start()
        client1GameThread.join(timeout=4.0)
        client2GameThread.join(timeout=4.0)
        if (client1GameThread.is_alive() and client2GameThread.is_alive()):
            sendGameSummary()
        printGameOver()
    except Exception as e:
        print("From playGame" + e)       


def closeConnections():
    try:
        clientSockets[0].close()
        clientSockets[1].close()
    except Exception as e:
        print("From closeConnections" + e)       

def resetGlobalVars():
    global winningTeam,needToOffer,clientSockets,clientNames
    winningTeam = -1
    needToOffer = True
    clientSockets = []
    clientNames = []

def Main():
    # if devNetwork:
    #     SERVER_IP = scapy.all.get_if_addr('eth1')
    # else:
    #     SERVER_IP = scapy.all.get_if_addr('eth2')

    serverSocket = start_server()
    while True:
        global needToOffer
        offer_thread = threading.Thread(target=offerStage)
        offer_thread.start()
        accept_clients(serverSocket)
        needToOffer = False
        offer_thread.join()
        sleep(2)
        playGame()
        resetGlobalVars()
    # closeConnections()

    #TODO: sigint and excpetion check


if __name__ == '__main__':
    Main()
