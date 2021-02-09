
#import "EEPROM.h"
#import "Settings.h"


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