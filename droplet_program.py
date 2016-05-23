"""This module will track each droplet and decide where to send them next
The arduino communications section will be used to communicate with the hardware
The computer vision section will be used to track if a droplet has moved successfully"""

#import the my custom modules
import arduinoComms
from userInput import Instructions
import userInput
import cameraInput

#import the time module to use the time.sleep function
import time

#import the sys module so that we can take command line options
import sys

class Droplet:
	
	def __init__(self, position, id_value):
		"""Initialise object state"""
		
		self.position = position
		self.id = id_value
		self.name = ""
		self.path = []
	
	def update_along_path(self,arduino_comm):
		"""Update the droplet along the its path"""
		
		#only move the droplet if the path is not empty
		if self.path != []:
			currentdir = self.path.pop()
			self.move(currentdir, arduino_comm)
			
			# return whether the path is complete yet
			return self.path != []
		else:
			return False
	
	def move(self, direction, arduino_comm):
		"""Move the droplet in the direction given
		Direction is in the form: {xDir: -1, yDir: 0} -- that would move left one block
		Diagonals are not allowed"""
		
		#validate the direction
		if direction["xDir"] != 0 and direction["yDir"] != 0:
			#error, invalid values (cannot go diagonal)
			raise ValueError("Droplets cannot move in diagonals")
		
		#clear current position
		arduino_comm.clear_plate(self.position["x"], self.position["y"])
		
		#set new position (to attract the droplet to)
		self.position["x"] += direction["xDir"]
		self.position["y"] += direction["yDir"]
		arduino_comm.set_plate(self.position["x"], self.position["y"])
		
	def add_path(self, position_aim):
		"""Create a path that moves the droplet towards the position_aim plate
		The path consists of a list of directions that describe the step by step path of the droplet
		Directions can only be horizontal or vertial (not both: diagonal)
		A direction is a dictionary with xDir and yDir elements, each of which is an integer between -1 and 1"""
		
		path_position = {'x': self.position["x"], 'y': self.position["y"]}
		
		while path_position != position_aim:
		
			diffx = position_aim["x"] - path_position["x"]
			diffy = position_aim["y"] - path_position["y"]
		
			if abs(diffx) > abs(diffy):
				#move in the horizontal direction towards the position_aim
				if path_position["x"] > position_aim["x"]:
					direction = {'xDir': -1, 'yDir': 0}
				elif path_position["x"] < position_aim["x"]:
					direction = {'xDir': 1 , 'yDir': 0}
				else:
					#this else 'should' never run but just in case it does, the program will be able to handle it
					direction = {'xDir': 0 , 'yDir': 0}
					
				#add the direction to the path
				self.path.append(direction)
				
				#update the path_position
				path_position["x"] += direction["xDir"]
			else:
				#move in the vertical direction
				if path_position["y"] > position_aim["y"]:
					direction = {'xDir': 0, 'yDir': -1}
				elif path_position["y"] < position_aim["y"]:
					direction = {'xDir': 0, 'yDir': 1}
				else:
					#this else 'should' never be run...
					direction = {'xDir': 0, 'yDir': 0}
				
				#add the direction to the path
				self.path.append(direction)
				
				#update the path_position
				path_position["y"] += direction["yDir"]


