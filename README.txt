
THIS FILE CONTAINS INFORMATION ON HOW TO INSTALL AND RUN THE CODE


Arduino Firmware
The arduino firmware code can be found under ArduinoCode/ArduinoCode.ino
To install the firmware, this file must be opened in the Arduino IDE. Then, with the Arduino connected, the "Upload" button must be clicked.


Python main program
The code is known to run using Python 2.7.6 on Linux.

To run the program, one must navigate to the MainSoftware folder in terminal. To run the entire system you can type: 
python droplet_program.py userinput_valid.txt

To see the output from a bad user input file, you can type: 
python droplet_program.py userinput_invalid.txt

To run the test suite of the visual feedback system (as demonstrated in my video presentation) you can type:
python cameraInput.py
