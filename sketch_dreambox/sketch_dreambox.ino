//  --
char SoftwareVersion[21] = "SM7ECA-210219-3A";
#include <Arduino.h>
#include <WiFiMulti.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "Settings.h"
#define INC_DMR_CALLS

//----------------------------------------- DMR MODULE COMMANDS
//
#define SET_DIGITAL_CHANNEL            0x22
#define SET_ANALOG_CHANNEL             0x23
#define GET_DIGITAL_CHANNEL            0x24
#define GET_ANALOG_CHANNEL             0x25
#define SET_TRANSMIT_INFORMATION       0x26
#define QUERY_INIT_FINISHED            0x27
#define SET_ENHANCED_FUNCTION          0x28
#define SET_ENCHRYPTION_FUNKTION       0x29
#define SET_MIC_GAIN                   0x2A
#define QUERY_DIGITAL_VOICE_INFO       0x2B
#define SEND_SMS                       0x2C
#define GET_SMS                        0x2D
#define SET_VOLUME                     0x2E
#define SET_MONITOR                    0x2F
#define SET_SQUELCH                    0x30
#define SET_POWER_MODE                 0x31
#define QUERY_SIGNAL_STRENGTH          0x32
#define SET_RELAY_DISCONNECT_NET_MODE  0x33
#define QUERY_VERSION                  0x34

#define FUNC_ENABLE                    0x01
#define FUNC_DISABLE                   0x02

// ---------------------------------------------------- Pin definitions
#define  beepPin    14  //beepPin; OUTPUT, this is is actually A0 but we are to use it
//for the beeper as pin 13 was used by SPI in this case

//-------------------------------------------------------------- Main state machine states
#define IDLE_STATE 0          // unit is waiting for action
#define TRANSMIT_STATE 1      // PTT pressed transmitting
#define CHAN_CHANGE_STATE 2   // Change channel with encoder
#define REC_DMR_STATE 4       // We are receiving a call
#define SMS_REC_STATE 5       // We are receiving a SMS
#define SMS_SEND_STATE 6      // We are sending SMS
#define MODE_CHANGE_STATE 7   // Change mode - not used yet

//------------------------------------------------------------ serial comm pins
//RX, TX//additional serial ports for Nextion display
#define RXD1 2
#define TXD1 4
//RX, TX//additional serial ports for RF module
#define RXD2 16
#define TXD2 17

uint32_t serial_speed = 115200; // UART comm-speed - serial monitor
boolean DMRDebug = true;       // Communication trace
boolean NXDebug = true;         // Nextion communication trace
//--------------------------------------------------------- Global communication buffers
uint8_t buff[256];              // Global common area - DMR communication buffer
uint8_t NXbuff[100];             // Global common area - Nextion communication receive buffer
uint8_t SMSbuff[256];         // Sparar undan inkommande SMS
boolean bRecVoicemessage = false;
boolean bRecVoicemessageStart = false;
boolean bRecVoicemessageEnd = false;
boolean bCheckedreceiver = false;
boolean bSMSmessageReceived = false;

//---------------------------------------------------------- Nextion variables, moved here
//                                                           didn´t compile correctly when
//                                                           in A40Nextion_HMI module!!!!!
//------------------------------------------------------------- Nextion meny key items
uint8_t   NXselectRep;                  // selected row in replist screen
uint32_t  NXselectTG;        // TG list
uint8_t   lastNXtrans = 0;              // NX comm error debbugging aid
boolean   WIFIcallfound = false;
uint8_t   NXmaxrxTalkgroups = 32;       // Max no of talkgroup buttons on page 11
// page 4
uint8_t  p4_numRows = 6;       // number of rows of channels on page 4
uint8_t  p4_curPage = 0;        // current page of scroll list
uint8_t  p4_startRecord = 0;     // index of first record on a page
uint8_t  p4_selectedRow = 0;
boolean  p4_eof = false;
// page 5
uint8_t p5_startRecord = 0;    // index to start searching
uint8_t p5_numRows = 6;       // number of rows of channels on page 5
uint8_t p5_lastRecord = -1;    // last record read on last page
boolean p5_eof = false;
// page 6
uint8_t p6_numRows = 6;       // number of rows of channels on page 6
uint8_t p6_curPage = 0;        // current page of scroll list
uint8_t p6_startRecord = 0;     // index of first record on a page
boolean p6_eof = false;
//------------------------------------------------------------ State Machine
int     UnitState = IDLE_STATE;
int     lastUnitState;
//------------------------------------------------------------ Timer variables
unsigned long loopstart, loopstartNext, looptime, looptimelast;       // counting main loop time
static unsigned long lastInterruptTime = 0, lastInterruptRSSITime = 0;

