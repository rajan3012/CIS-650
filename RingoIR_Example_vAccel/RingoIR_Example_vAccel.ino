#include "RingoHardware.h"
#include "FunStuff.h"
#include "IRCommunication.h"
#include "Navigation.h"

#define MSG_SIZE 3
byte msg[MSG_SIZE];

byte myID = 0x03;
byte accelx,accely;

byte maxAccelx = -1; 
byte maxAccely = -1; 

int i,n,bumpdir,heading,currentheading,degr;
int32_t largenum;


void setup() {
  HardwareBegin();        //initialize Ringo's brain to work with his circuitry
  PlayStartChirp();       //Play startup chirp and blink eyes
  SwitchMotorsToSerial(); //Call "SwitchMotorsToSerial()" before using Serial.print functions as motors & serial share a line
  CalibrateNavigationSensors();
  NavigationBegin();      //initialize navigation functionality. Ringo should be completely still when this happens.
  ResetIR(MSG_SIZE);

  Serial.begin(9600);
  Serial.print("Accel Zeros[0]"); Serial.println(AccelZeroes[0]);
  Serial.print("Accel Zeros[1]"); Serial.println(AccelZeroes[1]);  
  randomSeed(analogRead(0));
  RestartTimer();
}

void sendAccel() {
  n=AccelBufferSize();
  memset(AccelAcceleration, '\0', n);
     
  if(n){
    AccelGetAxes(AccelAcceleration);
    AccelAcceleration[0]=AccelAcceleration[0]-AccelZeroes[0];//x-axis raw
    AccelAcceleration[1]=AccelAcceleration[1]-AccelZeroes[1];//y-axis raw
  }
  accelx=-AccelAcceleration[0];//still raw x, but facing correct direction
  accely=-AccelAcceleration[1];//still raw y, but facing correct direction
  
  //if(GetTime()>200){                                                            //Debugging Code
  //  Serial.print(accelx,DEC);Serial.print(" ");Serial.println(accely,DEC);
  //  RestartTimer(); 
  //}
  
  AccelGetAxes(AccelAcceleration);
  AccelAcceleration[0]=AccelAcceleration[0]-AccelZeroes[0];//x-axis raw
  AccelAcceleration[1]=AccelAcceleration[1]-AccelZeroes[1];//y-axis raw
    
  SimpleGyroNavigation();//look at gyroscope as it turns
  
  Serial.print("SENSOR:    " );Serial.print(accelx,DEC);Serial.print(" ");Serial.println(accely,DEC);
  
  if (abs(accelx) > maxAccelx) {
    maxAccelx = accelx;
  }
  if (abs(accely) > maxAccely) {
    maxAccely = accely;
  }

  
  //Serial.print(maxAccelx,DEC);Serial.print(" ");Serial.println(maxAccely,DEC);
  //Serial.print(accelx/maxAccelx,DEC);Serial.print(" ");Serial.println(accely/maxAccely,DEC);
  //Serial.print(accelx,DEC);Serial.print(" ");Serial.println(accely,DEC);
  msg[0] = myID; // send myID around the ring for election
  msg[1] = abs(accelx*100)/maxAccelx;
  msg[2] = abs(accely*100)/maxAccely;
  
  SendIRMsg(myID, msg, MSG_SIZE);
  Serial.print("MESSAGE:  " );Serial.print(msg[0],HEX);Serial.print(" ");Serial.print(msg[1],HEX);Serial.print(" ");Serial.println(msg[2],HEX);Serial.println();

  ResetIR(MSG_SIZE);
  }  

void loop(){ 
  OnEyes(0,0,200);
  sendAccel(); 
  delay(500);
  OffEyes();
}

