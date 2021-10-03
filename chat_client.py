from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QLabel, QPushButton, QListWidget, QStackedWidget
from PyQt5 import uic
import sys

connectedClientsList = ["Alice", "Kenari"]

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

        # Attach functions to buttons when clicked
        self.connect_button.clicked.connect(self.connect)
        self.cancel_button.clicked.connect(lambda: sys.exit())

    # Specify functions of buttons
    def connect(self):
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
        self.closeconnected_button.clicked.connect(self.closeconnected)
        self.createroom_button.clicked.connect(self.createroom)
        self.onetoone_button.clicked.connect(self.onetoone)
        self.connectedclient_list.itemActivated.connect(self.itemactivated)


    #Specify function of buttons
    def closeconnected(self):
        widget.removeWidget(connectedUI)
        widget.insertWidget(0, connectionUI)

    def createroom(self):
        connectedClientsList.append("Aeon")
        self.connectedclient_list.clear()
        self.connectedclient_list.addItems(connectedClientsList)
        self.connectedclient_list.repaint()
    
    def onetoone(self):
        print("Selected client: ", self.connectedclient_list.currentRow())

    def itemactivated(self):
        print("Selected client: ", self.connectedclient_list.currentItem().text())

# Initialise the app and the various scenes. Uses a stacked widget to enable switching between scenes by replacing the current widget with the new widget when 
# necessary. 
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