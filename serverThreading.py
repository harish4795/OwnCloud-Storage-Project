import getpass
import socket
import hashlib
import MySQLdb
from boto3.session import Session
import boto3
import os
from threading import Thread
from time import sleep
import commands
import threading

ACCESS_KEY = '*****************'
SECRET_KEY = '*****************'
session = Session(aws_access_key_id = ACCESS_KEY, aws_secret_access_key = SECRET_KEY)
db = MySQLdb.connect(host='localhost', user='root', passwd='*****')
cur = db.cursor()
cur.execute("CREATE DATABASE IF NOT EXISTS user_details")
db.commit()
db.close()
db = MySQLdb.connect(host='localhost', user='root', passwd='*****', db='user_details')
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS Credentials(Username VARCHAR(20) PRIMARY KEY, Password VARCHAR(255) NOT NULL)")
os.makedirs(os.getenv("HOME")+'/Deletelog/')
HOST = '0.0.0.0'
PORT = 65000
BUFFER = 1024
homePath = os.getenv("HOME")+"/"


def watchDir():
	while True:
		print("In watch thread:")
		numRows = cur.execute("SELECT Username FROM Credentials")
		rows = cur.fetchall()
		for row in rows:
			username = ''.join(row)
			status,numberOfFiles = commands.getstatusoutput("ls ~/" + username +" -1 | wc -l")
			#print("Number of files: ",numberOfFiles)
			if(int(numberOfFiles) > 0):
				s3 = boto3.resource('s3')
				fileList = []
				status,output = commands.getstatusoutput("ls ~/"+username)
				fileList = output.split('\n')
				for files in fileList:
					if("_aws_sync" in files):
						continue
					else:
						s3.Bucket(username).upload_file((homePath+username+"/"+files),files)
						#print("Uploaded the file ",files)
						os.system("rm "+homePath+username+"/"+files)
						#print("Deleted the file from server",files)
			if(os.path.isfile((homePath+"Deletelog/"+username+"_delete.txt"))):
				i=0
				while True:
					try:
						with open(homePath+"Deletelog/"+username+"_delete.txt") as fd:
							fileContents = fd.readlines()[i]
							fileName = fileContents.strip().split(' ')[1]
							s3.Object(username,fileName).delete()
							#print("Deleted the file from AWS ",fileName)
							i+=1
					except:
						break
				os.system("rm "+homePath+"Deletelog/"+username+"_delete.txt")
		sleep(60)