class Grid:
	"""Keeps track of the grid and each droplet on it"""
	
	def __init__(self):
		"""Initialise object state"""
		
		self.dimensions = {'maxX': 8, 'maxY': 9}
		self.droplet_list = []
		self.arduino_comm = arduinoComms.ArduinoCommunication("/dev/ttyACM0")
		self.ui = userInput.UserInput()
		self.camInput = cameraInput.CameraInput("/dev/video1")
		self.waiting_time = 1
		
	
	def load_program(self, filename):
		"""Load the ui program"""
		
		runprogram = True
		
		# try to load the input file, catching the exception of any issues in the instruction set
		try:
			self.ui.load_input_file(filename)
		except ValueError as e:
		
			#print the issues that have risen from loading the instruction set
			print
			print e.args[0]
			print "\n".join(self.ui.errors)
			print
			print "Would you like to continue? (y/n)"
			response = raw_input("--> ")
			
			runprogram = (response == "y" or response == "yes" or response == "Y" or response == "YES")
		
		return runprogram
		
	def run_program(self):
		"""Run the program from the user input
		The program is stored in the self.ui object as a set of sequential instructions
		The system does not move on to the next instruction until the current instruction is complete"""
		
		#for each instruction in the set, execute it on the hardware
		for instruction in self.ui.instruction_set:
			if instruction[0] == Instructions.NEW:
				
				#add a new droplet to the droplet_list
				new_droplet = Droplet({'x': int(instruction[1][1]), 'y': int(instruction[1][2])}, instruction[1][0])
				self.droplet_list.append(new_droplet)
				
			elif instruction[0] == Instructions.MIX:
				
				#find the droplet index of both the referred droplets
				droplet1 = self.get_droplet_index(instruction[1][0])
				droplet2 = self.get_droplet_index(instruction[1][1])
				
				#add a path for the first droplet from its current position to the position of the other droplet
				self.droplet_list[droplet1].add_path(self.droplet_list[droplet2].position)
				
				#update droplet1 along its path until there is no change
				self.move_along_paths([droplet1])
				
				#declare the droplets as merged by creating a new droplet with the new id at the position of droplet2
				new_droplet = Droplet({'x': self.droplet_list[droplet2].position["x"], 'y': self.droplet_list[droplet2].position["y"]}, instruction[1][2])
				
				#add the new droplet to the list
				self.droplet_list.append(new_droplet)
				
				#remove the old droplets (droplet1 and droplet2)
				del self.droplet_list[droplet1]
				del self.droplet_list[droplet2]
				
			elif instruction[0] == Instructions.SPLIT:
				
				#perform the split in any direction by turning on two of the plates either side of the droplet
				index = self.get_droplet_index(instruction[1][0])
				new_positions = self.split_droplet(index)
				
				#if the split occurred sort out the old and new droplets
				if len(new_positions) == 2:
					#create the two new droplets and assign their names
					new_droplet1 = Droplet(new_positions[0], instruction[1][1])
					new_droplet2 = Droplet(new_positions[1], instruction[1][2])
					
					#add the droplets to the list
					self.droplet_list.append(new_droplet1)
					self.droplet_list.append(new_droplet2)
					
					#delete the old droplet
					del self.droplet_list[index]
				
			elif instruction[0] == Instructions.WAIT:
				
				#simply wait for a specific number of time
				time.sleep(float(instruction[1][0]))
				
			elif instruction[0] == Instructions.MOVE:
				
				#find the index of the droplet
				droplet_index = self.get_droplet_index(instruction[1][0])
				
				#add a path for the indicated droplet from its current position to the indicated position
				self.droplet_list[droplet_index].add_path({'x': int(instruction[1][1]), 'y': int(instruction[1][2])})
				
				#move the droplet along the path
				self.move_along_paths([droplet_index])
		
		
	def get_droplet_index(self, droplet_id):
		"""Get the index of the droplet that has the given id value in the droplet list"""
		
		#initialise droplet_index
		droplet_index = -1
		
		#loop through each droplet in the droplet list
		for i in range(0,len(self.droplet_list)):
			if self.droplet_list[i].id == droplet_id:
				droplet_index = -1
		
		#return the found droplet_index
		return droplet_index
	
	
	def move_along_paths(self, droplet_indexes):
		"""Move each droplet in the droplet_indexes list along its path one at a time, 
		waiting inbetween each total step"""
		
		#initialise a flag to distinguish if there are any paths yet unfinished
		any_remaining = True
		
		while any_remaining:
			any_remaining = False
			
			for index in droplet_indexes:
				if self.droplet_list[index].update_along_path(self.arduino_comm):
					#at least one droplet is still moving
					any_remaining = True
				
			#wait for a second inbetween each droplet moving 1 position step
			time.sleep(self.waiting_time)
			
			#check that the expected position and actual position from the visual feedback match up
			droplet_positions = self.camInput.find_drop_positions()
			#for index in droplet_indexes:
				#if not self.droplet_list[index].position in droplet_positions:
					#print "Droplet " + self.droplet_list[index].id + " does not match the visual feedback!"
			


	def split_droplet(self, droplet_index):
		"""Split the droplet into two"""
		
		#check if the droplet is on a horizontal edge (left or right)
		# if so, check if it is on a vertical edge (top or bottom)
		#  if so, move it in towards the centre by 1 in a horizontal direction before splitting
		
		xpos = self.droplet_list[droplet_index].position["x"]
		ypos = self.droplet_list[droplet_index].position["y"]
		
		done_already = False
		
		new_positions = []
		
		#check if we are at the left or right
		if xpos == 1 or xpos == self.dimensions["maxX"]:
			# check if we can do the split horizontally
			if self.dimensions["maxX"] <= 2:
				#check if we can do the split vertically
				if self.dimensions["maxY"] <= 2:
					print "Splitting is not available on such a small working area, needs 3 consecutive plates"
				else:
					#do the split vertically
					#check if we are at the top or bottom
					if ypos == 1 or ypos == self.dimensions["maxY"]:
						#move the droplet towards the centre vertically
						direction = 0
						#find which direction to move in (up or down)
						if ypos == 1:
							direction = 1
						else:
							direction = -1
						
						self.droplet_list[droplet_index].move({'xDir': 0, 'yDir': direction})
					#do the split in the vertical direction
					done_already = True
					
					self.arduino_comm.set_plate(xpos, ypos - 1)
					self.arduino_comm.set_plate(xpos, ypos + 1)
					
					new_positions.append({'x': xpos, 'y': ypos - 1})
					new_positions.append({'x': xpos, 'y': ypos + 1})
					
			else:
				#move the droplet towards the centre horizontally
				direction = 0
				#find which direction to move in (left or right)
				if xpos == 1:
					direction = 1
				else:
					direction = -1
					
				self.droplet_list[droplet_index].move({'xDir': direction, 'yDir': 0}, self.arduino_comm)
		
		if not done_already:
			#do the split in the horizontal direction
			self.arduino_comm.set_plate(xpos - 1, ypos)
			self.arduino_comm.set_plate(xpos + 1, ypos)
			
			new_positions.append({'x': xpos - 1, 'y': ypos})
			new_positions.append({'x': xpos + 1, 'y': ypos})
			
		#wait for 1 second to let the droplets move
		time.sleep(self.waiting_time)
		
		#check if the splitting happened
		if len(new_positions) == 2:
			#if so check the expected position of each of the resulting droplets with the visual feedback
			droplet_positions = self.camInput.find_drop_positions()
			#if not new_positions[0] in droplet_positions or new_positions[1] in droplet_positions:
				#print "Droplet positions after split do not match the visual feedback!"
		
		return new_positions


if __name__=="__main__":
	#The main program
	
	if len(sys.argv) < 2:
		print "Usage:   python droplet_program inputfile.txt"
		print
		print "Please specify an input file"
	else:
		grid = Grid()
		
		#load the user input file
		if grid.load_program(sys.argv[1]):
			
			#run through the protocol
			print "Instruction set contains no issues"
			print "Running program..."
			
			grid.run_program()
		
		print "Done"
	
	
	
	
