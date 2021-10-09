import socket, sys, argparse, threading, datetime

host = 'localhost'
data_payload = 2048
backlog = 1
clientDict = {} # key is client nickname, value is socket reference of the client
roomDict = {} # key is room name, value is array of client nicknames


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
    newclient_thread = threading.Thread(target=new_clients, args=(sock, clientDict))
    newclient_thread.setDaemon(True)
    newclient_thread.start()
    send_data(sock, clientDict)


def new_clients(sock, clientset):
    while True:
        client, address = sock.accept()
        uname = client.recv(data_payload).decode()
        if uname:
            clientDict[uname] = client
            recv_thread = threading.Thread(target=notify_all, args=(uname, None, "NewClient", None))
            recv_thread.setDaemon(True)
            recv_thread.start()


def receive_data(sock, client, uname):
    while True:
        data = client.recv(data_payload)
        if data:
            messageList = data.decode().split('|||')
            if messageList:
                message_thread = threading.Thread(target=message_actions, args=(uname, messageList))
                message_thread.setDaemon(True)
                message_thread.start() 

            
            
            # sending_thread = threading.Thread(target=receive_data, args=)


            for c in clientDict: 
                if c != client:
                    c.sendall((f"{uname}> {data.decode()}").encode('utf-8'))


def send_data(sock, clientset):
    while True:
        message = input("Server > ")
        message = f"Server> {message}"
        for c in clientset:
            c.sendall(message.encode('utf-8'))
             

def message_actions(uname, messageList):
    if messageList[0] == "GroupInvite":
        if messageList[2] in clientDict and messageList[1] in roomDict:
            roomDict[messageList[1]] = roomDict[messageList[1]].append(messageList[2])
            notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupInvite", messageList[2]))    
            notify_thread.setDaemon(True)
            notify_thread.start()
    elif messageList[0] == "GroupJoin":
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupJoin", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
        roomDict[messageList[1]].append(uname)
    elif messageList[0] == "OneToOneMessage":
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "OneToOneMessage", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
    elif messageList[0] == "GroupMessage":
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "GroupMessage", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
    elif messageList[0] == "Disconnect":
        clientDict.pop(uname, None)
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "Disconnect", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()
        for key in roomDict.keys():
            if roomDict[key].contains(uname):
                roomDict[key].remove(uname)
    elif messageList[0] == "NewGroup":
        roomDict[messageList[1]] = [uname]
        notify_thread = threading.Thread(target=notify_all, args=(uname, messageList[1], "NewGroup", messageList[2]))    
        notify_thread.setDaemon(True)
        notify_thread.start()



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
                clientDict[member].sendAll(data.encode('utf-8'))
            elif member == message:
                data = ["InviteToGroup", recipient, message, " ", datetime.datetime.now().strftime('%H:%M')]
                clientDict[member].sendAll(data.encode('utf-8'))
    elif messageType == "GroupJoin":
        data = ["AddGroupMember", recipient, uname, " ", datetime.datetime.now().strftime('%H:%M')]
        for member in roomDict[recipient]:
            if member != uname:
                clientDict[member].sendAll(data.encode('utf-8'))
    elif messageType == "OneToOneMessage" and recipient in clientDict:
        data = ["OnetoOne", " ", uname, message, datetime.datetime.now().strftime('%H:%M')]
        clientDict[recipient].sendall(data.encode('utf-8'))
    elif messageType == "GroupMessage" and recipient in roomDict:
        data = ["Group", recipient, uname, message, datetime.datetime.now().strftime('%H:%M')]
        for member in roomDict[recipient]:
            if member != uname:
                clientDict[member].sendAll(data.encode('utf-8'))
    elif messageType == "Disconnect":
        data = ["Disconnect", " ", uname, message, datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.values():
            client.sendAll(data.encode('utf-8'))
    elif messageType == "NewGroup":
        data = ["NewGroup", recipient, uname, message, datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.values():
            if client != uname:
                client.sendAll(data.encode('utf-8'))
    elif messageType == "NewClient":
        data = ["NewClient", " ", uname, " ", datetime.datetime.now().strftime('%H:%M')]
        for client in clientDict.values():
            if client != uname:
                client.sendAll(data.encode('utf-8'))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Socket Server Example')
    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    chat_server(port)