class clientThread(threading.Thread):
	def __init__(self,socket,clientIP):
		threading.Thread.__init__(self)
		self.clientSocket = socket
		self.ip = clientIP[0]
		self.socket = clientIP[1]

	def run(self):
		#print(self.ip)
		operationType = self.clientSocket.recv(BUFFER)
		if(operationType == "Create account"):
			flag = 0
			count=0
			while(flag == 0):
				username = self.clientSocket.recv(BUFFER)
				numRows = cur.execute("SELECT Username FROM Credentials")
				rows = cur.fetchall()
				for row in rows:
					if(''.join(row) == username):
						print("Username already taken, requesting for a different username")
						self.clientSocket.send("Username already taken")
						break
					else:
						count+=1
				if(count == numRows):
					try:
						s3 = boto3.resource('s3')
						s3.create_bucket(Bucket=username)
						flag=1
						self.clientSocket.send("Username available")
					except Exception as ex:
						print("Username already taken, requesting for a different username")
						self.clientSocket.send("Username already taken")
				count=0
			flag=0
			password = self.clientSocket.recv(BUFFER)
			cur.execute("INSERT INTO Credentials(Username, Password) VALUES (%s, %s)",(username,password))
			db.commit()
			os.makedirs(homePath+username+"/")
			self.clientSocket.close()
		
		elif(operationType == "Upload file"):
			flag=0
			while(flag!=1):
				username = self.clientSocket.recv(BUFFER)
				statement = "SELECT Password FROM Credentials WHERE Username='%s'" % username
				numRows = cur.execute(statement)
				if(numRows == 0):
					self.clientSocket.send("Please check the username")
				else:
					flag=1
					self.clientSocket.send("Correct username")
			password = self.clientSocket.recv(BUFFER)
			rows = cur.fetchall()
			flag=0
			while(flag!=1):
				for row in rows:
					if(''.join(row) == password):
						self.clientSocket.send("Authentication Successful")
						flag=1
					else:
						self.clientSocket.send("Authentication Unsuccessful")
						password = clientSocket.recv(BUFFER)
			
			fileName = self.clientSocket.recv(BUFFER)
			#print("File to be uploaded %s" % fileName)
			self.clientSocket.send("Send file")
			f = open(homePath+username+"/"+fileName,'wb+')
			buff = self.clientSocket.recv(BUFFER)
			f.write(buff)
			while(buff!=''):
				buff = self.clientSocket.recv(BUFFER)
				f.write(buff)
			f.close()
			s3 = boto3.resource('s3')
			s3.Bucket(username).upload_file(homePath+username+"/"+fileName,fileName)
			self.clientSocket.close()

		elif(operationType == "Download File"):
			flag=0
			while(flag!=1):
				username = self.clientSocket.recv(BUFFER)
				statement = "SELECT Password FROM Credentials WHERE Username='%s'" % username
				numRows = cur.execute(statement)
				if(numRows == 0):
					self.clientSocket.send("Please check the username")
				else:
					flag=1
					self.clientSocket.send("Correct username")
			password = self.clientSocket.recv(BUFFER)
			rows = cur.fetchall()
			flag=0
			while(flag!=1):
				for row in rows:
					if(''.join(row) == password):
						self.clientSocket.send("Authentication Successful")
						flag=1
					else:
						self.clientSocket.send("Authentication Unsuccessful")
						password = self.clientSocket.recv(BUFFER)

			fileName = self.clientSocket.recv(BUFFER)
			s3 = boto3.resource('s3')
			s3.Bucket(username).download_file(fileName,homePath+username+"/"+fileName)
			f = open(homePath+username+"/"+fileName,'rb')
			fileSize = os.stat(homePath+username+"/"+fileName).st_size
			pos=0
			while(fileSize>0):
				f.seek(pos)
				buff=f.read(BUFFER)
				if(buff!=''):
					self.clientSocket.send(buff)
					fileSize = fileSize - BUFFER
					pos+=BUFFER
			f.close()
			os.system("rm "+homePath+username+"/"+fileName)
			self.clientSocket.close()

		elif(operationType == "Synchronize"):
			flag=0
			while(flag!=1):
				username = self.clientSocket.recv(BUFFER)
				statement = "SELECT Password FROM Credentials WHERE Username='%s'" % username
				numRows = cur.execute(statement)
				if(numRows == 0):
					self.clientSocket.send("Please check the username")
				else:
					flag=1
					self.clientSocket.send("Correct username")
			password = self.clientSocket.recv(BUFFER)
			rows = cur.fetchall()
			flag=0
			while(flag!=1):
				for row in rows:
					if(''.join(row) == password):
						self.clientSocket.send("Authentication Successful")
						flag=1
					else:
						self.clientSocket.send("Authentication Unsuccessful")
						password = clientSocket.recv(BUFFER)
			s3 = boto3.resource('s3')
			bucketName = s3.Bucket(username)
			for files in bucketName.objects.all():
				s3.Bucket(username).download_file(files.key,homePath+username+"/"+files.key+"_aws_sync")
			#	print("Sleeping to check if file is present in the user directory")
			#	sleep(60)
				os.system("scp "+homePath+username+"/"+files.key+"_aws_sync root@"+self.ip+":~/OwnCloud/"+files.key)
				os.system("rm "+homePath+username+"/"+files.key+"_aws_sync")
			self.clientSocket.close()

if __name__=='__main__':

	welcomeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	welcomeSocket.bind((HOST,PORT))
	clientThreads = []
	
	watchThread = Thread(target=watchDir)
	watchThread.start()

	while True:
		welcomeSocket.listen(6)
		print("Server listening for new connections")
		cSocket, clientIP = welcomeSocket.accept()
		client = clientThread(cSocket,clientIP)
		client.start()
		clientThreads.append(client)

