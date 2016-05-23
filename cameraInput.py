import cv2
import numpy as np
import time
import math

class CameraInput:
	"""Class to contain the camera input code,
	includes methods used by the main methods,
	also setup of the input stream"""
	
	def __init__(self, device_name=""):
		"""Setup the camera for input at the given device name"""
		if device_name=="":
			self.capture=None
		else:
			self.capture = cv2.VideoCapture(device_name)
		

	def release_video_capture(self):
		"""Release the video capture"""
		
		if self.capture != None:
			self.capture.release()
	
	
	def get_line_intersection(self, r1, theta1, r2, theta2):
		"""Solves line intersection for lines represented in the form:
		x cos(theta) + y sin(theta) = rho
	
		Returns a tuple of x and y coordinates at the point of intersection"""
	
		# y = x(-cos(theta)/sin(theta)) + r/sin(theta)
	
		#		   r2		   		r1
		#      -----------  -   -----------
		#	   sin(theta2)	  	sin(theta1)
		# x = --------------------------------
		#	  -cos(theta1)	+   cos(theta2)
		#	  ------------      -----------
		# 	   sin(theta1)		sin(theta2)
	
		# x = ((r2/sin(theta2)) - (r1/sin(theta1))) / ((-cos(theta1)/sin(theta1)) + (cos(theta2)/sin(theta2)))
		
		#deal with divide by zero by setting the angle to be just off 0
		if theta1 == 0:
			theta1 = 0.00001
		if theta2 == 0:
			theta2 = 0.00001
		
		x = ((r2/math.sin(theta2)) - (r1/math.sin(theta1))) / ((-math.cos(theta1)/math.sin(theta1)) + (math.cos(theta2)/math.sin(theta2)))
		y = (x * (-math.cos(theta1) / math.sin(theta1))) + (r1/math.sin(theta1))
		
		return (int(x), int(y))
	
	def get_euclidean_distance(self, point1, point2):
		"""Get the Euclidean distance between the two given points.
		dist = sqrt(diffx^2 + diffy^2)"""
	
		diffx = point1[0] - point2[0]
		diffy = point1[1] - point2[1]
	
		return np.sqrt((diffx**2) + (diffy**2))
	
	def calculate_line(self, x, y, theta):
		"""Calculate the rho value of the line equation for a 
		line with a given theta and that intersects the given points"""
	
		# x cos(theta) + y sin(theta) = rho
		return (x * np.cos(theta)) + (y * np.sin(theta))
	
	
	def find_drop_positions(self, filename=""):
		"""Find the droplet positions in the current image"""
		
		if filename == "":
			#get image from camera
			ret, img = self.capture.read()
			
			#camera code not in use!
			return []
		else:
			#read the image from the given file
			img = cv2.imread(filename)
			
		#apply a small amount of blur
		img = cv2.medianBlur(img, 3)
		#convert the image to grayscale
		gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

		#create a blank image of the same size to draw the visualisation of the output
		s = gray.shape
		blank = np.zeros(s, np.uint8)

		#apply another larger blurring function
		gaus_blur = cv2.GaussianBlur(gray,(5,5),0)

		#use the canny algorithm to find all the edges in the image
		edges = cv2.Canny(gaus_blur, 150, 150)

		#find the contours in the image and draw them to the visualisation
		contours, hierarchy = cv2.findContours(edges,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		cv2.drawContours(blank,contours, -1, (255,255,255), 1)

		#use the hough line detection algorithm to find all the lines in the image
		lines = cv2.HoughLines(blank,1,np.pi/180,100)

		#find the top, left, right and bottom lines in the image (only looking at lines that are horizontal or vertical)
		top =    {'value': 10000, 'rho': 0, 'theta': 0}
		left =   {'value': 10000, 'rho': 0, 'theta': 0}
		bottom = {'value':     0, 'rho': 0, 'theta': 0}
		right =  {'value':     0, 'rho': 0, 'theta': 0}

		for rho,theta in lines[0]:
			a = np.cos(theta)
			b = np.sin(theta)
			x0 = a*rho
			y0 = b*rho
		
			#we are assuming that the camera has been aligned roughly square with the board
			if theta > (np.pi/2) - 0.3 and theta < (np.pi/2) + 0.3:
				#this is a horizontal line
				if y0 < top['value']:
					top['value'] = y0
					top['rho'] = rho
					top['theta'] = theta
				
				if y0 > bottom['value']:
					bottom['value'] = y0
					bottom['rho'] = rho
					bottom['theta'] = theta
			else:
				#this is probably a vertical line (there should not be any other lines)
				if x0 < left['value']:
					left['value'] = x0
					left['rho'] = rho
					left['theta'] = theta
				
				if x0 > right['value']:
					right['value'] = x0
					right['rho'] = rho
					right['theta'] = theta    
			

		# http://docs.opencv.org/2.4/modules/imgproc/doc/feature_detection.html?highlight=houghcircles#cv2.HoughCircles
		#use hough circle detection to find all the circles of a particular size (droplets) in the image
		droplets = cv2.HoughCircles(gaus_blur, cv2.cv.CV_HOUGH_GRADIENT, 1, 15, param1=50, param2=30, minRadius=20, maxRadius=50)
		
		top_left_point = self.get_line_intersection(top['rho'], top['theta'], left['rho'], left['theta'])
		cv2.circle(blank, top_left_point, 7, (255,255,255), 1)

		bottom_left_point = self.get_line_intersection(bottom['rho'], bottom['theta'], left['rho'], left['theta'])
		cv2.circle(blank, bottom_left_point, 7, (255,255,255), 1)

		top_right_point = self.get_line_intersection(top['rho'], top['theta'], right['rho'], right['theta'])
		cv2.circle(blank, top_right_point, 7, (255,255,255), 1)

		# next calculate the length of the top line and the left line
		top['length']  = self.get_euclidean_distance(top_left_point, top_right_point)
		left['length'] = self.get_euclidean_distance(top_left_point, bottom_left_point)

		drop_pos = []
		
		#only decode the droplets if there are some that have been detected
		if droplets != None:

			# for each circle found, calculate its grid position
			for droplet in droplets[0]:
				# find the values for the line that is parallel with the left line and goes through the droplet centre
				rhox = self.calculate_line(droplet[0], droplet[1], left['theta'])
				rhoy = self.calculate_line(droplet[0], droplet[1], top['theta'])

				# find the intersection between that line and the top line
				intersectionx = self.get_line_intersection(rhox, left['theta'], top['rho'], top['theta'])
				intersectiony = self.get_line_intersection(rhoy, top['theta'], left['rho'], left['theta'])
	
				# find the distance between the intersection and the top left corner
				distx = self.get_euclidean_distance(top_left_point, intersectionx)
				disty = self.get_euclidean_distance(top_left_point, intersectiony)
	
				# x 'grid position' = (distance / top length) * 8  (+1 to start from 1 not 0)
				xgridpos = (8 * distx / top['length']) + 1
				ygridpos = (8 * disty / left['length']) + 1
	
				drop_pos.append((int(xgridpos),int(ygridpos)))
			
				cv2.circle(blank,(droplet[0],droplet[1]),droplet[2],(255,255,255),2)

		##for visualising the output:
		#cv2.imshow("Output", blank)
		#cv2.waitKey(0)
		
		#return the list of droplet grid positions
		return drop_pos


if __name__=="__main__":
	#test suite
	
	camIn = CameraInput()
	
	#a list of my test input images and the position of the droplets within them
	images = [("test_4_6.jpg",(4,6)), ("test_4_5.jpg", (4,5)), ("test_5_5.jpg", (5,5)), ("test_6_5.jpg", (6,5))]
	
	for i in range(0,4):
		drop_positions = camIn.find_drop_positions(images[i][0])
		
		if images[i][1] in drop_positions:
			print "SUCCESS: Program found the position of the droplet"
		else:
			print "FAILED: Program did not find the position of the droplet in",images[i][0]

	
	