//------------------------------------------------------------ Button status
boolean btnPTT = false;
boolean btnChangeCh = false;

////------------------------------------------------------------ Calculated freq from chan no
//long int  tx_freq, rx_freq;
//
// ----------------------------------------------------------- Scanning of time slots in IDLE_STATE
boolean   ts_scan = true;
uint32_t  tsSwitchLast;
uint32_t  tsSwitchInterval = 2000;    // hang time when switching between ts

//------------------------------------------------------------ RSSI scanning
uint32_t RSSItimer = 0;
//----------------------------------------------------------- Current received call
uint32_t rxContact;
char rxContactChar[] = "0000000";
uint32_t rxGroup;
typedef struct
{
  uint32_t ri_id;
  String ri_callsign;
  String ri_fname;
  String ri_surname;
  String ri_state;
  String ri_city;
  String ri_country;
  long  ri_count;
  uint32_t  ri_talkgroup;     //last heard on talkgroup ..
} Radioid ;
//------------------------------------------------------------- Current/Last rx contact
String ri_callsign;
String ri_city;
String ri_country;
String ri_fname;
String ri_surname;
long ri_id;
String ri_state;
uint32_t ri_talkgroup;
long  ri_count;

// ------- Setup menu items

//  long  maxCH = 40;
byte  maxAudioVolume = 9;
byte  maxMicVolume = 15;
byte  audioVolume = 4;
byte  micVolume = 15;

//----------------------------------------------------------- Saved settings
//struct allSettings { //all our settings in EEPROM
//  byte audioLevel; //1-9; default = 8
//  byte micLevel; //0-15, mic gain setting
//  char callSign[12]; //callsign, max 12 chars
//  uint32_t localID;  // DMRID
//  uint8_t chnr;
//  uint32_t TG;
//  bool ts_scan;   //
//};
//struct allSettings mySettings;
//   uint32_t mySetting_localID;  // DMRID
uint8_t   rxTGStatus[33] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                            1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                            1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0
                           };
uint32_t  rxTalkGroup[33] = {240, 2400, 2401, 2402, 240216, 2403, 2404, 2405, 2406, 24061, // List of relevant TalkGroups
                             24062, 24063, 2407, 240721, 2410, 2411, 2412, 2413, 2414, 2415, // 32 are fed into the rx group list
                             2416, 240240, 91, 9, 240850, 0, 0, 0, 0, 0, 0, 0
                            };                    // in the DMR module


//----------------------------------------------------------- Global area setting of digital and analog channels
typedef struct
{
  uint8_t  head;          //header 0x68
  uint8_t  CMD;           // command 0x22
  uint8_t  RW;            // operation type
  uint8_t  SR;            // set/response
  uint16_t CKSUM;         // checksum
  uint8_t  LEN_dummy;      // måste vara = 0
  uint8_t  LEN;            // DATA length
  uint32_t rx_freq;       //receive  frequency    400000000-48000000HZ
  uint32_t tx_freq;       //transmit frequency    400000000-48000000HZ
  uint32_t localID;       //my own DMR ID
  uint32_t GroupList[32]; //list of TGs monitored
  uint32_t tx_contact;    //contact  number  1-16776415, receiver TG or DMR ID if individual call
  uint8_t  ContactType;   //contact  type  0:individual call 1:group  call2:call all 3：full duplex
  uint8_t  power;         //0:low power  1：high power
  uint8_t  cc;            //color code0~15
  uint8_t  InboundSlot;   //0:slot 11:slot 2  TS
  uint8_t  OutboundSlot;  //0:slot 11:slot 2  TS
  uint8_t  ChannelMode;   //0:  direct connectionmode 4: true dual slot (DMR tier 2)
  uint8_t  EncryptSw;     //encryption switch1:enable 2:disable - allways use 2
  uint8_t  EncryptKey[8]; //secret key
  uint8_t  pwrsave;       //power save switch 2:disable 1:enable
  uint8_t  volume;        //Volume 1-9
  uint8_t  mic;           //micgain 0-15
  uint8_t  relay;         //relay disconnect net 2:disable 1:enable ???
  uint8_t  tail;          //trailing character
} db_digital_info;

