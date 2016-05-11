
/* 

Ringo Robot
Ringo_PreLoaded_Behaviors_Rev06
Version 6.1 12/2015

IMPORTANT NOTE:  THIS SKETCH REQUIRES ARDUINO IDE 1.6.5 OR LATER TO COMPILE
(Previous versions compile this sketch too large to fit into Ringo's processor)

This sketch showcases several possible Ringo behaviors.
Use these behaviors as starting points for your own work.
When reset or turned on, press one of the number keys on your
IR remote control to activate one of the behaviors. If Ringo
blinks red, then the key was not recognized. If Ringo blinks
green, then the key was recognized and a beavior has
been started.

Significant portions of this code written by
Dustin Soodak for Plum Geek LLC. Some portions
contributed by Kevin King.
Portions from other open source projects where noted.
This code is licensed under:
Creative Commons Attribution-ShareAlike 2.0 Generic (CC BY-SA 2.0)
https://creativecommons.org/licenses/by-sa/2.0/
Visit http://www.plumgeek.com for Ringo information.
Visit http://www.arduino.cc to learn about the Arduino.

*/

#include "RingoHardware.h"
#include "Behaviors.h"

#define REMOTE_NUM 2

void setup(){
  HardwareBegin();        //initialize Ringo's brain to work with his circuitry
  PlayStartChirp();       //Play startup chirp and blink eyes
  RxIRRestart(4);         //wait for 4 byte IR remote command
  IsIRDone();
  GetIRButton();
  RestartTimer();

}

// global variables used by Color Wheel example
int redIntensity = 0;
int greenIntensity = 0;
int blueIntensity = 0;
int red;
int green;
int blue;
int presentDirection = 0;
int hue = 0;
int hueOpposite = 180;
// end global variables used by Color Wheel example
    
void loop(){

  restart:              //label to cause program to come back to here if "MENU" on remote is pressed in any example
  
   byte button = 0;

  if(GetTime()>1000){   //blink rear pixel once a second to indicate Ringo is in "Menu" mode
      SetPixelRGB(0,0,0,100);   // turn on rear tail light to BLUE
      delay(10);                // brief delay
      OffPixels();              // turn off all pixels
      RestartTimer();           // zero timer
      } 
      
  //Example user code:  
  
  if(IsIRDone()){                   //wait for an IR remote control command to be received
      button = GetIRButton();       // read which button was pressed, store in "button" variable
      RxIRRestart(4);     
      if(button){                   // if "button" is not zero...
        switch (button){            // activate a behavior based on which button was pressed

         case REMOTE_NUM:           // Button 3, "The Ringo Dance" behavior
         RxIRRestart(4);            // restart wait for 4 byte IR remote command
         Behavior_TheRingoDance();  // what it says NO EDGE DETECTION - DON'T LET RINGO JUMP OFF YOUR TABLE!
         break;
         
         default:                   // if no match, break out and wait for a new code
         PlayNonAck();              // quick "NonAck" chirp to know a known button was received, but not understood as a valid command
         RxIRRestart(4);            //wait for 4 byte IR remote command
         SwitchMotorsToSerial();
         Serial.print("button: ");Serial.println(button);  // send button number pressed to serial window
      
         break;
        }
        
      }
      button = 0;
      
    }//end if(IsIRDone())
}


