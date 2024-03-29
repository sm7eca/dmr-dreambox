
#ifndef SETTINGS_H
#define SETTINGS_H

#define SETTINGS_WIFI_SSID_LEN 32
#define SETTINGS_WIFI_PASSWD_LEN 16

typedef struct _WifiSettingS {
  char ssid[SETTINGS_WIFI_SSID_LEN + 1];
  char passwd[SETTINGS_WIFI_PASSWD_LEN + 1];
} WifiSettingS;

typedef struct _TalkGroupS {
  uint32_t    tg_id;
  uint8_t     ts;
} TalkGroupS;

typedef struct _RepeaterS {
  uint8_t     zone;
  uint32_t    dmrId;
  uint32_t    tx;                 // tx freq
  uint32_t    rx;                 // rx freq
  uint8_t     cc;                 // colour code
  uint8_t     timeSlot;           //
  uint8_t     timeSlotNo;         // number of timeslots
  char        repeaterName[16];   // repeater call sign
  char        repeaterLoc[16];    // human readable location
  TalkGroupS  groups[10];
  uint8_t     chnr;               // channel no
} RepeaterS;

#define SETTINGS_MAX_WIFI_AP 4
#define SETTINGS_MAX_NUM_MANUAL_REPEATERS 4
#define SETTINGS_MAX_NUM_REPEATERS 25

//typedef struct _RepeaterConfigS {
//  RepeaterS   repeater[30];
//} RepeaterConfigS;


typedef struct _DmrSettingsS {
  uint16_t           version;
  WifiSettingS  wifisettings[SETTINGS_MAX_WIFI_AP];
  uint8_t       audioLevel;       //  1-9; default = 8
  uint8_t       micLevel;         //  0-15, mic gain setting
  char          callSign[12];     // callsign, max 12 chars
  uint32_t      localID;          //   DMRID
  char          longitude[11];    // saved from last location search
  char          latitude[11];     // "
  uint16_t      distance;         // "
  char          qthloc[9];        // qth locator for future use
  uint8_t       chnr;             //  current channel
  uint32_t      TG;               //  current talk group
  bool          ts_scan;          //
  uint8_t       rxTGStatus[33];   //
  uint32_t      rxTalkGroup[33];
  RepeaterS     repeater[SETTINGS_MAX_NUM_REPEATERS];
} DmrSettingsS;


typedef struct _EepromSettings {
  uint16_t      flag;
  uint16_t      version;
  DmrSettingsS  settings;
} EepromSettings;


// initiate persistent settings
void settingsInit(void);

// check whether settings exist in EEPROM
bool settingsInitiated(void);

// write EEPROM with new settings
void settingsWrite(DmrSettingsS* dmrSettings);

// read settings from EEPROM into dmrSettings
void settingsRead(DmrSettingsS* dmrSettings);

// write wifi settings into to a distinct slot
void settingsAddWifiAp(DmrSettingsS* dmrSettings, WifiSettingS* wifiAp, uint8_t slot);

void  NXinitDisplay(const String msg);
void  NXinitialSetup();
void  NXdimdisplay(uint8_t func);
void  NX_P0_showState();
void  NX_P0_DisplayMainPage();
void  NX_P0_DisplayReceive(boolean rec_on, byte calltype, uint32_t TGId);
void  NX_P0_DisplayTransmit(boolean on);
void  NX_P0_DisplayCurrentTS();
void  NX_P8_viewSMS(String rxContactChar, String SMStext);
void  NX_P9_set_callsign_id();
void  NX_P0_updateRSSI(uint8_t rssi);
void  NX_P0_showVol();
boolean  wifiConnect();
void  WiFisetTime();
boolean  EIMreadStatus();
void  EIMreadRepeaters();
void  EIMreadHotspots();
boolean EIMreadRepeaterDMRid(char* DMRid, uint8_t k);
boolean EIMreadRepeatersLocation(char* longitude, char* latitude, int distance);
void  EIMeraseRepHotspot(uint8_t k);
void  EIMprintDMRsettingsitem(uint8_t k);
void  NXhandler();
void  wifiGetDMRID();
void DMRinitChannel();


#endif /* SETTINGS_H */
