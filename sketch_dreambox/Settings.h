
#ifndef SETTINGS_H
#define SETTINGS_H

#define SETTINGS_WIFI_SSID_LEN 32
#define SETTINGS_WIFI_PASSWD_LEN 16

typedef struct _WifiSettingS {
  char ssid[SETTINGS_WIFI_SSID_LEN + 1];
  char passwd[SETTINGS_WIFI_PASSWD_LEN + 1];
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

#define SETTINGS_MAX_WIFI_AP 4


typedef struct _RepeaterConfigS {
  RepeaterS   repeater[50];
} RepeaterConfigS;


typedef struct _DmrSettingsS {
  int           version;
  WifiSettingS  wifisettings[SETTINGS_MAX_WIFI_AP];
  uint8_t       audioLevel;       //  1-9; default = 8
  uint8_t       micLevel;         //  0-15, mic gain setting
  char          callSign[12];     // callsign, max 12 chars
  uint32_t      localID;          //   DMRID
  uint8_t       chnr;             //
  uint32_t      TG;               //  current talk group
  bool          ts_scan;          //
  uint8_t       rxTGStatus[33];   //
  uint32_t      rxTalkGroup[33];
  RepeaterS     repeater[100];
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
void settingsAddWifiAp(DmrSettingsS* dmrSettings, WifiSettingS* wifiAp, int slot);

#endif /* SETTINGS_H */
