#ifndef __SETTINGS_H_
#define __SETTINGS_H_
typedef struct _WifiSettingS {
  char ssid[33];
  char passwd[17];
} WifiSettingS;

typedef struct _TalkGroupS {
  uint32_t    dmrId; 
} TalkGroupS;

typedef struct _RepeaterS {
  uint8_t     zone;
  uint32_t    dmrId;        
  uint16_t    iaruChannel;        // IARU channel
  uint8_t     cc;                 // colour code
  uint8_t     timeSlot;           // 
  uint8_t     timeSlotNo;         // number of timeslots
  char        repeaterName[16];   // repeater call sign
  char        repeaterLoc[16];    // human readable location
  TalkGroupS  groups[10];
} RepeaterS;


typedef struct _RepeaterConfigS {
  RepeaterS   repeater[50];
} RepeaterConfigS;


typedef struct _DmrSettingsS {
  int           version;
  WifiSettingS  wifisettings[4];
  uint8_t       audioLevel;       //  1-9; default = 8
  uint8_t       micLevel;         //  0-15, mic gain setting
  char          callSign[12];     // callsign, max 12 chars
  uint32_t      localID;          //   DMRID
  uint8_t       chnr;             // 
  uint32_t      TG;               //  current talk group
  bool          ts_scan;          //
  uint8_t       rxTGStatus[33];   //
  uint32_t      rxTalkGroup[33];  
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
#endif