db_digital_info digData;

typedef struct
{
  uint8_t  head;          //header 0x68
  uint8_t  CMD;           // command 0x22
  uint8_t  RW;            // operation type
  uint8_t  SR;            // set/response
  uint16_t CKSUM;         // checksum
  uint8_t  LEN_dummy;      // måste vara = 0
  uint8_t LEN;            // DATA length
  uint32_t  rx_freq;    // receive  frequency    400000000-48000000HZ
  uint32_t  tx_freq;    // transmit frequency    400000000-48000000HZ
  uint8_t   band;       // 0:narrow 1:wide
  uint8_t   power;      // 0:low power 1:high power
  uint8_t   sq;         // SQ level0~9
  uint8_t   rx_type;    // |0:carrier|1:ctcsss |2:normal DCS|3:inverse DCS
  uint8_t   rx_subcode; // |0|   0~50  |   0~82   |  0~82
  uint8_t   tx_type;    // |0:carrier  |1:ctcsss |2:normal DCS|3:inverse DCS
  uint8_t   tx_subcode; // |0|   0~50  |   0~82   |  0~82
  uint8_t   pwrsave;    // power save switch    2:disable 1:enable
  uint8_t   volume;     // Volume 1-9
  uint8_t   monitor;    // monitor switch       2:disable 1:enable
  uint8_t   relay;      // relay disconnect net 2:disable 1:enable
  uint8_t   tail;       //trailing character
} db_analog_info;

db_analog_info anaData;

//------------------------------------------------------------------------ Global SMS comm area
typedef struct
{
  uint8_t  head;        //header 0x68
  uint8_t  CMD;         //
  uint8_t  RW;          // operation type
  uint8_t  SR;          // set/response
  uint16_t CKSUM;       // checksum
  uint8_t  LEN_dummy;   // måste vara = 0
  uint8_t  LEN;         // DATA length
  uint8_t   msg_type;   // message typ 1:IP with confirm 2:IP without confirm 3:group call
  uint32_t  callNum;    // contact DMR ID
  uint16_t  filler1;    // header assume 0x20
  uint16_t  filler2;    // header assume 0x20
  uint8_t   msg[19];    // message max len 60
  uint8_t   tail;       //trailing character
} db_SMSsend_info;

typedef struct
{
  uint8_t  head;        // header 0x68
  uint8_t  CMD;         // command 0x22
  uint8_t  RW;          // operation type
  uint8_t  SR;          // set/response
  uint16_t CKSUM;       // checksum
  uint8_t  LEN_dummy;   // måste vara = 0
  uint8_t  LEN;         // DATA length
  uint32_t  callNum;    // contact DMR ID
  uint8_t   msg[60];    // message max len 60
  uint8_t   tail;       // trailing character
} db_SMSget_info;

//-------------------------------------------------------------- Channel item struct - future use
typedef struct {        //all our data of each channel in EEPROM
  uint8_t   chnr;
  uint32_t  TG;
  unsigned long rx_freq;    //receiving fregency, long int version 446.500 = 44650000, total 8 digits
  unsigned long tx_freq;    //transmiting frequency, long int version 446.500 = 44650000, total 8 digits
  unsigned int  cc;          //CC color code
  unsigned int ts;          // time slot
  byte power;               //the output power level, 0 = high; 1 = low, 2 = 3 = middle
  char nameCH[12];          //name of the channel, max 12 chars, as the char[12] = '\0',
  //so you only have 11 chars
} ChanItem ;
ChanItem curChanItem;

