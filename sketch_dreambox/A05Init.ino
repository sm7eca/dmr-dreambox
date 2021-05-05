//******************************************************* Normal start aequence
void IN_NormalStartup()
{
  NXinitDisplay("WIFI connect");
  if (wifiConnect())   //Connect to WiFi
  {
    BwifiOn = true;
  }
    NXinitDisplay("Set time");
  WiFisetTime();
  audioVolume = dmrSettings.audioLevel;
  micVolume = dmrSettings.micLevel;
  curdigCh = dmrSettings.repeater[dmrSettings.chnr];
  currepTG = dmrSettings.repeater[dmrSettings.chnr].groups[dmrSettings.TG];
  NXinitDisplay("Connect to DMR-mod");
#ifdef INC_DMR_CALLS
  while (not DMRTransmit(FUNC_ENABLE, QUERY_INIT_FINISHED)) // Check - DMR Module running?
  {
    delay(1000);
  }
  //NXdisplayVersion();
#endif
  NXinitDisplay("Set DMR Channel");
  DMRinitChannel();                                        // Setup initial DMR digital channel
  DMRTransmit(FUNC_ENABLE, GET_DIGITAL_CHANNEL);           // Verify digital channel set
  NXinitDisplay("Display main page");
  NX_P9_set_callsign_id();
  NX_P0_DisplayMainPage();
  NX_P0_updateRSSI(0);                                     // reset S meter on page 0
  NX_P15_initLongLat();
  NX_P0_showVol();                                         // update the volume display from actual DMR value
  // uint32_t rx, tx;
  // NX_P0_DisplayCurrent();
  //stop the first beep
  beep(false);                                             // LED off - startup finished
  //-------------------------------------------------------set start values of state machine and TS scan param
  UnitState = IDLE_STATE;
  loopstart = loopstartNext = millis();
  ts_scan = dmrSettings.ts_scan;
  tsSwitchLast = millis();
  Terminal.print(" Setup free heap ");
  Terminal.println(ESP.getFreeHeap());

}
