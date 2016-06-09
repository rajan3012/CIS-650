#include "RingoHardware.h" //include Ringo background functions
#include "IRCommunication.h" //sending receiving IR signals
int leftOn, leftOff, rightOn, rightOff, rearOn, rearOff; //declare variables
int leftDiff, rightDiff, rearDiff; //more variables

int frontAvg, rearAvg;
#define REMOTE_NUM 4 //yellow bug listening for 4 
//#define REMOTE_NUM 9 //red bug listening for 9 
#define SRC  0x00
#define DST  0xFF
byte msg[] = {0x68,0x97};
byte code[] = {0x00,0xff,0x30,0xcf}; //yellow bug sends 1 
//byte code[] = {0x00,0xff,0x68,0x97};  //red bug sends 0

void setup()
{
  //HardwareBegin(); //initialize Ringo’s circuitry
  PlayStartChirp(); //play startup chirp and blink eyes
  
  RxIRRestart(4);         //wait for 4 byte IR remote command
  IsIRDone();
  GetIRButton();
  RestartTimer();
  Serial.begin(9600);
  //OnEyes(0,0,200); //blue to start
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
  
  //Serial.print(leftOn); // print the results to the serial window
  //Serial.print(" ");
  //Serial.print(rightOn); // print the results to the serial window
  //Serial.print(" ");
  //Serial.print(rearOn); // print the results to the serial window
  //Serial.println(" ");
  //delay(200);
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
  
     if(leftOn <100 && rightOn >=100) //WHITE detected by RIGHT sensor,  BLACK detected by LEFT sensor
    {
      Serial.print("\n****");
      Serial.println("lefton\trighton\tFront Avg\n");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print(" ");
      Serial.println(rightOn); // print the results to the serial window

      Serial.print("\n*****LEFT sensor detected BLACK  \nLeftSensor Val =");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print("\n***");
      //PlayChirp(100,100);
      OnEyes(200,0,0);  //red - left sensor detects black
      return 1;
    }  
    else if(rightOn <100 && leftOn >=100) //WHITE detected by LEFT sensor and BLACK detected by RIGHT sensor
    {
      Serial.print("\n***");
      Serial.println("lefton\trighton\n");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print(" ");
      Serial.print(rightOn); // print the results to the serial window
      Serial.print(" ");
      Serial.print("\n*****RIGHT sensor detected BLACK  \nRightSensor Val =");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print("\n***");
      //PlayChirp(100,100);
      OnEyes(0,200,0);  //green - right sensor detects black
      return 2;
    }
    else if(leftOn <100 && rightOn < 100) //Both detected BLACK
    {
      Serial.print("\n***");
      Serial.println("lefton\trighton\n");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print(" ");
      Serial.println(rightOn); // print the results to the serial window

      //PlayChirp(100,100);
      OnEyes(0,0,200);  //blue - both detected black
      Serial.print(" BOTH DETECTED BLACK!");
      return 4;
    }
    else if(rightOn >=100 && leftOn >=100) //both detected WHITE
    {
      Serial.print("\n***");
      Serial.println("lefton\trighton\n");
      Serial.print(leftOn); // print the results to the serial window
      Serial.print(" ");
      Serial.println(rightOn); // print the results to the serial window

      //PlayChirp(100,100);
      OnEyes(50,50,50);  //white - both detected white
      
      Serial.print("BOTH SENSORS DETECTED WHITE!");
      return 3;
    }
    
 
  
  delay(500);
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
bool detect_flag = false;
bool done = false;
void loop()
{

  
  restart:
    byte button;
  //if(IsIRDone())  //wait for an IR remote control command to be received

  if(done || IsIRDone())  //wait for an IR remote control command to be received
  {                   
      button = GetIRButton();       // read which button was pressed, store in "button" variable
     
      if(button){                   // if "button" is not zero...
        switch (button){            // activate a behavior based on which button was pressed

         case REMOTE_NUM:                    // Button 9, "Drive with remote control" behavior
         delay(3000);
         Serial.print("\n***key pressed***\n");
         PlayAck();
         //edge_detected = 0;
         //moveForward();
         detect_flag = true;
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
       done =false;
  }
  /*
  edge = LookForEdge();
  if(FrontEdgeDetected(edge))
  {
    Motors(0,0);
    PlayChirp(0,0);
  }*/
  
  Serial.print("\n***In loop***\n");
  //sense_edge();
  if(detect_flag == true)
  {
    edge_detected = sense_edge();
    
    //Serial.print("\nEdge detected?\n");
    //Serial.print(edge_detected);
   
    if(edge_detected == 1) //left sensor detected back - mover right motor
    {
        Serial.println("Left Detected Black, Move Right motor");
        //Motors(0,30);
        delay(300);
  
    }
    else if(edge_detected == 2)
    {
      Serial.println("Right Detected Black, Move Left motor");
      //Motors(30,0);
      delay(300);
    }
    else if(edge_detected == 3)
    {
      Serial.println("Continue moving - following the line!");
      //Motors(30,32.5);
      
    }
    else if(edge_detected == 4)
    {
      Serial.println("Stop! Both detected black!");
      delay(400);//so that it moves a bit ahead of the black line
      //Motors(0,0);
      detect_flag = false;
      done = false; // just to make sure it was set correctly 
      /*
      while(!done)
      {
        TxIR(code, sizeof(code));
        RxIRRestart(sizeof(code));
        if(IsIRDone()){
          done = true;
          RxIRRestart(4); 
        }
        delay(100);
      }*/
       Serial.println("Sending Code BEFORE... ");

      int i=0;
      while(i<10)
      {
        Serial.print(i);
        //Serial.println("  Sending Code ... ");
       
        TxIR(code, sizeof(code));
        RxIRRestart(sizeof(code));
        Serial.println("Sending Code ... ");
        delay(500);

        if(IsIRDone()){
          Serial.println("Recieved Signal!! ");
          done = true;
          i=10;
        }
        delay(500);
        i++;
        RxIRRestart(sizeof(code)); 

      }
      
      
        //delay(2000);
      //Motors(0,0);
    }
  }
    
  //delay(300);
  //moveForward();
}