DmrSettingsS dmrSettings;
WifiSettingS  WifiAp;

void   NXinitDisplay();
boolean  wifiConnect();
void WiFisetTime();
void  EIMreadStatus();
void  EIMreadRepeaters();
void  EIMreadHotspots();
void  NXhandler();
void  wifiGetDMRID();

void beep(bool bp)
//---------------------------------------------------------------- beep
{
  //you can mute the beep totally from here. by default, we need beep
  //sound on key pressing except PTT
  if (bp == true)
  {
    digitalWrite(14, HIGH); //start the beep
  }
  else
  {
    digitalWrite(14, LOW); //stop the beep
  }
}

//boolean calculateFreq(long int chan)
////-------------------------------------------------------------- calculate freq
//// calculate frequency pairs fråm Channel RUxxx and Uxxx
////
//{
//  if (chan > 360 and chan < 399)      // repeater channels RUxxx
//  {
//    rx_freq = 430000000 + 12500 * chan;
//    tx_freq = rx_freq - 2000000;
//    return true;
//  }
//  if (chan > 260 and chan < 303)      // simplex channels Uxxx
//  {
//    rx_freq = 430000000 + 12500 * chan;
//    tx_freq = rx_freq;
//    return true;
//  }
//  return false;
//}

//************************************************************************* start setup
//*************************************************************************************


