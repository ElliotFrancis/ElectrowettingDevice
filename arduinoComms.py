"""This module contains code to communicate specifically to the arduino
All communication follows the protocol
This code abstracts the protocol so that higher layers can use this without knowing what the protocol is"""

import serialComms
import time

class ArduinoCommunication:
	
	def __init__(self, port_name, dimensions=[8,9]):
		"""Initialise the state of the object and its attributes
		"""
		
		self.serial = serialComms.SerialCommunication(port_name)
		self.maxX = dimensions[0]
		self.maxY = dimensions[1]
		
		self.msg_queue = []
		self.arduino_version = ""
	
	
	def validate_coordinates(self, x, y):
		"""Validates the given coordinates
		x and y must be positive integers
		They cannot be more than the dimensions given at initialisation, or less than 0
		"""
		
		if x < 0 or x >= self.maxX or y < 0 or y >= self.maxY:
			#error
			raise ValueError("x or y are out of bounds for set plate function")
	
		
	def set_plate(self, x, y):
		"""Sets the plate on at coordinates x, y
		x and y are positive integers
		They cannot be more than the dimensions given at initialisation, or less than 0
		"""
		self.validate_coordinates(x, y)
		
		self.msg_queue.append("S%i%i" % (x,y))
		self.serial.write(self.msg_queue[-1])
		
		
	def clear_plate(self, x, y):
		"""Clears the plate to be off at coordinates x, y
		x and y are positive integers
		"""
		
		self.validate_coordinates(x, y)
		self.msg_queue.append("C%i%i" % (x,y))
		self.serial.write(self.msg_queue[-1])
		
	
	def clear_all_plates(self):
		"""Sends a message to clear all plates (turn all plates off)"""
		
		self.msg_queue.append("CAP")
		self.serial.write("CAP")
		
	
	def get_version(self):
		"""Sends a message to get the version of the software that is running on the arduino"""
		
		self.msg_queue.append("VER")
		self.serial.write("VER")
		
	
	def check_replies(self):
		"""Check the replies from the arduino"""
		
		msg_list = self.serial.read()
		
		for msg in msg_list:
			original_msg = msg[4:]
			if len(msg) > 0:
				if msg[0] == 'V':
					original_msg = "VER"
					self.arduino_version = msg
			
			if original_msg in self.msg_queue:
				self.msg_queue.remove(original_msg)
				
			else:
				#error unexpected message arrived from arduino
				print("Unexpected message arrived from arduino: %s" % (msg,))


if __name__ == "__main__":
	# test suite for this module
	acomms = ArduinoCommunication("/dev/ttyACM0")
	acomms.set_plate(4,2)
	#acomms.set_plate(6,9) #correctly errors on this command
	acomms.clear_plate(1,6)
	acomms.clear_all_plates()
	acomms.get_version()
	
	# wait for arduino to respond
	time.sleep(4)
	
	# check the reply messages from the arduino
	acomms.check_replies()
	
	# print the returned messages to the terminal
	print("msg_queue:")
	print(acomms.msg_queue)
	print("version: %s" % (acomms.arduino_version,))
	
