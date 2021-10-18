import socket, argparse, threading, datetime

host = 'localhost'
data_payload = 2048
backlog = 1
clientDict = {} # key is client nickname, value is socket reference of the client
roomDict = {} # key is room name, value is array of client nicknames
rot13 = str.maketrans(
    'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
    'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm')


# TODO: sort out client dictionary that maps client nickname to client object
# TODO: store in dictionary the room names and the nicknames of clients involved in each room


def chat_server(port):
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_STREAM)
    # Enable reuse address/port
    sock.setsockopt(socket.SOL_SOCKET,
                    socket.SO_REUSEADDR, 1)
    
    # Bind the socket to the port
    print(f"Starting up chat server on {host} port {port}")
    sock.bind((host, port))
    
    # Listen to clients, backlog argument specifies the max no.of queued connections
    sock.listen(backlog)

    print("Waiting for a client")
    while True:
        print("accepting clients")
        client, address = sock.accept()
        newclient_thread = threading.Thread(target=new_clients, args=(sock, client))
        newclient_thread.setDaemon(True)
        newclient_thread.start()
        setupclient_thread = threading.Thread(target=setup_client, args=(client, ))
        setupclient_thread.setDaemon(True)
        setupclient_thread.start()


# Method that sends necessary information to the client in order to set them up. This includes
# notifying the user of the current list of clients available to communicate with and the group chats
# available to join, and their current group members.
def setup_client(client):
    if len(clientDict) > 0:
        data = ["ClientSetup", " ", " ", ";".join([str(element) for element in list(clientDict.keys())]), datetime.datetime.now().strftime('%H:%M')]
        client.sendall(data_to_serial(data).encode('utf-8'))
        if len(roomDict) > 0:
            roomString = ''
            for key in roomDict.keys():
                roomString = roomString + str(key) + "="
                roomString = roomString + ",".join([str(element) for element in roomDict[key]])
                roomString = roomString + ";"
            data = ["GroupSetup", " ", " ", roomString, datetime.datetime.now().strftime('%H:%M')]
            client.sendall(data_to_serial(data).encode('utf-8'))


# Method that stores information about a new client and calls methods to notify the rest of the clients 
# that a new client is available to communicate with
def new_clients(sock, client):
    uname = client.recv(data_payload).decode().translate(rot13)
    if uname:
        print(uname + " joined. Current clients are " + ','.join([str(element) for element in list(clientDict.keys())]))
        clientDict[uname] = client
        notify_thread = threading.Thread(target=notify_all, args=(uname, None, "NewClient", None))
        notify_thread.setDaemon(True)
        notify_thread.start()
        recv_thread = threading.Thread(target=receive_data, args=(sock, client, uname))
        recv_thread.setDaemon(True)
        recv_thread.start()


# Method that receives information from the client, performs decoding and decryption before calling 
# methods to deal with the message and its contents.
def receive_data(sock, client, uname):
    while True:
        data = ''
        try:
            data = client.recv(data_payload)
        except socket.error as e:
            print(f"Socket error: {str(e)}")
            client.close()
            message = ["Disconnect", " ", " ", " "] 
            disconnect_thread = threading.Thread(target=message_actions, args=(uname, message))
            disconnect_thread.setDaemon(True)
            disconnect_thread.start()
            break
        if data:
            messageList = data.decode().translate(rot13).split('|||')
            if messageList:
                message_thread = threading.Thread(target=message_actions, args=(uname, messageList))
                message_thread.setDaemon(True)
                message_thread.start() 
          

# Method that perfroms actions depending on the type of message received. Calls the notify_all method to 
# notify all relevant clients of changes.
def message_actions(uname, messageList):
    if messageList[0] == "GroupInvite":
        if messageList[2] in clientDict and messageList[1] in roomDict:
            roomDict[messageList[1]].append(messageList[2])
            notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupInvite", messageList[2]))    
            notify_thread.setDaemon(True)
            notify_thread.start()
    elif messageList[0] == "GroupJoin":
        roomDict[messageList[1]].append(uname)
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupJoin", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()   
    elif messageList[0] == "OneToOneMessage":
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "OneToOneMessage", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
    elif messageList[0] == "GroupMessage":
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupMessage", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
    elif messageList[0] == "Disconnect":
        clientDict[uname].close()
        clientDict.pop(uname, None)
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "Disconnect", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
        for key in roomDict.keys():
            if uname in roomDict[key]:
                roomDict[key].remove(uname)
    elif messageList[0] == "NewGroup":
        roomDict[messageList[1]] = [uname]
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "NewGroup", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()


# Method that notifies all relevant clients about updates based on the message arguments.
def notify_all(uname, recipient, messageType, message):

    # GroupInvite
    # Send AddGroupMember to everyone (except sender and new group member) to notify them that there is a new group member
    # Send InviteToGroup to the new member 
    # GroupJoin
    # Send AddGroupMember to everyone (except sender) to notify them that there is a new group member
    # OneToOneMessage
    # Send OnetoOne to the receiver
    if messageType == "GroupInvite":
        data = ["AddGroupMember", recipient, message, " ", datetime.datetime.now().strftime('%H:%M')]
        for member in roomDict[recipient]:
            if member != uname and member != message:
                clientDict[member].sendall(data_to_serial(data).encode('utf-8'))
            elif member == message:
                data = ["InviteToGroup", recipient, ";".join(str(element) for element in roomDict[recipient]), " ", datetime.datetime.now().strftime('%H:%M')]
                clientDict[member].sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "GroupJoin":
        data = ["AddGroupMember", recipient, uname, ",", datetime.datetime.now().strftime('%H:%M')]
        for member in roomDict[recipient]:
            if member != uname:
                clientDict[member].sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "OneToOneMessage" and recipient in clientDict:
        data = ["OnetoOne", " ", uname, message, datetime.datetime.now().strftime('%H:%M')]
        clientDict[recipient].sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "GroupMessage" and recipient in roomDict:
        data = ["Group", recipient, uname, message, datetime.datetime.now().strftime('%H:%M')]
        for member in roomDict[recipient]:
            if member != uname:
                clientDict[member].sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "Disconnect":
        data = ["Disconnect", " ", uname, message, datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.values():
            client.sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "NewGroup":
        data = ["NewGroup", recipient, uname, message, datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.values():
            if client != clientDict[uname]:
                client.sendall(data_to_serial(data).encode('utf-8'))
    elif messageType == "NewClient":
        data = ["NewClient", " ", uname, " ", datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.keys():
            if client != uname:
                clientDict[client].sendall(data_to_serial(data).encode('utf-8'))


# Converts data from an array of string to a string, and performs encryption with ROT13
def data_to_serial(data):
    serial = ''
    for string in data:
        serial = serial + string + '|||'
    return serial.translate(rot13)


# Main function
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Socket Server Example')
    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    chat_server(port)