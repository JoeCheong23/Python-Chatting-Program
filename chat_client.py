from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QLabel, QPushButton, QListWidget, QStackedWidget, QTextBrowser
from PyQt5 import uic
import sys, socket, threading, datetime

ownNickname = ''
host = 'localhost'
data_payload = 2048
connectedClientsList = [] # List contaning the nickname of all clients that are connected to the server
chatroomDict = {} # key is group name, value is list of group members. First group member in list is the group's creator
groupMessages = {} # key is group name, value is string containing all messages separated by new line
oneToOneMessages = {} # key is client name, value is string containing all messages separated by new line
currentOneToOneClientPartner = ''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Consider saving time separately for messages so different layout can be used. Long string is very rigid.


# Method to establish a connection with the server and identify yourself by your nickname. Nickname should be unique.
def establish_connection(port, nickname):
    sock.connect((host, port))
    sock.sendall(nickname.encode('utf-8'))

# Format for message to be sent is [typeOfMessage, destination client/group, message, time]
# typeOfMessage can be GroupInvite, GroupJoin, OneToOneMessage, GroupMessage, Disconnect, NewGroup
def send_message(message):
    message_string = ''
    for i in message:
        message_string = message_string + i + '|||'
    try:
        sock.sendall(message_string.encode('utf-8'))
    except socket.error as e:
        print(f"Socket error: {str(e)}")
    except Exception as e:
        print(f"Other exception: {str(e)}")


