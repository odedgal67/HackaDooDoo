import socket
import os
import threading
from time import sleep, time
import struct
import signal
import random
import scapy.all
import sys

# Colors


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


# Questions and answers bank
questionsList = [("2+2", "4"), ("5-2", "3"), ("9-7", "2"), ("8+1", "9"),
                 ("6-5", "1"), ("8-9+2", "1"), ("5+3", "8"), ("3+4", "7"),
                 ("6+4-5", "5"), ("2+6-7+1", "2"), ("(5*2)-3",
                                                    "7"), ("((5*10)/2)-19", "6"),
                 ("log(8)*((9/3)/3)", "3")]

# Global variables
def_tstp_handler = None
currQuestion = None
currAnswer = None
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = None
MAX_BUFFER_SIZE = 1024
UDP_PORT = 13117
FORMAT = 'utf-8'
MAGIC_COOKIE = 0xabcddcba
MESSAGE_TYPE = 0x2
udpMsg = None
broadcastIP = "255.255.255.255"
UDP_ADDR = (broadcastIP, UDP_PORT)
winningTeam = -1
needToOffer = True
serverSocket = None
clientSockets = []
clientNames = []
handleClientLock = threading.Lock()


# -----------------------------------------------------functions--------------------------------------------------------------

"""
    Description:
        offer thread function that broadcasts an offer message every second
    Params:
        ()
    Returns:
        void
"""


def offerStage():
    try:
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while needToOffer:
            udpSocket.sendto(udpMsg, UDP_ADDR)
            sleep(1)
        udpSocket.close()
    except Exception as e:
        print("{}From offerStage {}{}".format(bcolors.FAIL, e, bcolors.ENDC))
        udpSocket.close()


"""
    Description:
        read the client name from the client socket
    Params:
        (conn:Socket)
    Returns:
        void
"""


def read_name(conn):
    try:
        # recv is returning the name with \n at the end
        clientName = conn.recv(MAX_BUFFER_SIZE).decode()
        clientName = clientName[: -1]  # removing \n in the end of the name
        clientNames.append(clientName)
        print("{}{} has joined the game{}".format(
            bcolors.OKGREEN, clientName, bcolors.ENDC))
    except Exception as e:
        print("{}From read_name {}{}".format(bcolors.FAIL, e, bcolors.ENDC))
        conn.close()


"""
    Description:
        the client thread function that sends the question and waits for answer
    Params:
        (conn:Socket,clientIndex:int,question:String,answer:String)
    Returns:
        void
"""


def handle_client(conn, clientIndex, question, answer):
    global winningTeam
    msg = "Welcome to Quick Maths. \nPlayer 1: {} \nPlayer 2: {} \n== \nPlease answer the following question as fast as you can: \nHow much is {}?".format(
        clientNames[0], clientNames[1], question)
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
        print("{}From handle_client {}{}".format(
            bcolors.FAIL, e, bcolors.ENDC))
        conn.close()


"""
    Description:
        accept two clients to the game and add them to the list of clients
    Params:
        (serverSocket:Socket)
    Returns:
        void
"""


def accept_clients(serverSocket):
    try:
        clientSocket1, addr1 = serverSocket.accept()
        read_name(clientSocket1)
        clientSocket2, addr2 = serverSocket.accept()
        read_name(clientSocket2)
        clientSockets.append(clientSocket1)
        clientSockets.append(clientSocket2)
    except Exception as e:
        print("{}From accept_clients {}{}".format(
            bcolors.FAIL, e, bcolors.ENDC))


"""
    Description:
        starts the server socket and returns it
    Params:
        ()
    Returns:
        void
"""


def start_server():
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverSocket.bind((SERVER_IP, SERVER_PORT))
        serverSocket.listen(2)  # server is listening for client connection
        print("{}Server started, listening on IP address {}{}".format(
            bcolors.OKCYAN, SERVER_IP, bcolors.ENDC))
        return serverSocket
    except Exception as e:
        print("{}From start_server {}{}".format(bcolors.FAIL, e, bcolors.ENDC))


"""
    Description:
        returns a tuple of type (string,int) representing (question,answer)
    Params:
        ()
    Returns:
        tuple(String,int)
"""


