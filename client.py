import getpass
import socket
import hashlib
import os

HOST = '10.10.10.3'
PORT = 65000
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.connect((HOST,PORT))

print("Enter the type of Operation:\n 1. Create an account \n 2.Upload a file \n3. Download a file\n 4.Synchronize\n")
operation=raw_input()
if(int(operation)==1):
	serverSocket.send("Create account")
	username = raw_input('Enter your username\n')
	serverSocket.send(username)
	recvMessage = serverSocket.recv(1024).decode('utf-8')
	while (recvMessage == "Username already taken"):
		print("Username already taken \n Enter a different username")
		username = raw_input()
		serverSocket.send(username.encode('utf-8'))
		recvMessage = serverSocket.recv(1024).decode('utf-8')
	password = getpass.getpass('Password:')
	hashPwd = hashlib.md5(password)
	serverSocket.send(hashPwd.hexdigest())
	#recvMessage = serverSocket.recv(1024).decode('utf-8')
	#print(recvMessage)                  
	homePath = os.getenv("HOME")
	os.makedirs(homePath+'/OwnCloud/')          
	os.spawnl(os.P_NOWAIT,os.system("screen -dSm inotify ./sync_remote.sh '%s' &" % username))
	serverSocket.close()

elif(int(operation)==2):
	serverSocket.send("Upload file")
	username=raw_input('Enter your username\n')
	serverSocket.send(username)
	message = serverSocket.recv(1024)
	while(message == "Please check the username"):
		username=raw_input("Wrong Username. Enter the correct username\n")
		serverSocket.send(username)
		message = serverSocket.recv(1024)
	password = getpass.getpass('Password:')
	hashPwd = hashlib.md5(password)
	serverSocket.send(hashPwd.hexdigest())
	message = serverSocket.recv(1024)
	while(message == "Authentication Unsuccessful"):
		password = getpass.getpass('Enter the correct password:')
		serverSocket.send(password)
		message = serverSocket.recv(1024)
	
	filePath = raw_input('Enter the filepath:')
	fileName = filePath.split('/')[-1]
	f=open(filePath,'r')
	serverSocket.send(fileName)
	serverSocket.recv(1024)    #Send File from server
	fileSize = os.stat(filePath).st_size
	pos = 0
	while(fileSize>0):
		f.seek(pos)
		buff = f.read(1024)
		#print(buff)
		if(buff!=''):
			serverSocket.send(buff)
			fileSize = fileSize-1024
			pos+=1024
	f.close()
	serverSocket.close()

elif(int(operation)==3):
	serverSocket.send("Download File")
	username = raw_input("Enter the username\n")
	serverSocket.send(username)
	message = serverSocket.recv(1024)
	while(message == "Please check the username"):
		username = raw_input("Enter the correct username")
		serverSocket.send(username)
		message = serverSocket.recv(1024)
	password = getpass.getpass("Password:")
	hashPwd = hashlib.md5(password)
	serverSocket.send(hashPwd.hexdigest())
	message = serverSocket.recv(1024)
	while(message == "Authentication Unsuccessful"):
		password = getpass.getpass('Enter the correct password:')
		hashPwd = hashlib.md5(password)
		serverSocket.send(hashPwd.hexdigest())
		message = serverSocket.recv(1024)
	fileName = raw_input("Enter the file name")
	serverSocket.send(fileName)
	f = open(fileName,'w+')
	buff = serverSocket.recv(1024)
	f.write(buff)
	while(buff!=''):
		buff = serverSocket.recv(1024)
		f.write(buff)
	f.close()
	serverSocket.close()

elif(int(operation)==4):
	serverSocket.send("Synchronize")
	username=raw_input('Enter your username\n')
	serverSocket.send(username)
	message = serverSocket.recv(1024)
	while(message == "Please check the username"):
		username=raw_input("Wrong Username. Enter the correct username\n")
		serverSocket.send(username)
		message = serverSocket.recv(1024)
	password = getpass.getpass('Password:')
	hashPwd = hashlib.md5(password)
	serverSocket.send(hashPwd.hexdigest())
	message = serverSocket.recv(1024)
	while(message == "Authentication Unsuccessful"):
		password = getpass.getpass('Enter the correct password:')
		serverSocket.send(password)
		message = serverSocket.recv(1024)

	serverSocket.close()
