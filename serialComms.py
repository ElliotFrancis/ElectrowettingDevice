"""This module is part of the arduino communication section
The module creates a generic abstraction for the reading and writing of serial bytes
The end of any message is declared by using the \\r\\n characters"""

import serial
import time

class SerialCommunication:
	"""Class to abstract the reading and writing to serial port
	Maintains a connection to the port
	"""
	
	def __init__(self, port_name="/dev/ttyUSB1"):
		"""Setup the serial port
		Return a connection object"""
		
		self.connection = serial.Serial()
		
		# setup the details for the connection
		self.connection.port = port_name
		self.connection.baudrate = 9600
		self.connection.bytesize = serial.EIGHTBITS
		self.connection.parity = serial.PARITY_NONE
		self.connection.stopbits = serial.STOPBITS_ONE

		#set the class attribute called input to be an empty string
		self.input=""
		
		#open the serial connection for the duration that this object is existing
		self.connection.open()
		
		#wait for 2 seconds before sending any instructions over the serial connection
		time.sleep(2)
		
	def __del__(self):
		"""Close the serial connection"""
		
		self.connection.close()

	def read(self):
		"""Read any serial characters that are waiting
		Return all characters that are read"""
		
		while self.connection.inWaiting() > 0:
			self.input += self.connection.read(1)
		
		command_list = self.input.split("\r\n")
		
		#store the last command (incomplete command) back into the input string
		self.input = command_list[-1]
		
		#return the list of all the commands except the last element (the incomplete command)
		return command_list[:-1]
	
	def write(self, command):
		"""Write the command to the serial output (making sure that it complies with the protocol)
		"""
		
		self.connection.write("%s\r\n" % (command,) )
		
		
if __name__=="__main__":

	serial_obj = SerialCommunication("/dev/ttyACM0")
	
	commands = ["VER","S21", "C54", "CAP"]
	
	# attempt to send the above commands over serial communication
	for command in commands:
		print("Writing %s command" % (command,))
		serial_obj.write(command)
	
		#wait 1 second for the device on the other end to respond
		time.sleep(1)
	
		msg_list = serial_obj.read()
		if len(msg_list) != 0:
			print [msg for msg in msg_list]
	
	