def generateRandomQuestion() -> tuple:
    return random.choice(questionsList)


"""
    Description:
        sends the clients the summary of the game
    Params:
        ()
    Returns:
        void
"""


def sendGameSummary():
    try:
        msg = ""
        if winningTeam != -1:
            # generate summary string
            msg = "Game Over!\nThe correct answer was {}!\n\nCongratulations to the winner: {}{}".format(
                currAnswer, clientNames[winningTeam], bcolors.ENDC).encode()
        else:
            msg = "Game Over!\nThe correct answer was {}!\n\nThe game ended with a tie{}".format(
                currAnswer, bcolors.ENDC).encode()

            # send summary to client
        clientSoc = clientSockets[0]
        clientSoc.send(msg)
        clientSoc = clientSockets[1]
        clientSoc.send(msg)
    except Exception as e:
        print("{}From sendGameSummary {}{}".format(
            bcolors.FAIL, e, bcolors.ENDC))


"""
    Description:
        prints a game over message
    Params:
        ()
    Returns:
        void
"""


def printGameOver():
    print("{}Game over, sending out offer requests...{}".format(
        bcolors.OKBLUE, bcolors.ENDC))


"""
    Description:
        creates the two client threads and activates them
    Params:
        ()
    Returns:
        void
"""


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
        client1GameThread.join(timeout=10.0)
        client2GameThread.join(timeout=10.0)
        if (client1GameThread.is_alive() and client2GameThread.is_alive()):
            sendGameSummary()
        printGameOver()
    except Exception as e:
        print("{}From playGame {}{}".format(bcolors.FAIL, e, bcolors.ENDC))


"""
    Description:
        closes the opened client sockets 
    Params:
        ()
    Returns:
        void
"""


def closeConnections():
    try:
        if(len(clientSockets) == 2):
            clientSockets[0].close()
            clientSockets[1].close()
        elif (len(clientSockets) == 1):
            clientSockets[0].close()

    except Exception as e:
        print("{}From closeConnections {}{}".format(
            bcolors.FAIL, e, bcolors.ENDC))


"""
    Description:
        resets relevant the global varibales for a new game on the server
    Params:
        ()
    Returns:
        void
"""


def resetGlobalVars():
    global winningTeam, needToOffer, clientSockets, clientNames
    winningTeam = -1
    needToOffer = True
    clientSockets = []
    clientNames = []


"""
    Description:
        this function is used to redefine a signal behaviour
    Params:
        (sig,frame)
    Returns:
        void
"""


def signal_handler(sig, frame):
    print("\nServer closing peacfully...")
    closeConnections()
    serverSocket.close()  # close that server socket and free the port
    if(sig == signal.SIGTSTP):
        signal.signal(sig, def_tstp_handler)
        signal.raise_signal(sig)


"""
    Description:
        setting the global variables to initial values
    Params:
        ()
    Returns:
        void
"""


def setGlobals():
    global def_tstp_handler, SERVER_PORT, udpMsg, SERVER_IP

    # signals
    def_tstp_handler = signal.getsignal(signal.SIGTSTP)
    signal.signal(signal.SIGTSTP, signal_handler)

    # server port
    SERVER_PORT = random.randrange(5000, 7000)

    # creating udp offer message to send
    udpMsg = struct.pack('IbH', MAGIC_COOKIE, MESSAGE_TYPE,
                         SERVER_PORT)  # encoding udp message

    # set ip from user input
    print("please select network type: \n1) dev network \n2)test network")
    typeOfNet = sys.stdin.readline()
    if typeOfNet == "1":
        SERVER_IP = scapy.all.get_if_addr('eth1')
    else:
        SERVER_IP = scapy.all.get_if_addr('eth2')


def Main():

    global serverSocket

    setGlobals()  # set global variables to default values
    serverSocket = start_server()

    while serverSocket != None:  # infinite loop to keep server alive
        global needToOffer
        offer_thread = threading.Thread(target=offerStage)
        offer_thread.start()
        accept_clients(serverSocket)
        needToOffer = False
        offer_thread.join()
        sleep(10)
        playGame()
        resetGlobalVars()


if __name__ == '__main__':
    Main()
