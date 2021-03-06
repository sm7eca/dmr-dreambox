
#include "EEPROM.h"
#include "Settings.h"


EepromSettings eepromContainer;

const int ADDR_SETTINGS = 0;
const int ADDR_REPEATER = ADDR_SETTINGS + sizeof(EepromSettings) + 32;
const String debugStr = "PS: ";

void settingsPrintMsg(const String msg)
{
  // helper function, print debug message
  Serial.println(debugStr + msg);
}

void settingsInit(void)
{
  //  initialize the EEPROM with the predefined size
  
  EEPROM.begin(sizeof(EepromSettings));
  settingsPrintMsg("settingsInit, finished");
}

bool settingsInitiated(void)
{
  // read start address, if flag 0x7F is visable + version > 0
  // return True

  eepromContainer.flag = 0x0000;
  eepromContainer.version = 0X0000;

  EEPROM.get(ADDR_SETTINGS, eepromContainer);
  if (eepromContainer.flag == 0x7F7F && eepromContainer.version > 0) {
    settingsPrintMsg("settingsInitiated, TRUE");
    return true;
  } else {
    Serial.println(eepromContainer.flag,HEX);
    Serial.println(eepromContainer.version,HEX);
    settingsPrintMsg("settingsInitiated, FALSE");
    return false;
  }

}

void settingsRead(DmrSettingsS* dmrSettings)
{
  settingsPrintMsg("settingsRead, start");

  eepromContainer.flag = 0x0000;
  eepromContainer.version = 0x0000;

  // read from EEPROM
  EEPROM.get(ADDR_SETTINGS, eepromContainer);
  
  // copy application settings into container
  memcpy(dmrSettings, &eepromContainer.settings, sizeof(DmrSettingsS));

  settingsPrintMsg("settingsRead, finished");
}

void settingsWrite(DmrSettingsS *dmrSettings)
{
  // write settings into the EEPROM
  // encapsulated into container
  settingsPrintMsg("settingsWrite, start");

  eepromContainer.flag = 0x7F7F;
  eepromContainer.version = 0x0001;

  memcpy(&eepromContainer.settings, dmrSettings, sizeof(DmrSettingsS));

  EEPROM.put(ADDR_SETTINGS, eepromContainer);
  EEPROM.commit();

  settingsPrintMsg("settingsWrite, finished");
}

void settingsAddWifiAp(DmrSettingsS* dmrSettings, WifiSettingS* wifiAp, int slot)
{
  // write AP settings into a distinct slot
  settingsPrintMsg("settingsWriteWifi, start");

  if (slot >= SETTINGS_MAX_WIFI_AP) {
    settingsPrintMsg("settingsWriteWifi, failed => invalid slot");
    return;
  }

  // erase that wifi slot
  memset(dmrSettings->wifisettings[slot].ssid, 0, SETTINGS_WIFI_SSID_LEN);
  memset(dmrSettings->wifisettings[slot].passwd, 0, SETTINGS_WIFI_PASSWD_LEN);

  // copy new items
  memcpy(dmrSettings->wifisettings[slot].ssid, wifiAp->ssid, SETTINGS_WIFI_SSID_LEN);
  memcpy(dmrSettings->wifisettings[slot].passwd, wifiAp->passwd, SETTINGS_WIFI_PASSWD_LEN);

  settingsPrintMsg("settingsWriteWifi, finished");
}
