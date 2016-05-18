#include "RingoHardware.h" //include Ringo background functions
#include "IRCommunication.h" //sending receiving IR signals
int leftOn, leftOff, rightOn, rightOff, rearOn, rearOff; //declare variables
int leftDiff, rightDiff, rearDiff; //more variables

int frontAvg, rearAvg;
int flag;
#define REMOTE_NUM 5
#define SRC  0x00
#define DST  0xFF
byte code[] = {0x00,0xff,0x38,0xC7};

void setup()
{
  HardwareBegin(); //initialize Ringo’s circuitry
  PlayStartChirp(); //play startup chirp and blink eyes  
  RxIRRestart(4);         //wait for 4 byte IR remote command
  IsIRDone();
  GetIRButton();
  RestartTimer();
  Serial.begin(9600);
  OnEyes(0,0,200); //blue to start
  delay(100);
  OffEyes();
}

int sense_edge()
{
  Serial.print("\n***Checking for edge***\n");
  digitalWrite(Source_Select, LOW); // select bottom light sensors
  digitalWrite(Edge_Lights, HIGH); // turn on the IR light sources
  delayMicroseconds(200); // let sensors stabilize
  leftOn = analogRead(LightSense_Left); // read sensors w/ IR lights on
  rightOn = analogRead(LightSense_Right); // read sensors w/ IR lights on
  rearOn = analogRead(LightSense_Rear); // read sensors w/ IR lights on
  Serial.println("lefton\trighton\trearon\n");
  Serial.print(leftOn); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rightOn); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rearOn); // print the results to the serial window
  Serial.println(" ");
  delay(200);
  digitalWrite(Edge_Lights, LOW); // turn off the IR light sources
  delayMicroseconds(200); // let sensors stabilize
  /*
  leftOff = analogRead(LightSense_Left); // read sensors w/ IR lights off
  rightOff = analogRead(LightSense_Right); // read sensors w/ IR lights off
  rearOff = analogRead(LightSense_Rear); // read sensors w/ IR lights off

  Serial.println("leftoff\trightoff\trearoff");
  Serial.print(leftOff); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rightOff); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rearOff); // print the results to the serial window
  Serial.println(" ");
  //delay(200);
  leftDiff = leftOn-leftOff; // subtract out ambient light
  rightDiff = rightOn-rightOff; // subtract out ambient light
  rearDiff = rearOn-rearOff; // subtract out ambient light
  Serial.println("leftdiff\trightdff\treardiff\n");
  Serial.print(leftDiff); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rightDiff); // print the results to the serial window
  Serial.print(" ");
  Serial.print(rearDiff); // print the results to the serial window
  Serial.println(" "); // blank line with carriage return*/
  //delay(250); // wait 1/4 second before doing it again

  frontAvg = (leftOn + rightOn)/2;
  rearAvg = rearOn;

  
  //if(rearAvg <=100)
  if(frontAvg <=100) //black line detected
  {
    PlayChirp(100,100);
    //OnEyes(200,0,0);  //red - edge detected
    delay(100);
    OffEyes();
    return 1;    
  }
  //OnEyes(0,200,0); //green - no edge
  return 0;
}

int moveForward()
{
  Serial.print("\n***Moving***\n");
  Motors(30,32.5);  //Motors(LEFT, RIGHT);
  
  delay(50);
  return 0;
}

int edge_detected = 0;
char edge;

void loop()
{
  
  restart:
  byte button;

  if(IsIRDone())  //wait for an IR remote control command to be received
  {                   
      button = GetIRButton();       // read which button was pressed, store in "button" variable
     
      if(button){                   // if "button" is not zero...
        switch (button){            // activate a behavior based on which button was pressed

         case REMOTE_NUM:                    // Button 9, "Drive with remote control" behavior
         delay(3000);
         Serial.print("\n***key pressed***\n");
         //PlayAck();
         //edge_detected = 0;
         //flag = 1;
         moveForward();
         //OnEyes(0,200,0);  //green
         RxIRRestart(4);            // restart wait for 4 byte IR remote command
         break;
         default:                   // if no match, break out and wait for a new code
           PlayNonAck();              // quick "NonAck" chirp to know a known button was received, but not understood as a valid command          
           SwitchMotorsToSerial();
           Serial.print("button: ");
           Serial.println(button);  // send button number pressed to serial window
        }
      }
  RxIRRestart(4);
  }
  /*
  edge = LookForEdge();
  if(FrontEdgeDetected(edge))
  {
    Motors(0,0);
    PlayChirp(0,0);
  }*/
  
  Serial.print("\n***In loop***\n");
  
  edge_detected = sense_edge();
  Serial.print("\nEdge detected?\n");
  Serial.print(edge_detected);

  if(edge_detected == 1)
  { 
      //move till no edge
      //delay(100);
      Motors(0,0); //kill motors
      PlayChirp(0,0);
      //OnEyes(0,0,0);
      TxIR(code, sizeof(code));
      RxIRRestart(sizeof(code));
      //delay(1000);
      //edge_detected = 0;
  }

  //flag = 0;
  //delay(2000);
  //moveForward();
}
