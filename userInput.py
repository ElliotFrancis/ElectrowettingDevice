"""This module allows the user to input a text file describing a set of instructions for the hardware
The instruction set can consist of any number of valid instructions in the described protocol
Any instruction lines that cannot be parsed successfully will be flagged in some way and the protocol will not run.
The protocol for user input is described in detail in the file named: UserProtocol.txt"""

#we are using a regular expression in UserInput.extract_parameters method
import re
import os.path

class Instructions:
	"""This class acts as an enum to hold the different types of commands"""
	NEW		= 1
	MIX		= 2
	SPLIT	= 3
	WAIT	= 4
	MOVE	= 5
	
	ExpectedParams = {NEW: 3, MIX: 3, SPLIT: 3, WAIT: 1, MOVE: 3}

class UserInput:
	"""This class contains code to read a user input file and hold the instruction set"""
	
	def __init__(self):
		"""Initialise the class"""
		# this list will hold all the instructions that have been extracted
		self.instruction_set = []
		# a list of protocol errors so the user can see where things went wrong
		self.errors = []
		self.defined_droplets = []
		self.deleted_droplets = []
		
		
	def load_input_file(self, filename):
		"""Load the input file into an instruction set
		Throw exception if the file is empty
		Throw exception if there are errors (but still load all the valid instructions)
		Any previous instructions are cleared before loading the new file"""
		
		# clear the previous instructions
		self.instruction_set = []
		self.errors = []
		
		instructions = []
		
		# read the contents of the file with name 'filename'
		if os.path.isfile(filename):
			txt = open(filename).read()
		else:
			raise ValueError("The file cannot be found: Please check that it is spelt correctly")
			
		
		# split the text into line by line instructions
		instructions = txt.split('\n')
		# for windows: remove any carriage return characters
		instructions = filter(lambda ch: ch != '\r', instructions)
		
		line_count = 1
		
		for i in instructions:
			if i != "" and i[0] != " ":
				try:
					instruction_id = self.match_instruction(i)
					params = self.extract_parameters(instruction_id, i)
					
					self.check_defined_droplets(instruction_id, params)
					
					# add the 'decoded' instruction to the instruction set
					# instructions in the set are in the form: (instruction_id, [list of params])
					self.instruction_set.append((instruction_id, params))
					
				except ValueError as val_e:
					self.errors.append("Line %i: '%s' ::: %s" % (line_count, i, val_e.args[0]))
					
			line_count += 1
		
		if len(self.errors) > 0:
			raise ValueError("There were errors in the instruction set")
		
	
	def match_instruction(self, instruction):
		"""Matches an instruction to one of the defined ones
		Returns the "enum" of the instruction"""
		
		# convert to upper case (the protocol is case insensitive
		instruction.upper()
		
		# test which of the known instructions the given instruction is (if any)
		if instruction[0:3] == "NEW":
			return Instructions.NEW
		elif instruction[0:3] == "MIX":
			return Instructions.MIX
		elif instruction[0:5] == "SPLIT":
			return Instructions.SPLIT
		elif instruction[0:4] == "WAIT":
			return Instructions.WAIT
		elif instruction[0:4] == "MOVE":
			return Instructions.MOVE
		else:
			# if no known instruction is present, raise an exception - the passed instruction is invalid
			raise ValueError("Invalid instruction")
		
	def extract_parameters(self, instruction_id, instruction):
		"""Extracts the parameter(s) of the given instruction
		Returns the extracted parameters in a list"""
		
		parameters = []
		
		# convert to upper case to make the protocol case insensitive
		instruction.upper()
		
		# split the instruction into all its seperate parts (ignore any extra symbols)
		tokens = re.split("[ >,+]", instruction)
		
		# remove empty strings
		tokens = [token for token in tokens if len(token) != 0]
		expected_params = Instructions.ExpectedParams[instruction_id]
		if len(tokens) - 1 < expected_params:
			raise ValueError("Too few arguments for this instruction")
		elif len(tokens) - 1 > expected_params:
			raise ValueError("Too many arguments for this instruction")
		
		# return all instruction parameters except the first one (the actual instruction)
		return tokens[1:]
		
	def check_defined_droplets(self, instruction_id, params):
		"""Checks that droplets are defined before they are used in the program,
		Checks that new droplets being defined are not currently defined, and defines them"""
		
		undefined_droplets = ""
		
		try:
			if instruction_id == Instructions.NEW:
				undefined_droplets = ". Droplet %s cannot be defined" % (params[0])
				self.define_droplet(params[0])
			elif instruction_id == Instructions.MIX:
				undefined_droplets = ". Droplet %s cannot be defined" % (params[2])
				self.check_droplet_is_defined(params[0])
				self.check_droplet_is_defined(params[1])
				
				self.remove_defined_droplet(params[0])
				self.remove_defined_droplet(params[1])
				
				self.define_droplet(params[2])
			elif instruction_id == Instructions.SPLIT:
				undefined_droplets = ". Droplet %s and droplet %s cannot be defined" % (params[1],params[2])
			
				self.check_droplet_is_defined(params[0])
				self.remove_defined_droplet(params[0])
				
				self.define_droplet(params[1])
				self.define_droplet(params[2])
			elif instruction_id == Instructions.MOVE:
				self.check_droplet_is_defined(params[0])
				
		except ValueError as val_e:
			raise ValueError(val_e.args[0] + undefined_droplets)
		
	def define_droplet(self, droplet):
		"""This defines the droplet if it not already defined, if it is already defined, it throws an error"""
		
		#check if already defined
		if droplet in self.defined_droplets:
			raise ValueError("Droplet %s has already been defined previously in the instruction set" % (droplet,))
		else:
			self.defined_droplets.append(droplet)

	def check_droplet_is_defined(self, droplet):
		"""This checks if the given droplet name is already defined"""
		
		if droplet not in self.defined_droplets:
			errstring = ""
			if droplet in self.deleted_droplets:
				errstring = "Droplet %s is no longer available at this point in the instruction set" % (droplet,)
			else:
				errstring = "Droplet %s has not been defined yet" % (droplet,)
				
			raise ValueError(errstring)
			
	def remove_defined_droplet(self, droplet):
		"""This removes a droplet definition"""
		
		self.defined_droplets.remove(droplet)
		self.deleted_droplets.append(droplet)

if __name__=="__main__":
	
	i = UserInput()
	try:
		i.load_input_file("testinput.txt")
		print "No Errors"
	except ValueError as e:
		print e.args[0]
		print "\n".join(i.errors)
	
	print
	print "Valid Instructions: %i" % (len(i.instruction_set),)
	
	
	
	

