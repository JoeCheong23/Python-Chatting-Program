from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QLabel, QPushButton, QListWidget, QStackedWidget, QTextBrowser
from PyQt5 import uic, QtCore
import sys, socket, threading, datetime, re, time

port = 6942
rot13 = str.maketrans(
    'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
    'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm')
ownNickname = ''
host = 'localhost'
data_payload = 2048
connectedClientsList = [] # List contaning the nickname of all clients that are connected to the server
chatroomDict = {} # key is group name, value is list of group members. First group member in list is the group's creator
groupMessages = {} # key is group name, value is string containing all messages separated by new line
oneToOneMessages = {} # key is client name, value is string containing all messages separated by new line
currentOneToOneClientPartner = ''
currentGroup = ''
sock = None


# Consider saving time separately for messages so different layout can be used. Long string is very rigid.

# Method to wait to prevent two threads trying to access the same lock.
def wait(): 
    time.sleep(0.5)


# Method to establish a connection with the server and identify yourself by your nickname. Nickname should be unique.
def establish_connection(port, nickname):
    print(nickname)
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(nickname.translate(rot13).encode('utf-8'))
    # Establish socket connection
    recv_thread = threading.Thread(target=receive_data, args=(sock,))
    recv_thread.setDaemon(True)
    recv_thread.start()

# Method that sends message to the server after encrypting and encoding it.
# Format for message to be sent is [typeOfMessage, destination client/group, message, time]
# typeOfMessage can be GroupInvite, GroupJoin, OneToOneMessage, GroupMessage, Disconnect, NewGroup
def send_message(message):
    message_string = ''
    for i in message:
        message_string = message_string + i + '|||'
    try:
        sock.sendall(message_string.translate(rot13).encode('utf-8'))
    except socket.error as e:
        print(f"Socket error: {str(e)}")
    except Exception as e:
        print(f"Other exception: {str(e)}")


# Method that decrypts, decodes, and stores the information based on the message received.
# Format for message to be received is [typeOfMessage, sender client/group, sender nickname, message, time]
# typeOfMessage can be InviteToGroup, Group, OnetoOne, NewGroup, NewClient, AddGroupMember, Disconnect
def receive_message(message):
    messageList = message.decode('utf-8').translate(rot13).split('|||')

    if messageList[0] == "NewGroup" :
        chatroomDict[messageList[1]] = messageList[2].split(',')
        groupMessages[messageList[1]] = ""
        repaint_UI("NewGroup", "")
    elif messageList[0] == "InviteToGroup":
        chatroomDict[messageList[1]] = messageList[2].split(";")
    elif messageList[0] == "ClientSetup":
        global connectedClientsList
        connectedClientsList = messageList[3].split(";")
        for x in connectedClientsList:
            oneToOneMessages[x] = ''
        repaint_UI("NewClient", "")
    elif messageList[0] == "GroupSetup":
        groupSplit = messageList[3].split(";")
        for x in groupSplit[:-1]:
            roomName = x.split("=")[0]
            roomMembers = x.split("=")[1].split(",")
            chatroomDict[roomName] = roomMembers
            groupMessages[roomName] = ''
        repaint_UI("NewGroup", "")
    elif messageList[0] == "NewClient":
        connectedClientsList.append(messageList[2])
        oneToOneMessages[messageList[2]] = ""
        repaint_UI("NewClient", "")
    elif messageList[0] == "Group":
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
        repaint_UI("GroupMessage", messageList[1])
    elif messageList[0] == "OnetoOne":
        oneToOneMessages[messageList[2]] = oneToOneMessages[messageList[2]] + messageList[2] + " ("  + messageList[4] + "): " + messageList[3] + "\n"
        repaint_UI("OnetoOne", messageList[2])
    elif messageList[0] == "AddGroupMember":
        chatroomDict[messageList[1]].append(messageList[2])
        groupMessages[messageList[1]] = groupMessages[messageList[1]] + "Server ("  + messageList[4] + "): " + messageList[2] + " has connected!\n"
        repaint_UI("AddGroupMember", messageList[1])
    elif messageList[0] == "Disconnect":
        disconnectedMember = messageList[2]
        connectedClientsList.remove(disconnectedMember)
        for roomKey in chatroomDict.keys():
            if disconnectedMember in chatroomDict[roomKey]:
                chatroomDict[roomKey].remove(disconnectedMember)
                groupMessages[roomKey] = groupMessages[roomKey] + "Server ("  + messageList[4] + "): " + messageList[2] + " has disconnected!\n"
        oneToOneMessages[disconnectedMember] = oneToOneMessages[disconnectedMember] + "Server ("  + messageList[4] + "): " + messageList[2] + " has disconnected!\n"
        repaint_UI("NewClient", "")
        if currentOneToOneClientPartner == disconnectedMember:
            repaint_UI("OnetoOne", disconnectedMember)
        if currentGroup != '':
            repaint_UI("AddGroupMember", currentGroup)
    