# Format for message to be received is [typeOfMessage, sender client/group, sender nickname, message, time]
# typeOfMessage can be InviteToGroup, Group, OnetoOne, NewGroup, NewClient, AddGroupMember, Disconnect
def receive_message(message, connection_ui, connected_ui):
    messageList = message.decode('utf-8').split('|||')

    if messageList[0] == "NewGroup" or messageList[0] == "InviteToGroup":
        chatroomDict[messageList[1]] = messageList[2].split(',')
        groupMessages[messageList[1]] = ""
    elif messageList[0] == "NewClient":
        connectedClientsList.append(messageList[2])
        oneToOneMessages[messageList[2]] = ""
        connected_ui.new_client()
    elif messageList[0] == "Group":
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
    elif messageList[0] == "OnetoOne":
        oneToOneMessages[messageList[2]] = oneToOneMessages[messageList[2]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
    elif messageList[0] == "AddGroupMember":
        chatroomDict[messageList[1]] = chatroomDict[messageList[1]].append(messageList[2])
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + "Server ("  + messageList[4] + "): " + messageList[2] + " has connected!\n"
    elif messageList[0] == "Disconnect":
        disconnectedMember = messageList[2]
        connectedClientsList.remove(disconnectedMember)
        for roomKey in chatroomDict.keys():
            if chatroomDict[roomKey].contains(disconnectedMember):
                chatroomDict[roomKey].remove(disconnectedMember)
                groupMessages[roomKey] = groupMessages[roomKey] + "Server ("  + messageList[4] + "): " + messageList[2] + " has disconnected!\n"
        oneToOneMessages[disconnectedMember] = oneToOneMessages[disconnectedMember] + "Server ("  + messageList[4] + "): " + messageList[2] + " has disconnected!\n"
    

# Function to receive data that should be run in a separate thread to prevent blocking
def receive_data(sock, connection_ui, connected_ui):
    try:
        while True:
            data = sock.recv(data_payload)
            receive_message(data, connection_ui, connected_ui)
    except socket.error as e:
        print(f"Socket error: {str(e)}")
    except Exception as e:
        print(f"Other exception: {str(e)}")
    finally:
        print("Closing connection to the server")
        sock.close()


class ConnectionUI(QWidget):
    def __init__(self):
        super(ConnectionUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/Connection.ui", self)
         
        # Define the widgets
        self.app_name = self.findChild(QLabel, "app_name")
        self.ip_label = self.findChild(QLabel, "ip_label")
        self.port_label = self.findChild(QLabel, "port_label")
        self.nickname_label = self.findChild(QLabel, "nickname_label")
        self.ip_textfield = self.findChild(QLineEdit, "ip_textfield")
        self.port_textfield = self.findChild(QLineEdit, "port_textfield")
        self.nickname_textfield = self.findChild(QLineEdit, "nickname_textfield")
        self.connect_button = self.findChild(QPushButton, "connect_button")
        self.cancel_button = self.findChild(QPushButton, "cancel_button")

        # Initialise
        self.ip_textfield.setText("localhost")

        # Attach functions to buttons when clicked
        self.connect_button.clicked.connect(self.connect)
        self.cancel_button.clicked.connect(lambda: sys.exit())

    # Specify functions of buttons
    def connect(self):
        ownNickname=self.nickname_textfield.text()
        connection_thread = threading.Thread(target=establish_connection, args=(int(self.port_textfield.text()), self.nickname_textfield.text()))
        connection_thread.setDaemon(True)
        connection_thread.start()
        widget.removeWidget(connectionUI)
        widget.insertWidget(0, connectedUI)
        

class ConnectedUI(QMainWindow):

    def __init__(self):
        super(ConnectedUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/Connected.ui", self)

        #Define the widgets
        self.Chatroom = self.findChild(QLabel, "Chatroom")
        self.connectedclient_list = self.findChild(QListWidget, "connectedclient_list")
        self.Chatroom_label2 = self.findChild(QLabel, "Chatroom_label2")
        self.chatroom_list = self.findChild(QListWidget, "chatroom_list")
        self.onetoone_button = self.findChild(QPushButton, "onetoone_button")
        self.createroom_button = self.findChild(QPushButton, "createroom_button")
        self.joinroom_button = self.findChild(QPushButton, "joinroom_button")
        self.closeconnected_button = self.findChild(QPushButton, "closeconnected_button")

        self.connectedclient_list.addItem("Andrew")
        self.connectedclient_list.addItem("Kenari")

        # Attach functions to buttons when clicked
        self.closeconnected_button.clicked.connect(self.close_connected)
        self.createroom_button.clicked.connect(self.create_room)
        self.onetoone_button.clicked.connect(self.onetoone)
        self.connectedclient_list.itemActivated.connect(self.item_activated)


    #Specify function of buttons
    def close_connected(self):
        widget.removeWidget(connectedUI)
        widget.insertWidget(0, connectionUI)

    def create_room(self):
        connectedClientsList.append("Aeon")
        self.connectedclient_list.clear()
        self.connectedclient_list.addItems(connectedClientsList)
        self.connectedclient_list.repaint()
    
    def onetoone(self):
        print("Selected client: ", self.connectedclient_list.currentRow())

    def item_activated(self):
        print("Selected client: ", self.connectedclient_list.currentItem().text())

    def new_client(self):
        self.connectedclient_list.clear()
        self.connectedclient_list.addItems(connectedClientsList)
        self.connectedclient_list.repaint()

    def new_group(self):
        self.chatroom_list.clear()
        for group in chatroomDict:
            self.chatroom_list.addItem((group + " by " + chatroomDict[group][0]))
        self.chatroom_list.repaint()

class OneToOneUI(QMainWindow):

    def __init__(self):
        super(ConnectedUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/OneToOne.ui", self)

        #Define the widgets
        self.onetoone_chatwith_label = self.findChild(QLabel, "onetoone_chatwith_label")
        self.onetoone_textbrowser = self.findChild(QTextBrowser, "onetoone_textbrowser")
        self.onetoone_textfield = self.findChild(QLineEdit, "onetoone_textfield")
        self.onetoone_send_button = self.findChild(QPushButton, "onetoone_send_button")
        self.onetoone_close_button = self.findChild(QPushButton, "onetoone_close_button")


        # Attach functions to buttons when clicked
        self.onetoone_close_button.clicked.connect(self.close_button)
        self.onetoone_send_button.clicked.connect(self.create_room)

    def initialise(self):
        self.onetoone_chatwith_label = 'Chat with ' + currentOneToOneClientPartner
        self.onetoone_textbrowser.setText(oneToOneMessages[currentOneToOneClientPartner])

    #Specify function of buttons
    def close_button(self):
        widget.removeWidget(onetooneUI)
        widget.insertWidget(0, connectionUI)

    def send_button(self):
        current_time = datetime.datetime.now().strftime('%H:%M')
        data_to_send = [ownNickname, currentOneToOneClientPartner, self.onetoone_textfield.text(), current_time]
        send_message(data_to_send)
        oneToOneMessages[currentOneToOneClientPartner] = oneToOneMessages[currentOneToOneClientPartner] + ownNickname + " ("  + current_time + "): " + self.onetoone_textfield.text() + "\n"
        self.onetoone_textfield.setText('')
            


# Initialise the app and the various scenes. Uses a stacked widget to enable switching between scenes by replacing the current widget with the new widget when 
# necessary. 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QStackedWidget()
    connectionUI = ConnectionUI()
    connectedUI = ConnectedUI()
    onetooneUI = OneToOneUI()
    widget.addWidget(connectionUI)
    widget.setFixedHeight(610)
    widget.setFixedWidth(805)
    widget.setWindowTitle("Chatroom")
    widget.show()
    app.exec_()

    # Establish socket connection
    recv_thread = threading.Thread(target=receive_data, args=(sock, connectionUI, connectedUI))
    recv_thread.setDaemon(True)
    recv_thread.start()