void setup() {
  // put your setup code here, to run once:
  Serial.begin(serial_speed);                   //Serial monitor
  Serial1.begin(57600, SERIAL_8N1, RXD1, TXD1);  //Nextion Display
#ifdef INC_DMR_CALLS
  Serial2.begin(57600, SERIAL_8N1, RXD2, TXD2); //DMR module
  Serial2.setRxBufferSize(264);                 //We need at least 177 bytes for 0x24
#endif
  pinMode(14, OUTPUT);                          //LED not used
  beep(true);                                   //set LED on
  while (!Serial)
  {
    //  ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Startar");
  NXinitDisplay();                                         // Show the DMR page
  settingsInit();
  bool initiated = settingsInitiated();
  if (initiated) {
    settingsRead(&dmrSettings);
    Serial.println(dmrSettings.localID);
  }
  else
  {
    dmrSettings.version = 0x1;
    //   dmrSettings.wifisettings[][2]= {{"jullen11", "19nittionio"},
    //                                   {"malmoe99", "Nitton99"},
    //                                   {"Arnes iPhone", "9x8z0utpnp5md"},
    //                                   {"",""}};
    dmrSettings.audioLevel = 8;         //  1-9; default = 8
    dmrSettings.micLevel = 7;           //  0-15, mic gain setting
    strcpy (dmrSettings.callSign, "SM7ECA");    // callsign, max 12 chars
    dmrSettings.localID = 2400530;      //   DMRID
    dmrSettings.chnr = 2;               //
    dmrSettings.TG = 2406;              //  current talk group
    dmrSettings.ts_scan = false;        //
    for (int x = 0; x < 33; x++)
    {
      dmrSettings.rxTGStatus[x] = rxTGStatus[x] ;
      dmrSettings.rxTalkGroup[x] = rxTalkGroup[x];
    }
  }
  //  strcpy(WifiAp.ssid,"malmoe99");
  //  strcpy(WifiAp.passwd,"Nitton99");
  //  settingsAddWifiAp(&dmrSettings, &WifiAp, 0);
  //  strcpy(WifiAp.ssid,"jullen11");
  //  strcpy(WifiAp.passwd,"19nittionio");
  //  settingsAddWifiAp(&dmrSettings, &WifiAp, 1);
  //  strcpy(WifiAp.ssid,"Arnes iPhone");
  //  strcpy(WifiAp.passwd,"9x8z0utpnp5md");
  //  settingsAddWifiAp(&dmrSettings, &WifiAp, 2);
  Serial.print(dmrSettings.wifisettings[0].ssid);
  Serial.println(dmrSettings.wifisettings[0].passwd);
  Serial.print(dmrSettings.wifisettings[1].ssid);
  Serial.println(dmrSettings.wifisettings[1].passwd);
  Serial.print(dmrSettings.wifisettings[2].ssid);
  Serial.println(dmrSettings.wifisettings[2].passwd);
  wifiConnect();                                //Connect to WiFi
  WiFisetTime();
  EIMreadStatus();
  EIMreadRepeaters();
  EIMreadHotspots();
  DMRDebug = false;                            //tracing on Serial monitor
  NXDebug = false;
  //--------------------------------------------initiation - will be maintained on NX setup page
  //  strcpy(mySettings.callSign, "SM7ECA");
  //  mySettings.localID = 2400530;
  //  mySettings.chnr = 2;
  //  mySettings.TG = 2406;
  //  mySettings.ts_scan = false;
  audioVolume = dmrSettings.audioLevel;
  micVolume = dmrSettings.micLevel;
  curChanItem.chnr = dmrSettings.chnr;
  curChanItem.TG = dmrSettings.TG;
#ifdef INC_DMR_CALLS
  while (not DMRTransmit(FUNC_ENABLE, QUERY_INIT_FINISHED)) // Check - DMR Module running?
  {
    delay(1000);
  }
  //NXdisplayVersion();
#endif
  DMRinitChannel(curChanItem.chnr, curChanItem.TG);        // Setup initial DMR digital channel
  DMRTransmit(FUNC_ENABLE, GET_DIGITAL_CHANNEL);           // Verify digital channel set
  NX_P9_set_callsign_id();
  NX_P0_DisplayMainPage();
  NX_P0_updateRSSI(0);                                     // reset S meter on page 0
  NX_P0_showVol();                                         // update the volume display from actual DMR value
  // long int rx, tx;
  // NX_P0_DisplayCurrent();
  //stop the first beep
  beep(false);                                             // LED off - startup finished
  //-------------------------------------------------------set start values of state machine and TS scan param
  UnitState = IDLE_STATE;
  loopstart = loopstartNext = millis();
  ts_scan = dmrSettings.ts_scan;
  tsSwitchLast = millis();
  Serial.print(" Setup free heap ");
  Serial.println(ESP.getFreeHeap());
}

//************************************************************************** start main loop
//******************************************************************************************
void loop()
{
  //  Main loop and State machine
  //---------------------------------development aid - show current state on p0
  NX_P0_showState();
  //------------------------------- 0x3D start message found when reading from DMR
  if (bRecVoicemessageStart)
  {
    bRecVoicemessageStart = false;
    DMRvoicemessageStart();
  }
  //------------------------------- 0x3D stop message found when reading from DMR
  if (bRecVoicemessageEnd)
  {
    bRecVoicemessageEnd = false;
    DMRvoicemessageEnd();
  }
  //------------------------------- 0x2D message found when reading from DMR
  if (bSMSmessageReceived)
  {
    bSMSmessageReceived = false;
    UnitState = SMS_REC_STATE;
  }
  #ifdef INC_DMR_CALLS
  //------------------------------- take care of message from DMR
  if (Serial2.available() != 0)
  {
    DMRhandler();
  }
  #endif
  //-------------------------------- take care of message from Nextion
  if (Serial1.available() != 0)
  {
    NXhandler();
  }
 #ifdef INC_DMR_CALLS
  //------------------------------- state machine handling certain situations
  switch (UnitState)
  {
    case IDLE_STATE:            // 0
      do_idle();
      break;
    case TRANSMIT_STATE:        // 1
      do_transmit();
      break;
    case REC_DMR_STATE:         // 4
      do_RecDMR();
      break;
  }
#endif
}
//************************************************************************** end main loop
