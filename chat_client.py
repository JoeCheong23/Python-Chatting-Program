from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QLabel, QPushButton, QListWidget, QStackedWidget
from PyQt5 import uic
import sys, socket, threading


host = 'localhost'
data_payload = 2048
connectedClientsList = [] # List contaning the nickname of all clients that are connected to the server
chatroomList = {} # key is group name, value is list of group members. First group member in list is the group's creator
groupMessages = {} # key is group name, value is string containing all messages separated by new line
oneToOneMessages = {} # key is client name, value is string containing all messages separated by new line
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Consider saving time separately for messages so different layout can be used. Long string is very rigid.


# Method to establish a connection with the server and identify yourself by your nickname. Nickname should be unique.
def establish_connection(port, nickname):
    sock.connect((host, port))
    sock.sendall(nickname.encode('utf-8'))

# Format for message to be sent is [nickname, destination client/group, message, time]
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
# typeOfMessage can be Invite, Group, OnetoOne, NewGroup, NewClient, AddGroupMember
def receive_message(message, connection_ui, connected_ui):
    messageList = message.decode('utf-8').split('|||')

    if messageList[0] == "NewGroup":
        groupMemberList = messageList[2].split(',')
        chatroomList[messageList[1]] = groupMemberList
        groupMessages[messageList[1]] = ""
    elif messageList[0] == "NewClient":
        connectedClientsList.append(messageList[1])
        oneToOneMessages[messageList[2]] = ""
        connected_ui.new_client()
    elif messageList[0] == "Group":
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
    elif messageList[0] == "OnetoOne":
        oneToOneMessages[messageList[2]] = oneToOneMessages[messageList[2]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
    elif messageList[0] == "AddGroupMember":
        chatroomList[messageList[1]] = chatroomList[messageList[1]].append(messageList[2])
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + "Server ("  + messageList[4] + "): " + messageList[3] + " has connected!\n"


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
        for group in chatroomList:
            self.chatroom_list.addItem((group + " by " + chatroomList[group][0]))
        self.chatroom_list.repaint()


# Initialise the app and the various scenes. Uses a stacked widget to enable switching between scenes by replacing the current widget with the new widget when 
# necessary. 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QStackedWidget()
    connectionUI = ConnectionUI()
    connectedUI = ConnectedUI()
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