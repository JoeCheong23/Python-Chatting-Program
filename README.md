# Python-Chatting-Program

Chatting program between clients and server over sockets on localhost, implemented in Python. GUI utilises the PyQt5 library. This was done as part of an assignment.

The functionality involves communicating with clients in a one-to-one chat, viewing a list of available clients to chat with, and a list of groups to join. The client can also create their own group and invite other members into their group chat. Clients in a group chat can send a message that would be received by all members of the chat. The clients will be notified if a member of their group chat disconnects or if a new member joins. 

To run the server, enter ```python chat_server.py --port=<port_number>```
To run a client instance, enter ```python chat_client.py```

If you have more than one version of python installed, you may need to run the server by entering ```python3 chat_server.py --port=<port_number>``` and run the client instances by entering ```python3 chat_client.py``` instead. 

The batchfile was included for testing purposes and can be run by entering ```./chat.bat``` into the command prompt. The batch file will run the server and create three instances of clients.
