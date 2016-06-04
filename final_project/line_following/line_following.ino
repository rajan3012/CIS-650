#include "RingoHardware.h" //include Ringo background functions
#include "IRCommunication.h" //sending receiving IR signals
int leftOn, leftOff, rightOn, rightOff, rearOn, rearOff; //declare variables
int leftDiff, rightDiff, rearDiff; //more variables

int frontAvg, rearAvg;
#define REMOTE_NUM 9
#define SRC  0x00
#define DST  0xFF
byte msg[] = {0x68,0x97};
void setup()
{
  //HardwareBegin(); //initialize Ringo’s circuitry
  PlayStartChirp(); //play startup chirp and blink eyes
  
  RxIRRestart(4);         //wait for 4 byte IR remote command
  IsIRDone();
  GetIRButton();
  RestartTimer();
  Serial.begin(9600);
  OnEyes(0,0,200); //blue to start
}

int sense_edge()
{
  /*
   * the bug detects white around a black. makes it seem like it's following a black line. 
   * So if left sensor detects black - turn the bug left till it finds white
   * Same with the right sensor. If black detected, turn right till you find white.
   * And keep the bug moving during this operation.
   */
   
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
  //rearAvg = rearOn;
  
  //if(rearAvg <=100)
  if(leftOn <100) //black line detected
  {
    Serial.print("\nLeft sensor detected black  \nLeftSensor Val -");
    Serial.print(leftOn); // print the results to the serial window
    
    Serial.print("\nFrontAvg Val -");
    Serial.print(frontAvg);
    Serial.print("\n***");
    //PlayChirp(100,100);
    OnEyes(200,0,0);  //red - left sensor detects black
    //return 1;
  }
  if(rightOn <100) //black line detected
  {
    Serial.print("\nRight sensor detected black \nRightSensor Val =");
    Serial.print(rightOn); // print the results to the serial window
    
    Serial.print("\nFrontAvg Val =");
    Serial.print(frontAvg);
    Serial.print("\n***");
    //PlayChirp(100,100);
    OnEyes(0,200,0);  //green - right sensor detects black
    //return 1;
  }
  if(frontAvg >= 100) //both fronst sensors detect white
  {
    Serial.print("\nBoth sensors detected white");
    Serial.print("\nFrontAvg Val =");
    Serial.print(frontAvg);
    Serial.print("\n***");
    //PlayChirp(100,100);
    OnEyes(100,100,100);  //green - right sensor detects black
  }
  
  //OnEyes(0,200,0); //green - no edge
  //return 0;
}

int moveForward()
{
  Serial.print("\n***Moving***\n");
  Motors(30,32.5);  //Motors(LEFT, RIGHT);
  //delay(500);
  return 0;
}

int edge_detected = 0;
char edge;

void loop()
{
  /*
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
         moveForward();
         RxIRRestart(4);            // restart wait for 4 byte IR remote command
         break;

         default:                   // if no match, break out and wait for a new code
         PlayNonAck();              // quick "NonAck" chirp to know a known button was received, but not understood as a valid command
         
         SwitchMotorsToSerial();
         Serial.print("button: ");
         Serial.println(button);  // send button number pressed to serial window
         RxIRRestart(4);            //wait for 4 byte IR remote command
         break;
        }
       }
  }*/
  /*
  edge = LookForEdge();
  if(FrontEdgeDetected(edge))
  {
    Motors(0,0);
    PlayChirp(0,0);
  }*/
  
  Serial.print("\n***In loop***\n");
  sense_edge();
  //edge_detected = sense_edge();
  //Serial.print("\nEdge detected?\n");
  //Serial.print(edge_detected);
  /*
  if(edge_detected == 1)
  {
      Motors(0,0);
      PlayChirp(0,0);
      SendIRMsg(SRC, DST, msg,2);
      //delay(1000);
      //edge_detected = 0;
  }*/
  delay(2000);
  //moveForward();
}