# Function to receive data that should be run in a separate thread to prevent blocking
def receive_data(sock, ):
    try:
        while True:
            data = sock.recv(data_payload)
            receive_message(data)
    except socket.error as e:
        print(f"Socket error: {str(e)}")
    except Exception as e:
        print(f"Other exception: {str(e)}")
    finally:
        print("Closing connection to the server")
        sock.close()


# Method to refresh UI based on the specific view that has been updated.
def repaint_UI(repaint_option, chat_target):
 
    if repaint_option == "NewClient":
        connectedUI.connected_refresh_button.click()
    elif repaint_option == "NewGroup":
        connectedUI.connected_refresh_group_button.click()
    elif repaint_option == "GroupMessage":
        if (chat_target == currentGroup):
            groupChatUI.groupchat_refresh_message.click()
    elif repaint_option == "AddGroupMember":
        if (chat_target == currentGroup):
            groupChatUI.groupchat_refresh_members.click()
            groupChatUI.groupchat_refresh_message.click()
    elif repaint_option == "OnetoOne":
        if (chat_target == currentOneToOneClientPartner):
            onetooneUI.onetoone_refresh_button.click()
    

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
        global ownNickname
        ownNickname=self.nickname_textfield.text()
        port = int(self.port_textfield.text())
        connection_thread = threading.Thread(target=establish_connection, args=(port, self.nickname_textfield.text()))
        connection_thread.setDaemon(True)
        connection_thread.start()
        widget.removeWidget(connectionUI)
        widget.insertWidget(0, connectedUI)
        wait()
        connectedUI.initialise()

        

