//******************************************************* Normal start aequence
void IN_NormalStartup()
{
  if (wifiConnect())   //Connect to WiFi
  {
    BwifiOn = true;
  }
  WiFisetTime();
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