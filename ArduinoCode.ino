/*
  This code implements the arduino software section of the project.
  This software takes a serial value and 
*/

// software version:
char softVersion[] = "V 0.0.1";

// ground pins 0 to 8 (y axis on grid)
int G[] = {2,3,4,5,6,7,8,9,10};

// source pins 1 to 8 (x axis on grid)
int S[] = {11,12,13,14,15,16,17,18};

// holds the circular buffer for the serial input
int serialBuffer[15];

// hold the index pointers for the circular buffer
int bufTop = 0;
int bufBottom = 0;


// ------------------------ clear all the plates ------------------------
void clearPlates() {
  // set all plates off
  
  // set all source pins high
  for (int i = 0; i < 8; i++) {
    digitalWrite(S[i], HIGH);
  }
  
  // set all ground pins low
  for (int i = 0; i < 9; i++) {
    digitalWrite(G[i], LOW);
  }
}

// ------------------------ set the plate at the given xy coordinates ------------------------
void setPlate(int x, int y)
{
  // set the given plate on
  digitalWrite(S[x-1], LOW);
  digitalWrite(G[y-1], HIGH);
}

// ------------------------ clear the plate at the given xy coordinates -----------------------
void clearPlate(int x, int y)
{
  // clear the given plate (turn off)
  digitalWrite(S[x-1], HIGH);
  digitalWrite(G[y-1], LOW);
}

// ------------------------ act on a message that has been received ------------------------
void messageReceived() {

  // hold the message in a small int buffer
  // (messages from main software are always 3 characters long (not including the \n closing char)
  char message[3];

  // extract the message from the serial buffer
  for (int i = 0; i < 3; i++) {
    message[i] = serialBuffer[bufBottom];

    // increment the bottom pointer of the circular buffer
    bufBottom++;
    if (bufBottom >= 15)
      bufBottom = 0;
  }
  
  // act on the message
  if (message[0] == 'S') {

    // the message is a set plate command, the other two bytes of the message should contain the integers for x and y

    // return acknowledgement
    Serial.print("ACK ");
    Serial.print(message[0]);
    Serial.print(message[1]);
    Serial.println(message[2]);

    // extract the two x and y coordinates and set the plate at those coords
    setPlate(message[1]-48, message[2]-48);
    
  } else if (message[0] == 'C' && message[1] != 'A' && message[2] != 'P') {
    // the message is a clear plate command, the other two bytes of the message should contain the integers for x and y

    // return acknowledgement
    Serial.print("ACK ");
    Serial.print(message[0]);
    Serial.print(message[1]);
    Serial.println(message[2]);

    // extract the two x and y coordinates and clear the plate at those coords
    clearPlate(message[1]-48, message[2]-48);
    
  } else if (message[0] == 'C' && message[1] == 'A' && message[2] == 'P') {

    // the message is a clear all plates command

    // return acknowledgement
    Serial.println("ACK CAP");
    
    clearPlates();
    
  } else if (message[0] == 'V' && message[1] == 'E' && message[2] == 'R') {

    // the message is an arduino software version request
    // return software version
    Serial.println(softVersion);
  }
}

// ------------------------ read the serial input in case there are any awaiting messages ------------------------
void readSerialInput() {
  
  int incomingByte;
  
  // loop through all available bytes from the serial input
  while (Serial.available() > 0) {
    
    // receive the 'incoming' byte from the serial input
    incomingByte = Serial.read();

    // set the new byte into the serial buffer at the current top position
    serialBuffer[bufTop] = incomingByte;

    // increment the top position 'pointer'
    bufTop++;
    if (bufTop >= 15)
      bufTop = 0;

    // check if the new byte was a new line char...
    if (incomingByte == '\n') {
      // act on the received message
      messageReceived();
      
      // reset the bottom buffer 'pointer' to be the value of the top buffer pointer...
      // ...because bufTop is now pointing at the first clear space after the \n char
      bufBottom = bufTop;
    }
  }
  
}

// ------------------------ the setup routine runs at startup (or once when you press reset) ------------------------
void setup() {
  
  // initialise the digital pins as an output.
  // initialise the ground pins
  for (int i = 0; i < 9; i++) {
    pinMode(G[i], OUTPUT);
  }
  for (int i = 0; i < 8; i++) {
    pinMode(S[i], OUTPUT);
  }

  // initialise serial communications with a date rate of 9600 bps (standard comms speed)
  Serial.begin(9600);
}

// ------------------------ the loop routine runs over and over again forever ------------------------
void loop() {

  readSerialInput();
  delay(10);
}