class ConnectedUI(QMainWindow):

    def __init__(self):
        super(ConnectedUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/Connected.ui", self)

        #Define the widgets
        self.Chatroom = self.findChild(QLabel, "Chatroom")
        self.connectedclient_list = self.findChild(QListWidget, "connectedclient_list")
        self.Chatroom_label2 = self.findChild(QLabel, "Chatroom_label2")
        self.welcome_label = self.findChild(QLabel, "welcome_label")
        self.chatroom_list = self.findChild(QListWidget, "chatroom_list")
        self.onetoone_button = self.findChild(QPushButton, "onetoone_button")
        self.createroom_button = self.findChild(QPushButton, "createroom_button")
        self.joinroom_button = self.findChild(QPushButton, "joinroom_button")
        self.closeconnected_button = self.findChild(QPushButton, "closeconnected_button")
        self.connected_refresh_button = self.findChild(QPushButton, "connected_refresh_button")
        self.connected_refresh_group_button = self.findChild(QPushButton, "connected_refresh_group_button")


        # Attach functions to buttons when clicked
        self.closeconnected_button.clicked.connect(self.close_connected)
        self.createroom_button.clicked.connect(self.create_room)
        self.onetoone_button.clicked.connect(self.onetoone)
        self.joinroom_button.clicked.connect(self.join_room)
        self.connected_refresh_button.clicked.connect(self.new_client)
        self.connected_refresh_group_button.clicked.connect(self.new_group)

    def initialise(self):
        self.welcome_label.setText("Welcome " + ownNickname + "!")

    #Specify function of buttons
    def close_connected(self):
        data_to_send = ["Disconnect", " ", " ", datetime.datetime.now().strftime('%H:%M')]
        sock.close()
        widget.removeWidget(connectedUI)
        widget.insertWidget(0, connectionUI)

    def create_room(self):
        global chatroomDict
        groupCount = str(len(chatroomDict))
        groupName = "Group" + groupCount + " by " + ownNickname
        chatroomDict[groupName] = []
        chatroomDict[groupName].append(ownNickname)
        groupMessages[groupName] = ''
        data_to_send = ["NewGroup", groupName, " ", datetime.datetime.now().strftime('%H:%M')]
        send_message(data_to_send)
        self.new_group()
    
    def onetoone(self):
        if self.connectedclient_list.currentRow() != -1:
            global currentOneToOneClientPartner
            currentOneToOneClientPartner = self.connectedclient_list.currentItem().text()
            widget.removeWidget(connectedUI)
            widget.insertWidget(0, onetooneUI)
            wait()
            onetooneUI.initialise()

    def join_room(self):
        if self.chatroom_list.currentRow() != -1:
            global currentGroup
            currentGroup = self.chatroom_list.currentItem().text()
            if ownNickname not in chatroomDict[currentGroup]:
                chatroomDict[currentGroup].append(ownNickname)
                data_to_send = ["GroupJoin", currentGroup, " ", datetime.datetime.now().strftime('%H:%M')]
                send_message(data_to_send)
            widget.removeWidget(connectedUI)
            widget.insertWidget(0, groupChatUI)
            wait()
            groupChatUI.initialise()

    def new_client(self):
        self.connectedclient_list.clear()
        self.connectedclient_list.addItems(connectedClientsList)
        self.connectedclient_list.repaint()

    def new_group(self):
        self.chatroom_list.clear()
        self.chatroom_list.addItems(list(chatroomDict.keys()))
        self.chatroom_list.repaint()

class OneToOneUI(QMainWindow):

    def __init__(self):
        super(OneToOneUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/OneToOne.ui", self)

        #Define the widgets
        self.onetoone_chatwith_label = self.findChild(QLabel, "onetoone_chatwith_label")
        self.onetoone_textbrowser = self.findChild(QTextBrowser, "onetoone_textbrowser")
        self.onetoone_textfield = self.findChild(QLineEdit, "onetoone_textfield")
        self.onetoone_send_button = self.findChild(QPushButton, "onetoone_send_button")
        self.onetoone_close_button = self.findChild(QPushButton, "onetoone_close_button")
        self.onetoone_refresh_button = self.findChild(QPushButton, "onetoone_refresh_button")

        # Attach functions to buttons when clicked
        self.onetoone_close_button.clicked.connect(self.close_button)
        self.onetoone_refresh_button.clicked.connect(self.new_message)
        self.onetoone_send_button.clicked.connect(self.send_button)
        

    def initialise(self):
        self.onetoone_chatwith_label.setText('Chat with ' + currentOneToOneClientPartner)
        self.onetoone_textbrowser.setText(oneToOneMessages[currentOneToOneClientPartner])

    #Specify function of buttons
    def close_button(self):
        widget.removeWidget(onetooneUI)
        widget.insertWidget(0, connectedUI)

    def send_button(self):
        if self.onetoone_textfield.text() != "" or re.search("^\s*$", self.onetoone_textfield.text()) == False:
            current_time = datetime.datetime.now().strftime('%H:%M')
            data_to_send = ["OneToOneMessage", currentOneToOneClientPartner, self.onetoone_textfield.text(), current_time]
            send_message(data_to_send)
            oneToOneMessages[currentOneToOneClientPartner] = oneToOneMessages[currentOneToOneClientPartner] + ownNickname + " ("  + current_time + "): " + self.onetoone_textfield.text() + "\n"
            self.onetoone_textbrowser.setText(oneToOneMessages[currentOneToOneClientPartner])
        self.onetoone_textfield.setText('')

    def new_message(self):
        self.onetoone_textbrowser.setText(oneToOneMessages[currentOneToOneClientPartner])
            
class GroupChatUI(QMainWindow):

    def __init__(self):
        super(GroupChatUI, self).__init__()

        # Load the Connection.ui file
        uic.loadUi("./Windows/GroupChat.ui", self)

        #Define the widgets
        self.groupchat_label = self.findChild(QLabel, "groupchat_label")
        self.groupchat_textbrowser = self.findChild(QTextBrowser, "groupchat_textbrowser")
        self.groupchat_members_list = self.findChild(QListWidget, "groupchat_members_list")
        self.groupchat_textfield = self.findChild(QLineEdit, "groupchat_textfield")
        self.groupchat_send_button = self.findChild(QPushButton, "groupchat_send_button")
        self.groupchat_invite_button = self.findChild(QPushButton, "groupchat_invite_button")
        self.groupchat_close_button = self.findChild(QPushButton, "groupchat_close_button")
        self.groupchat_refresh_message = self.findChild(QPushButton, "groupchat_refresh_message")
        self.groupchat_refresh_members = self.findChild(QPushButton, "groupchat_refresh_members")

        # Attach functions to buttons when clicked
        self.groupchat_close_button.clicked.connect(self.close_button)
        self.groupchat_send_button.clicked.connect(self.send_button)
        self.groupchat_invite_button.clicked.connect(self.invite_button)
        self.groupchat_refresh_message.clicked.connect(self.new_messages)
        self.groupchat_refresh_members.clicked.connect(self.new_members)


    def initialise(self):
        self.groupchat_label.setText(currentGroup)
        self.groupchat_textbrowser.setText(groupMessages[currentGroup])
        self.groupchat_members_list.clear()
        self.groupchat_members_list.addItems(chatroomDict[currentGroup])
        self.groupchat_members_list.repaint()

    #Specify function of buttons
    def close_button(self):
        widget.removeWidget(groupChatUI)
        widget.insertWidget(0, connectedUI)

    def send_button(self):
        if self.groupchat_textfield.text() != "" or re.search("^\s*$", self.groupchat_textfield.text()) == False:
            current_time = datetime.datetime.now().strftime('%H:%M')
            data_to_send = ["GroupMessage", currentGroup, self.groupchat_textfield.text(), current_time]
            send_message(data_to_send)
            groupMessages[currentGroup] = groupMessages[currentGroup] + ownNickname + " ("  + current_time + "): " + self.groupchat_textfield.text() + "\n"
            self.groupchat_textbrowser.setText(groupMessages[currentGroup])
        self.groupchat_textfield.setText('')

    def invite_button(self):
        widget.removeWidget(groupChatUI)
        widget.insertWidget(0, inviteUI)
        inviteUI.initialise()

    def new_messages(self):
        global groupMessages
        self.groupchat_textbrowser.setText(groupMessages[currentGroup])
    
    def new_members(self):
        global chatroomDict
        self.groupchat_members_list.clear()
        self.groupchat_members_list.addItems(chatroomDict[currentGroup])
        self.groupchat_members_list.repaint()


class InviteUI(QMainWindow):

    def __init__(self):
        super(InviteUI, self).__init__()
        # Load the Connection.ui file
        uic.loadUi("./Windows/Invite.ui", self)

        #Define the widgets
        self.invite_list = self.findChild(QListWidget, "invite_list")
        self.invite_invite_button = self.findChild(QPushButton, "invite_invite_button")
        self.invite_cancel_button = self.findChild(QPushButton, "invite_cancel_button")


        # Attach functions to buttons when clicked
        self.invite_cancel_button.clicked.connect(self.cancel_button)
        self.invite_invite_button.clicked.connect(self.invite_button)

    def initialise(self):
        members = [x for x in connectedClientsList if x not in chatroomDict[currentGroup]]
        self.invite_list.clear()
        self.invite_list.addItems(members)
        self.invite_list.repaint()

    #Specify function of buttons
    def cancel_button(self):
        widget.removeWidget(inviteUI)
        widget.insertWidget(0, groupChatUI)
        groupChatUI.initialise()

    def invite_button(self):
        if self.invite_list.currentRow() != -1:
            current_time = datetime.datetime.now().strftime('%H:%M')
            data_to_send = ["GroupInvite", currentGroup, self.invite_list.currentItem().text(), current_time]
            send_message(data_to_send)
            chatroomDict[currentGroup].append(self.invite_list.currentItem().text())
            groupMessages[currentGroup] = groupMessages[currentGroup] + "Server ("  + current_time + "): " + self.invite_list.currentItem().text() + " has connected!\n"
            self.initialise()

# Initialise the app and the various scenes. Uses a stacked widget to enable switching between scenes by replacing the current widget with the new widget when 
# necessary. 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = QStackedWidget()
    connectionUI = ConnectionUI()
    connectedUI = ConnectedUI()
    onetooneUI = OneToOneUI()
    groupChatUI = GroupChatUI()
    inviteUI = InviteUI()
    widget.addWidget(connectionUI)
    widget.setFixedHeight(610)
    widget.setFixedWidth(805)
    widget.setWindowTitle("Chatroom")
    widget.show()
    app.exec_()

    