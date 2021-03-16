//========================================================================== startup
void NXend(int nr);

void NX_P3_statusDisplay(const String msg)
{
  Serial1.print("DMRlogga.t0");
  Serial1.print(".txt=");
  Serial1.print("\"");
  Serial1.print(msg);
  Serial1.print("\"");
  NXend(300);
}
void NXinitDisplay(const String msg)
//----------------------------------------------------- NXinitDisplay
//    start Nextion Screen
{
  Serial1.print("page 3");   //page 3
  NXend(2);
  NX_P3_statusDisplay(msg);
}
void NXinitialSetup()
//----------------------------------------------------------- Initial setup screen (
//
{
  Serial1.print("page 13");
  NXend(201);
}
//========================================================================== page 0
void NX_P0_DisplayMainPage()
//----------------------------------------------------------- DisplayMainPage
//
{
  Serial1.print("page main");
  NXend(24);
}
void NX_P0_DisplayCurrent()
//----------------------------------------------------------- DisplayCurrent
//
{
  // ---- input to display on "channel screen"
  //prepare those strings
  String tempS = String(digData.rx_freq);
  String fR = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
  tempS = String(digData.tx_freq);
  String fT = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
  String fullName = String(curdigCh.Name) + " " + String(curdigCh.Location);
  fullName.trim();
  String firstBlock = String(dmrSettings.localID);
  Serial1.print("main.t0.txt=\"");
  Serial1.print(firstBlock);
  Serial1.print("\"");
  NXend(8);
  Serial1.print("main.t2.txt=\"");
  Serial1.print(fullName);
  Serial1.print("\"");
  NXend(9);
  Serial1.print("main.t3.txt=\"");
  Serial1.print(dmrSettings.callSign);
  Serial1.print("\"");
  NXend(4);
  //these lines are for "TX:444.88250"
  Serial1.print("main.t5.txt=\"");
  Serial1.print(fT);
  Serial1.print("\"");
  NXend(10);
  switch (digData.power)
  {
    case 0:
      Serial1.print("main.t4.txt=\"1 W\"");
      break;
    case 1:
      Serial1.print("main.t4.txt=\"5 W\"");
      break;
    default:
      Serial1.print("main.t4.txt=\"1 W\"");
      break;
  }
  NXend(11);
  //these for large receiving frequency
  Serial1.print("main.t6.txt=\"");
  Serial1.print(fR.substring(0, 7));
  Serial1.println(fR.substring(7, 9));
  Serial1.print("\"");
  NXend(12);
  NX_P0_updateTXinfo();
}
void NX_P0_updateTXinfo()
//----------------------------------------------------------- updateTXinfo
//
//these lines are for "tx_group TSlot ColorCode"));
{
  switch (digData.ContactType)
  {
    case 0:
      Serial1.print("main.t1.txt=\"Individual\"");
      break;
    case 1:
      Serial1.print("main.t1.txt=\"Group Call\"");
      break;
    default:
      Serial1.print("main.t1.txt=\"Group Call\"");
      break;
  }
  NXend(13);
  Serial1.print("main.n5.val=");
  Serial1.print(digData.tx_contact);
  NXend(14);
  NX_P0_DisplayCurrentTS();
  Serial1.print("main.n3.val=");
  Serial1.print(digData.cc);
  NXend(16);
}
void  NX_P0_DisplayCurrentTS()
//----------------------------------------------------------- DisplayCurrentTS
//
{
  Serial1.print("main.n2.val=");
  Serial1.print(digData.InboundSlot + 1);
  NXend(15);
}
void  NX_P0_DisplayTransmit(boolean on)
//----------------------------------------------------------- DisplayTransmit
//
{
  // ---- input to display on "channel screen"
  String tempS, rxS;
  if (on)
  {
    tempS = String(digData.rx_freq);
    tempS = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
    Serial1.print("main.t5.txt=\"");
    Serial1.print(tempS);
    Serial1.print("\"");
    NXend(17);
    Serial1.print("main.t7.txt=\"on air\"");
    NXend(18);
    rxS = String(digData.tx_freq);
    Serial1.print("main.t6.txt=\"");
    Serial1.print(rxS.substring(0, 3));
    Serial1.print(F("."));
    Serial1.print(rxS.substring(3, 6));
    Serial1.print(rxS.substring(6, 40));
    Serial1.print("\"");
    NXend(19);
  }
  else
  {
    tempS = String(digData.tx_freq);
    tempS = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
    Serial1.print("main.t5.txt=\"");
    Serial1.print(tempS);
    Serial1.print("\"");
    NXend(20);
    Serial1.print("main.t7.txt=\"idle\""); // to erase the "on"
    NXend(21);
    rxS = String(digData.rx_freq);
    Serial1.print("main.t6.txt=\"");
    Serial1.print(rxS.substring(0, 3));
    Serial1.print(F("."));
    Serial1.print(rxS.substring(3, 6));
    Serial1.print(rxS.substring(6, 40));
    Serial1.print("\"");
    NXend(23);
  }
}
void NX_P0_DisplayReceive(boolean rec_on, byte calltype, uint32_t TGId)
//----------------------------------------------------------- DisplayReceive
//
{
  if (rec_on)
  {
    Serial1.print("main.t7.txt=\"mon\"");
    NXend(23);
    Serial1.print("main.t10.txt=\"");
    Serial1.print(rxGroup);
    Serial1.print("\"");
    //    switch (calltype)
    //    {
    //    case 0:
    //      Serial1.print("main.t10.txt=\"Individual\"");
    //      break;
    //    case 1:
    //      Serial1.print("main.t10.txt=\"Group Call\"");
    //      break;
    //    default:
    //      Serial1.print("main.t10.txt=\"Group Call\"");
    //      break;
    //    }
    NXend(24);
    Serial1.print("main.n4.val=");
    Serial1.print(TGId);
    NXend(25);
    if (WIFIcallfound)
    {
      Serial1.print("main.t12.txt=\"");
      Serial1.print(ri_callsign);
      Serial1.print("\"");
      NXend(26);
      Serial1.print("main.t17.txt=\"");
      Serial1.print(ri_fname);
      Serial1.print(",");
      if (ri_surname != "null")
      {
        Serial1.print(ri_surname);
        Serial1.print(",");
      }
      Serial1.print(ri_city);
      Serial1.print("\"");
      NXend(27);
      Serial1.print("main.t18.txt=\"");
      if (ri_state.length() != 0)
      {
        Serial1.print(ri_state);
        Serial1.print(",");
      }
      Serial1.print(ri_country);
      Serial1.print("\"");
      NXend(27);
    }
    else
    {
      Serial1.print("main.t12.txt=\"");
      Serial1.print("-- ");
      Serial1.print("\"");
      NXend(28);
      Serial1.print("main.t17.txt=\"");
      Serial1.print(" ");
      Serial1.print("\"");
      NXend(29);
      Serial1.print("main.t18.txt=\"");
      Serial1.print(" ");
      Serial1.print("\"");
      NXend(29);
    }
  }
  else
  {
    //    Serial1.print("main.t10.txt=\"Last\""); Ska kanske vara byte av färg istället?
    //    NXend(30);
    Serial1.print("main.t7.txt=\"idle\"");
    NXend(31);
    //   Serial1.print("main.t8.txt=\"     \"");
    //   NXend(31);
  }
}
void NX_P0_updateRSSI(uint8_t rssi)
//----------------------------------------------------- NX_P0_updateRSSI

{
  Serial1.print("main.j1.val="); // Changing the value of box n1
  uint8_t rssiproc = (100 * rssi) / 33;
  Serial1.print(rssiproc); // show set volume level
  NXend(23);
}
void NX_P0_showVol()
//----------------------------------------------------- NXshowVol

{
  Serial1.print("main.j0.val="); // Changing the value of progress bar
  int volproc = (100 * (audioVolume - 1)) / (maxAudioVolume - 1);
  Serial1.print(volproc); // show set volume level
  NXend(22);
}

void  NX_P0_showState()
//----------------------------------------------------- NX_P0_showState
//
// optimized - only update when changed
{
  if (UnitState != lastUnitState)
  {
    Serial1.print("main.n0.val="); // Changing the value of box n0
    Serial1.print(UnitState);
    NXend(6);
    lastUnitState = UnitState;
  }
  //  looptime = millis()-loopstartNext;
  //  loopstartNext = millis();
  //  if (abs(looptime)>150)
  //  {
  //    Serial1.print("main.n1.val="); // Changing the value of box n1
  //    Serial1.print(looptime); // show loop time
  //    NXend(7);
  //  }
  //  looptimelast = looptime;
}
//========================================================================== page 4

void  NX_P4_displayChannels()
//----------------------------------------------------------- displayChannel
//
// fill the channel screen
{
  int curRow = 0;
  p4_eof = false;
  p4_startRecord = p4_curPage * p4_numRows;
  for (curRow = 0; curRow < p4_numRows; curRow++)
  {
    if (digChlist[curRow + p4_startRecord].DMRid == 9999999)
    {
      p4_eof = true;
    }
    if (digChlist[curRow + p4_startRecord].DMRid != 0 and !p4_eof)
    {
      Serial1.print("b");
      Serial1.print(curRow);
      Serial1.print(".txt=");
      Serial1.print("\"");
      Serial1.print(digChlist[curRow + p4_startRecord].Name);
      Serial1.print(" ");
      Serial1.print(digChlist[curRow + p4_startRecord].Location);
      Serial1.print(" (");
      Serial1.print(String(digChlist[curRow + p4_startRecord].DMRid));
      Serial1.print(")");
      Serial1.print("\"");
      NXp4Ch[curRow] = digChlist[curRow + p4_startRecord];
      NXend(23);
    }
    else
    {
      Serial1.print("b");
      Serial1.print(curRow);
      Serial1.print(".txt=");
      Serial1.print("\"");
      Serial1.print(" ");
      Serial1.print("\"");
      p4_eof = true;
      NXend(24);
    }
  }
}
//========================================================================== page 5
void  NX_P5_displayTGlist()
//----------------------------------------------------------- displayChannel
//
// A channel is selected on page 4 - now list TGs
{

  //------------- display page header
  String fullName = String(NXp4Ch[p4_selectedRow].Name) + " " + String(NXp4Ch[p4_selectedRow].Location);
  fullName.trim();
  Serial1.print("t0.txt=");
  Serial1.print("\"");
  Serial1.print(fullName);
  Serial1.print("\"");
  NXend(26);
  //--------------- display static TGs connected to channel - max p5_numRows on a page
  int curRow = 0;
  p5_eof = false;
  uint32_t P4DMRid = NXp4Ch[p4_selectedRow].DMRid;
  p5_startRecord = p5_lastRecord + 1;
  for (int i = p5_startRecord; i < maxrepTGlist; i++)
  {
    if (repTGlist[i].DMRid == 9999999)
    {
      p5_eof = true;
    }
    if (repTGlist[i].DMRid == P4DMRid and !p5_eof)
    {
      Serial1.print("b");
      Serial1.print(curRow);
      Serial1.print(".txt=");
      NXp5repTG[curRow] = repTGlist[i];
      Serial1.print("\"");
      Serial1.print(String(repTGlist[i].TG));
      Serial1.print(" ");
      if (DBgetTG(repTGlist[i].TG))
      {
        Serial1.print(curTG.TGname);
        NXp5TG[curRow] = curTG;
      }
      Serial1.print(" ts:");
      Serial1.print(String(repTGlist[i].TS));
      Serial1.print("\"");
      NXend(23);
      if (curRow < p5_numRows - 1)
      {
        curRow++;
      }
      else
      {
        p5_lastRecord = i;
        return;
      }
    }
  }
  for (int i = curRow; i < p5_numRows; i++) // if page not filled blank out the rest
  {
    Serial1.print("b");
    Serial1.print(i);
    Serial1.print(".txt=");
    Serial1.print("\"");
    Serial1.print(" ");
    Serial1.print("\"");
    p5_eof = true;
    NXend(25);
  }
}
void NX_P5_buttonHandler()
//----------------------------------------- P5_buttonHandler
{
  if (NXbuff[2] == 0x19)
  {
    // --- scroll back to first page
    p5_lastRecord = -1;
    Serial1.print("TGlist.va0.val=1");
    NXend(50);
    Serial1.print("page 5");
    NXend(51);
  }
  if (NXbuff[2] == 0x20)
  {
    if (!p5_eof)
    {
      Serial1.print("TGlist.va0.val=1");
      NXend(52);
      Serial1.print("page 5");
      NXend(53);
    }
  }
  if (NXbuff[2] < 18)   // ---- Channel selected
  {
    Serial1.print("TGlist.va0.val=0");
    NXend(54);
    p5_lastRecord = -1; // ----- reset scroll page
    if (NXbuff[3] == 1)
    {
      curChanItem.chnr = NXp4Ch[p4_selectedRow].chnr;
      curChanItem.TG = NXp5repTG[NXbuff[2]].TG;
      digData.tx_contact = NXp5repTG[NXbuff[2]].TG;
      digData.ContactType = NXp5TG[NXbuff[2]].calltype;
      DMRinitChannel(curChanItem.chnr, curChanItem.TG);
      Serial1.print("page 0");
    }
    else
    {
      dmrSettings.chnr = NXp4Ch[p4_selectedRow].chnr;
      dmrSettings.TG = NXp5repTG[NXbuff[2]].TG;
      settingsWrite(&dmrSettings);
      Serial1.print("page 9");
    }
    NXend(55);
  }
}
//========================================================================== page 6
void NX_P6_displayTG()
//----------------------------------------------------------------------------NX_P6_display
{
  int recnr = 0;
  p6_eof = false;
  p6_startRecord = p6_curPage * p6_numRows;
  for (recnr = 0; recnr < p6_numRows; recnr++)
  {
    if (TGlist[recnr + p6_startRecord].TG == 9999999)
    {
      p6_eof = true;
    }
    if (TGlist[recnr + p6_startRecord].TG != 0 and !p6_eof)
    {
      Serial1.print("b");
      Serial1.print(recnr);
      Serial1.print(".txt=");
      Serial1.print("\"");
      // Serial1.print(String(recnr+p6_startRecord));
      // Serial1.print(" ");
      Serial1.print(TGlist[recnr + p6_startRecord].TG);
      Serial1.print(" ");
      Serial1.print(TGlist[recnr + p6_startRecord].TGname);
      Serial1.print("\"");
      NXp6TG[recnr] = TGlist[recnr + p6_startRecord];
      NXend(33);
    }
    else
    {
      Serial1.print("b");
      Serial1.print(recnr);
      Serial1.print(".txt=");
      Serial1.print("\"");
      Serial1.print(" ");
      Serial1.print("\"");
      p6_eof = true;
      NXend(34);
    }
  }

}
//========================================================================== page 8
void NX_P8_viewSMS(String rxContactChar, String SMStext)
{
  Serial1.print("page recSMS");
  NXend(82);
  char combinedArray[sizeof(rxContactChar) + sizeof(ri_callsign) + 3];
  sprintf(combinedArray, "%s %s", rxContactChar, ri_callsign); // with word space
  Serial1.print("t11.txt=");
  Serial1.print("\"");
  Serial1.print(String(combinedArray));
  Serial1.print("\"");
  NXend(80);
  //  String SMStext ="fglkj lkjdf gkj dfgkj ödjsf göj dsöfgj sdöfgj södfgj sdlfk60";
  Serial1.print("t0.txt=");
  Serial1.print("\"");
  Serial1.print(SMStext);
  Serial1.print("\"");
  NXend(81);
}
//========================================================================== page 9
void NX_P9_displaySSID()
{
  Serial1.print("setup.t11.txt=\"");
  Serial1.print(dmrSettings.wifisettings[0].ssid);
  Serial1.print("\"");
  NXend(900);
  Serial1.print("setup.t12.txt=\"");
  Serial1.print(dmrSettings.wifisettings[0].passwd);
  Serial1.print("\"");
  NXend(910);
  Serial1.print("setup.t13.txt=\"");
  Serial1.print(dmrSettings.wifisettings[1].ssid);
  Serial1.print("\"");
  NXend(901);
  Serial1.print("setup.t14.txt=\"");
  Serial1.print(dmrSettings.wifisettings[1].passwd);
  Serial1.print("\"");
  NXend(911);
  Serial1.print("setup.t15.txt=\"");
  Serial1.print(dmrSettings.wifisettings[2].ssid);
  Serial1.print("\"");
  NXend(902);
  Serial1.print("setup.t16.txt=\"");
  Serial1.print(dmrSettings.wifisettings[2].passwd);
  Serial1.print("\"");
  NXend(912);
  Serial1.print("setup.t18.txt=\"");
  Serial1.print(dmrSettings.wifisettings[3].ssid);
  Serial1.print("\"");
  NXend(903);
  Serial1.print("setup.t19.txt=\"");
  Serial1.print(dmrSettings.wifisettings[3].passwd);
  Serial1.print("\"");
  NXend(913);

}
void NX_P9_set_callsign_id()
{
  Serial1.print("setup.t8.txt=\"");
  Serial1.print(dmrSettings.callSign);
  Serial1.print("\"");
  NXend(90);
  Serial1.print("setup.n9.val=");
  Serial1.print(dmrSettings.localID);
  NXend(91);
}
void NX_P9_set_channelinfo()
//---------------------------------------------------------- get channelinfo from dmrSettings
{
  String fullName = String(digChlist[dmrSettings.chnr].Name) + " " + String(digChlist[dmrSettings.chnr].Location);
  fullName.trim();
  Serial1.print("setup.t2.txt=\"");
  Serial1.print(fullName);
  Serial1.print("\"");
  NXend(92);
  Serial1.print("setup.n2.val=");
  Serial1.print(dmrSettings.TG);
  NXend(93);

}
void NX_P9_displayVersion()
//----------------------------------------------------------- displayVersion
//
// Display software version from current code module
// Query DMR module version and display on oled, last line (unused for now)
{

  Serial1.print("t6.txt=\"");
  Serial1.print(SoftwareVersion);
  Serial1.print("\"");
  NXend(94);
#ifdef INC_DMR_CALLS
  if (DMRgetVersion())
  {
    char ModuleVersion[19] = "                  ";
    for (int x = 8; x < 26; x++)
    {
      ModuleVersion[x - 8] = char(buff[x]);
    }
    //    ModuleVersion[18] = 0x0;
    Serial1.print("t7.txt=\"");
    Serial1.print(ModuleVersion);
    Serial1.print("\"");
    NXend(95);
  }
#endif
}
void NX_P9_showVol()
//----------------------------------------------------- NXshowVol

{
  Serial1.print("j0.val="); // Changing the value of progress bar
  int volproc = (100 * (dmrSettings.audioLevel - 1)) / (maxAudioVolume - 1);
  Serial1.print(volproc); // show set volume level
  NXend(96);
}
void NX_P9_showMicVol()
//----------------------------------------------------- NXshowVol

{
  Serial1.print("j1.val="); // Changing the value of progress bar
  int volproc = (100 * dmrSettings.micLevel) / maxMicVolume;
  Serial1.print(volproc); // show set volume level
  NXend(97);
}
void NX_P9_getCallsign()
//------------------------------------------------------NX_P9_getCallsign
{
  for (int x = 0; x < 10; x++)
  {
    if (NXbuff[x + 3] == 0xFF)
    {
      dmrSettings.callSign[x] = 0x00;
      break;
    }
    if (NXbuff[x + 3] != 0x20)
    {
      dmrSettings.callSign[x] = NXbuff[x + 3];
    }
  }
  settingsWrite(&dmrSettings);
}
void NX_P9_getDMRid()
//------------------------------------------------------NX_P9_getDMRid
{
  dmrSettings.localID =  (uint32_t)NXbuff[5] << 16 | (uint32_t)NXbuff[4] << 8 | (uint32_t)NXbuff[3];
  settingsWrite(&dmrSettings);
}
void  NX_P9_saveSSID(int indx)
//------------------------------------------------------NX_P9_saveSSID
{
  char tmp[16];
  for (int x = 0; x < 16; x++)
  {
    if (NXbuff[x + 3] == 0xFF)
    {
      tmp[x] = 0x00;
      break;
    }
    tmp[x] = NXbuff[x + 3];
  }
  strcpy(WifiAp.passwd, dmrSettings.wifisettings[indx].passwd);
  strcpy(WifiAp.ssid, tmp);
  settingsAddWifiAp(&dmrSettings, &WifiAp, indx);
  settingsWrite(&dmrSettings);
}

void  NX_P9_savePasswd(int indx)
//------------------------------------------------------NX_P9_savePasswd
{
  char tmp[16];
  for (int x = 0; x < 16; x++)
  {
    if (NXbuff[x + 3] == 0xFF)
    {
      tmp[x] = 0x00;
      break;
    }
    tmp[x] = NXbuff[x + 3];
  }
  strcpy(WifiAp.ssid, dmrSettings.wifisettings[indx].ssid);
  strcpy(WifiAp.passwd, tmp);
  settingsAddWifiAp(&dmrSettings, &WifiAp, indx);
  settingsWrite(&dmrSettings);
}
//========================================================================== page 10
void NX_P10_rxLastHeard()
{
  int k = 0;
  for (int i = 0; i < numradioid; i++)
  {
    k++;
    Serial1.print("t");
    Serial1.print(k);
    Serial1.print(".txt=");
    Serial1.print("\"");
    Serial1.print(ri_list[i].ri_talkgroup);
    Serial1.print(" ");
    Serial1.print(ri_list[i].ri_id);
    Serial1.print(" ");
    Serial1.print(ri_list[i].ri_callsign);
    Serial1.print(" ");
    Serial1.print(ri_list[i].ri_fname);
    Serial1.print(" ");
    Serial1.print(ri_list[i].ri_city);
    Serial1.print(" :");
    Serial1.print(ri_list[i].ri_count);
    Serial1.print("\"");
    NXend(30);
    if (k > 9)
    {
      break;
    }
  }
}
//========================================================================= page 14
void NX_P14_getRepeaterDMRid()
//-----------------------------------------------------P14_getRepeaterDMRid()
{
  int k = 0;
  char repeaterIDChar[10];
  uint32_t repeaterID;
  if (NXbuff[6] == 0x0)
  {
    repeaterID =  (uint32_t)NXbuff[5] << 16 | (uint32_t)NXbuff[4] << 8 | (uint32_t)NXbuff[3];
  }
  else
  {
    repeaterID = (uint32_t)NXbuff[6] << 24 | (uint32_t)NXbuff[5] << 16 |
                 (uint32_t)NXbuff[4] << 8 | (uint32_t)NXbuff[3];
  }
//  Serial.println(repeaterID);
  ltoa(repeaterID, repeaterIDChar, 10);
  switch (NXbuff[2])
  {
    case 0x02:
      k = 0;
      break;
    case 0x04:
      k = 1;
      break;
    case 0x06:
      k = 2;
      break;
    case 0x08:
      k = 3;
      break;
//    case 0x0A:
//      k = 4;
//      break;
//    case 0x0C:
//      k = 5;
//      break;
//    case 0x0E:
//      k = 6;
//      break;
  }
  if (repeaterID != 0)
  {
    //    EIMreadStatus();
    EIMreadRepeaterDMRid(repeaterIDChar, k);
    NXrepeaterName[29] = 0x0;
  }
  else
  {
    EIMeraseRepHotspot(k);
    NXrepeaterName[0] = 0x0;
  }
  settingsWrite(&dmrSettings);


  Serial1.print("n");
  Serial1.print(k);
  Serial1.print(".val=");
  Serial1.print(repeaterID);
  NXend(142);

  Serial1.print("t");
  Serial1.print(k);
  Serial1.print(".txt=");
  Serial1.print("\"");
  Serial1.print(NXrepeaterName);
  Serial1.print("\"");
  NXend(140);
}

void  NX_P14_fillRepeaterlist()
//---------------------------------------------------------------------P14_fillRepeaterlist
{
  for (int k = 0; k < numManualRep; k++)
  {
    Serial1.print("n");
    Serial1.print(k);
    Serial1.print(".val=");
    Serial1.print(dmrSettings.repeater[k].dmrId);
    NXend(141);
    char charTmp[40] = "";
    if (dmrSettings.repeater[k].dmrId != 0)
    {
      sprintf(charTmp, "%s,%s", dmrSettings.repeater[k].repeaterName, dmrSettings.repeater[k].repeaterLoc);
      charTmp[29] = 0x0;
    }
    Serial1.print("t");
    Serial1.print(k);
    Serial1.print(".txt=");
    Serial1.print("\"");
    Serial1.print(charTmp);
    Serial1.print("\"");
    NXend(142);
  }
}
void NX_P14_updateRepHotspotDB(int first, int last)
//---------------------------------------------------------------------
{
  int i = 0;
  int j = 0;
  int j_start = 0;
  int n = 0;
  for (int k=first; k < last; k++)
  {
    if (dmrSettings.repeater[k].dmrId != 0)
    {
      digChlist[i].zone = dmrSettings.repeater[k].zone;                       //zone no = collection of repeaters or hotspots, not used yet
      digChlist[i].chnr = i;                                                  //internal channel for sorting and scrolling
      digChlist[i].DMRid = dmrSettings.repeater[k].dmrId;                     //DMRid för repeater eller Hotspot
      digChlist[i].tx = dmrSettings.repeater[k].tx;                           // tx freq
      digChlist[i].rx = dmrSettings.repeater[k].rx;                           // rx freq
      digChlist[i].cc = dmrSettings.repeater[k].cc;                           //color code0~15
      digChlist[i].TimeSlot = dmrSettings.repeater[k].timeSlot;               //0:slot 1 1:slot 2  TS numbering like the 22 command states (Current time slot when active)
      digChlist[i].TimeSlotNo = dmrSettings.repeater[k].timeSlotNo;           //number of time slots 1 or 2.
      digChlist[i].ChannelMode = 0;                                           //0:direct connection mode 4: true dual slot (DMR tier 2)
      strcpy(digChlist[i].Name, dmrSettings.repeater[k].repeaterName);    //name of the channel, 14 chars
      strcpy(digChlist[i].Location, dmrSettings.repeater[k].repeaterLoc); //location of device Hotspot or repeater, 14 chars
      i++;
      for (j = 0; j < 10; j++)
      {
        if (dmrSettings.repeater[k].groups[j].tg_id != 0)
        {
          repTGlist[n].DMRid = dmrSettings.repeater[k].dmrId;
          repTGlist[n].TG = dmrSettings.repeater[k].groups[j].tg_id;
          repTGlist[n].TS = dmrSettings.repeater[k].groups[j].ts;
          n++;
        }
      }
    }
  }
  digChlist[i].zone = 0;
  digChlist[i].chnr = 255;
  digChlist[i].DMRid = 0;
  digChlist[i].tx = 0;
  digChlist[i].rx = 0;
  digChlist[i].cc = 0;
  digChlist[i].TimeSlot = 0;
  digChlist[i].TimeSlotNo = 0;
  digChlist[i].ChannelMode = 0;
  strcpy(digChlist[i].Name, "");
  strcpy(digChlist[i].Location, "");
  repTGlist[n].DMRid = 9999999;
  repTGlist[n].TG = 0;
  repTGlist[n].TS = 0;
  maxdigChlist = i - 1;
  maxrepTGlist = n - 1;
}
void NX_P15_getInput()
//---------------------------------------------------------------------
{
  switch (NXbuff[2])
  {
    case 0x16:
      for (int x = 0; x < 10; x++)
      {
        if (NXbuff[x + 3] == 0xFF)
        {
          p15_long[x] = 0x00;
          break;
        }
        if (NXbuff[x + 3] != 0x20)
        {
          p15_long[x] = NXbuff[x + 3];
        }
      }
      Serial.print("p15_long ");
      Serial.println(p15_long);
      break;
    case 0x17:
      for (int x = 0; x < 10; x++)
      {
        if (NXbuff[x + 3] == 0xFF)
        {
          p15_lat[x] = 0x00;
          break;
        }
        if (NXbuff[x + 3] != 0x20)
        {
          p15_lat[x] = NXbuff[x + 3];
        }
      }
      Serial.println("p15_lat ");
      Serial.println(p15_lat);
      break;
    case 0x14:
      p15_dist = (uint32_t)NXbuff[6] << 24 | (uint32_t)NXbuff[5] << 16 |
                 (uint32_t)NXbuff[4] << 8 | (uint32_t)NXbuff[3];
      Serial.println("p15_dist ");
      Serial.println(p15_dist);
      break;
  }
}

void NX_P15_initPage()
//---------------------------------------------------------------------
{

}

void  NX_P15_fillRepeaterlist()
//---------------------------------------------------------------------
{
  if (!EIMreadRepeatersLocation(p15_long, p15_lat, p15_dist))
  {
    reptemplistCurLen = 0;
  }
  for (int i = 0; i < p15_numRows; i++)
  {
    strcpy(NXrepeaterName, "");
    if (i <= reptemplistCurLen)
    {
      //       sprintf(NXrepeaterName, "%d-%s,%s", reptemplist[i].dmrId, reptemplist[i].repeaterName, reptemplist[i].repeaterLoc);
      sprintf(NXrepeaterName, "%s,%s", reptemplist[i].repeaterName, reptemplist[i].repeaterLoc);
      NXrepeaterName[25] = 0x0;
    }
    Serial1.print("t");
    Serial1.print(i + 20);
    Serial1.print(".txt=");
    Serial1.print("\"");
    Serial1.print(NXrepeaterName);
    Serial1.print("\"");
    NXend(150);
  }

}
void  NX_P15_saveRepeaterlist()
//---------------------------------------------------------------------
//  the repeaters that are dynamically assigned reside i slot 4-18 of the setting.repeater-list.
//  Slot 0-4 are reserved for manually entered hotspots or repeaters.
//  If a repeater is saved manually it will not be include in the dynamic list.
//  For each repeater in the templist a call to EIM is made in order to find the associated Talkgroups.
//  If the temporary repeaterlist is empty nothing is changed.
{
  char repeaterIDChar[10];
  int t=reptemplistCurLen;
  if (reptemplistCurLen = 0)
  {
    return;
  }
  if (!EIMreadStatus())
  {
    return;
  }
  
  int j = numManualRep;
  int k;
  boolean manualfound = false;
  for (int i = 0; i <= t; i++)
  {
//    Serial.println(i);
//    Serial.println(reptemplist[i].dmrId);
//    Serial.println(t);
    manualfound = false;
    for (k = 0; k < numManualRep; k++)
    {
      if (dmrSettings.repeater[k].dmrId == reptemplist[i].dmrId)
      {
        manualfound = true;
      }
    }
    if (!manualfound)
    {
      ltoa(reptemplist[i].dmrId, repeaterIDChar, 10);
      EIMreadRepeaterDMRid(repeaterIDChar, j);
      j++;
    }
  }
  for (int i=t+t; i < maxRepeaters; i++)              // if you want to zero the repeater list
  {
    dmrSettings.repeater[i].zone  = 0;
    dmrSettings.repeater[i].dmrId = 0;
  }
//  for (int i=0;i<=maxRepeaters;i++)
//  {
//   EIMprintDMRsettingsitem(i);
//  }
  settingsWrite(&dmrSettings);
  NX_P14_updateRepHotspotDB(0,maxRepeaters);
//  DBprintChannels();
}
//========================================================================== field or button touch
void NX_txtfield_touched()
//----------------------------------------------------- NX_txtfield_touched
{
  switch (NXbuff[1])        // page
  {
    case 0x00:
      switch (NXbuff[2])    // field
      {
        case 0x04:
          if (digData.power == 0)
          {
            digData.power = 1;
          }
          else
          {
            digData.power = 0;
          }
          DMRupdateDigChannel();
          switch (digData.power)
          {
            case 0:
              Serial1.print("main.t4.txt=\"1 W\"");
              break;
            case 1:
              Serial1.print("main.t4.txt=\"5 W\"");
              break;
            default:
              Serial1.print("main.t4.txt=\"1 W\"");
              break;
          }
          NXend(11);
          break;
      }
      break;
    case 0x09:
      switch (NXbuff[2])
      {
        case 0x8:
          NX_P9_getCallsign();
          break;
        case 0x9:
          NX_P9_getDMRid();
          break;
        case 0x11:
          NX_P9_saveSSID(0);
          break;
        case 0x12:
          NX_P9_savePasswd(0);
          break;
        case 0x13:
          NX_P9_saveSSID(1);
          break;
        case 0x14:
          NX_P9_savePasswd(1);
          break;
        case 0x15:
          NX_P9_saveSSID(2);
          break;
        case 0x16:
          NX_P9_savePasswd(2);
          break;
        case 0x18:
          NX_P9_saveSSID(3);
          break;
        case 0x19:
          NX_P9_savePasswd(3);
          break;
      }
      break;
    case 0x0D:
      switch (NXbuff[2])
      {
        case 0x05:
          NX_P9_getCallsign();
          break;
        case 0x06:
          NX_P9_getDMRid();
          break;
        case 0x0E:
          NX_P9_saveSSID(0);
          break;
        case 0x0F:
          NX_P9_savePasswd(0);
          break;
        case 0x10:
          NX_P9_saveSSID(1);
          break;
        case 0x11:
          NX_P9_savePasswd(1);
          break;
        case 0x12:
          NX_P9_saveSSID(2);
          break;
        case 0x13:
          NX_P9_savePasswd(2);
          break;
        case 0x15:
          NX_P9_saveSSID(3);
          break;
        case 0x16:
          NX_P9_savePasswd(3);
          break;
      }
      break;
    case 0x0F:
      NX_P15_getInput();
      break;
  }
}
//========================================================================== field or button touch
void NX_numfield_touched()
//----------------------------------------------------- NX_txtfield_touched
{
  switch (NXbuff[1])        // page
  {

    case 0x09:
    case 0x0D:
      switch (NXbuff[2])
      {
        case 0x9:
          NX_P9_getDMRid();
          break;
      }
      break;
    case 0x0E:
      NX_P14_getRepeaterDMRid();
      break;
  }
}

void NX_button_pressed()
//----------------------------------------------------- NX_button_pressed
{
  switch (NXbuff[1])
  {
    case  0x00:              //-----------------------main page
      switch  (NXbuff[2])         // which button?
      {
        case 0x0:                   // PTT button b0
          if (NXbuff[3] == 1)
          {
            if (btnPTT == true)
            {
              btnPTT = false;
            }
            else
            {
              btnPTT = true;
            }
          }
          break;
        case 0x01:                   //lower audio b1
          if (audioVolume <= 1)
          {
            audioVolume = 2;
          }
          audioVolume = audioVolume - 1;
          DMRsetaudioVolume();
          break;
        case 0x02:                   //higher audio b2
          if (audioVolume >= maxAudioVolume)
          {
            audioVolume = maxAudioVolume - 1;
          }
          audioVolume = audioVolume + 1;
          DMRsetaudioVolume();
          break;
      }
      break;
    case  0x04:               //---------------------TG list page
      switch (NXbuff[2])
      {
        case 0x19:          // --- scroll back one page if there is
          p4_curPage = 0;
          Serial1.print("replist.va0.val=1");
          NXend(40);
          Serial1.print("page 4");
          NXend(41);

          break;
        case 0x20:          // --- scroll to next page if there is
          if (!p4_eof)
          {
            p4_curPage++;
            if (p4_curPage > (maxdigChlist / p4_numRows))
              p4_curPage--;
            Serial1.print("replist.va0.val=1");
            NXend(42);
            Serial1.print("page 4");
            NXend(43);
          }
          break;
      }
      if (NXbuff[2] < 18)   // ---- Channel selected
      {
        p4_selectedRow = NXbuff[2];
        NXselectRep = NXbuff[2] + p4_startRecord;
        Serial1.print("TGlist.va0.val=1");
        NXend(42);
        Serial1.print("page 5");
        NXend(27);
      }
      return;
    case  0x05:              // ---------------------repeater/TG list page
      NX_P5_buttonHandler();
      break;
    case  0x06:               //---------------------TG list page
      switch (NXbuff[2])
      {
        case 0x19:          // --- scroll back one page if there is
          p6_curPage = 0;
          Serial1.print("txGroup.va0.val=1");
          NXend(60);
          Serial1.print("page 6");
          NXend(61);
          break;
        case 0x20:          // --- scroll to next page if there is
          if (!p6_eof)
          {
            p6_curPage++;
            if (p6_curPage > (maxTGlist / p6_numRows))
              p6_curPage--;
            Serial1.print("txGroup.va0.val=1");
            NXend(62);
            Serial1.print("page 6");
            NXend(63);
          }
          break;
      }
      if (NXbuff[2] < 18)   // ---- Channel selected
      {
        digData.tx_contact = NXp6TG[NXbuff[2]].TG;
        digData.ContactType = NXp6TG[NXbuff[2]].calltype;
        NXselectTG = digData.tx_contact;
        DMRupdateDigChannel();
        Serial1.print("page 0");
        NXend(27);
      }
      break;
    case  0x07:               //---------------------Send SMS
      break;
    case  0x09:               //---------------------Setup
    case  0x0D:               //---------------------init Setup
      switch (NXbuff[2])
      {
        case 0x01:                   //lower audio b1
          if (dmrSettings.audioLevel <= 1)
          {
            dmrSettings.audioLevel = 2;
          }
          dmrSettings.audioLevel--;
          NX_P9_showVol();
          audioVolume = dmrSettings.audioLevel;
          settingsWrite(&dmrSettings);
          break;

        case 0x02:                   //higher audio b2
          if (dmrSettings.audioLevel >= maxAudioVolume)
          {
            dmrSettings.audioLevel = maxAudioVolume - 1;
          }
          dmrSettings.audioLevel++;
          NX_P9_showVol();
          audioVolume = dmrSettings.audioLevel;
          settingsWrite(&dmrSettings);
          break;
        case 0x04:
          if (dmrSettings.micLevel >= maxMicVolume)
          {
            dmrSettings.micLevel = maxMicVolume;
          }
          dmrSettings.micLevel++;
          NX_P9_showMicVol();
          micVolume = dmrSettings.micLevel;
          DMRsetMicVolume(micVolume);
          settingsWrite(&dmrSettings);
          break;
        case 0x03:
          if (dmrSettings.micLevel <= 0)
          {
            dmrSettings.micLevel = 1;
          }
          dmrSettings.micLevel--;
          NX_P9_showMicVol();
          micVolume = dmrSettings.micLevel;
          DMRsetMicVolume(micVolume);
          settingsWrite(&dmrSettings);
          break;
        case 0x18:
          UnitState = SYSTEM_STARTING;          // page 13 (initSetup) exit button
          break;
      }
      break;
    case  0xE:               //---------------------rxGroup update
      if (NXbuff[2] == 0x0)
      {
        NX_P14_updateRepHotspotDB(0,maxRepeaters);
      }
      break;

    case  0x11:               //---------------------rxGroup update
      if (NXbuff[2] < 32)
      {
        dmrSettings.rxTGStatus[NXbuff[2]] = NXbuff[3];
        settingsWrite(&dmrSettings);
      }
      break;
    case  0x12:
      switch (NXbuff[2])
      {
        case  0x00:
          if (NXbuff[3] == 1)
          {
            curdigCh.TimeSlot = 1;
          }
          else
          {
            curdigCh.TimeSlot = 2;
          }
          break;
        case  0x01:
          if (NXbuff[3] == 1)
          {
            curdigCh.TimeSlot = 2;
          }
          else
          {
            curdigCh.TimeSlot = 1;
          }

          break;
        case  0x02:
          if (NXbuff[3] == 1)
          {
            ts_scan = true;
          }
          else
          {
            ts_scan = false;
          }
          break;
      }
      break;
    case 0x0F:
      switch (NXbuff[2])
      {
        case  0x00:
          NX_P15_saveRepeaterlist();
          break;
        case  0x01:
          NX_P15_fillRepeaterlist();
          break;
      }
      break;
  }
}
//========================================================================== page init
void  NX_page_init()
//----------------------------------------------------- Events based on PP
{
  //  Serial.print("Page_init ");
  //  Serial.print(NXbuff[1],HEX);
  //  Serial.print(" ");
  //  Serial.print(ESP.getFreeHeap());
  //  Serial.print(" min heap ");
  //  Serial.println(ESP.getMinFreeHeap());

  switch (NXbuff[1])
  {
    case 0x00:                                      //main page
      //      DMRinitChannel(curChanItem.chnr,curChanItem.TG);
      DMRupdateDigChannel();
      NX_P0_DisplayCurrent();
      break;
    case 0x01:                                      //start page
      Serial1.print("t0.txt=\"");
      Serial1.print(String(dmrSettings.callSign));
      Serial1.print("\"");
      NXend(4);

    case 0x04:                                      //select repeater
      p5_lastRecord = -1;
      if (NXbuff[2] == 0x00)
      {
        p4_curPage = 0;
      }
      NX_P4_displayChannels();
      break;
    case 0x05:                                      //select TG
      if (NXbuff[2] == 0x00)
      {
        p5_lastRecord = -1;
      }
      NX_P5_displayTGlist();
      break;
    case 0x06:                                     //select tx TG
      if (NXbuff[2] == 0x00)
      {
        p6_curPage = 0;
      }
      NX_P6_displayTG();
      break;
    case 0x07:                                      //send SMS
      DMRsendSMS();
      break;
    case 0x09:                                      //setup parameters (wifi, TS scanning
      NX_P9_displaySSID();
      NX_P9_set_channelinfo();
      NX_P9_showVol();
      NX_P9_showMicVol();
      NX_P9_displayVersion();
      break;
    case 0x10:                                      //rx last heard DMR id
      NX_P10_rxLastHeard();
      break;
    case 0x11:                                      //select rx Talk Groups
      for (int i = 0; i < NXmaxrxTalkgroups; i++)
      {
        if (dmrSettings.rxTalkGroup[i] > 0)
        {
          Serial1.print("bt");
          Serial1.print(i);
          Serial1.print(".txt=\"");
          Serial1.print(String(dmrSettings.rxTalkGroup[i]));
          Serial1.print("\"");
          NXend(50);
          if (dmrSettings.rxTGStatus[i] == 1)
          {
            Serial1.print("bt");
            Serial1.print(i);
            Serial1.print(".val=1");
            NXend(50);
          }
        }
      }
      break;
    case 0x12:                                      // TS usage setup
      if (digData.InboundSlot == 0)
      {
        Serial1.print("bt0.val=1");
        NXend(40);
        Serial1.print("bt1.val=0");
        NXend(41);
      }
      else
      {
        Serial1.print("bt1.val=1");
        NXend(42);
        Serial1.print("bt0.val=0");
        NXend(43);
      }
      if (ts_scan)
      {
        Serial1.print("bt2.val=1");
      }
      else
      {
        Serial1.print("bt2.val=0");
      }
      NXend(44);
      break;
    case 0x13:                                      //setup parameters (wifi, TS scanning
      NX_P9_showVol();
      NX_P9_showMicVol();
      NX_P9_displayVersion();
      break;
    case 0x14:
    case 0x0E:
      NX_P14_fillRepeaterlist();
      break;
    case 0x15:
    case 0x0F:
      NX_P15_initPage();
      break;

  }
}
//========================================================================== NX main event handler
// based on event code sent from objects relevent routine is called
//
void NXhandler()
//--------------------------------------------------- NXhandler
//                                                    takes care of messages from Nextion
{
  if (Serial1.available() > 0)
  {
    if (NXlisten())
    {
      switch (NXbuff[0])
        //----- 31 PP FF <number>  Numeric field
        //----- 32 PP FF <text>    TextField
        //----- 33 PP BB AA  Button
        //----- 34 PP        Page
        //         PP = page no
        //         BB = Button no
        //         FF = field no
        //         AA = activity 1 = press, 0 = release
        //----- 65 PP BB EE Nextion standard message
        //         Returned when Touch occurs and component’s
        //         corresponding Send Component ID is checked
        //         in the users HMI design.
        //         PP is page number, CC is component ID,
        //         AA is activity (0x01 Press and 0x00 Release)
        //----- 1A Error message from Nextion
        //----- 00 Error message from Nextion
      {
        case 0x31:
          NX_numfield_touched();
        case 0x32:
          NX_txtfield_touched();
          break;
        case 0x33:
          NX_button_pressed();
          break;
        case 0x34:
          NX_page_init();
          break;
        case 0x65:                  // Nextion standard message
          break;
        case 0x1A:                                  // Returned when invalid Variable name
          Serial.print("Error NX message 0x1A ");    // or invalid attribute was used
          Serial.println(lastNXtrans);
          break;
        default:                                   // error message from Nextion
          Serial.print("Error NX message ");
          Serial.print(NXbuff[0], HEX);
          Serial.print(" ");
          Serial.println(lastNXtrans);
          break;
      }
    }
  }
}

//========================================================================== NX helper routines

boolean NXlisten()
//----------------------------------------------------------- NXreceiveFromDisplay
{
  int i = 0;
  int j = 0;
  int ffcount = 0;
  boolean rcode = false;
  uint32_t startmillis = millis();
  //Serial.print("Start rec ")
  while (Serial1.available() == 0 and ((millis() - startmillis) < 500)) { // wait for first character
  }
  if (Serial1.available() > 0)                                       // we have a message
  {
    while (Serial1.available() > 0 and i < 39)                              // read rest of message
    {
      NXbuff[i++] = Serial1.read(); //these are received response
      if (NXbuff[i - 1] == 0xFF) // and Serial2.available())             // until tail captured (FF FF FF)
      {
        ffcount++;
        if (ffcount == 3)
        {
          rcode = true;
          break;
        }
      }
      startmillis = millis();
      while (!(Serial1.available() > 0) and (millis() - startmillis) < 10000)
      { // wait max 5s if host is slow
      }
    }
    if (NXDebug)
    {
      Serial.print("From NX:");
      if (i > 0)
      {
        while (j < i)
        {
          Serial.print(NXbuff[j++], HEX);
          Serial.print(" ");
        }
      }
    }
    if (NXDebug)
    {
      Serial.print(" < ");
      Serial.print(i);
      Serial.println(" ");
    }
  }
  return rcode;         // return false if not a complete message is captured
}

void NXend(int nr)
//----------------------------------------------------------- NXend
{
  Serial1.write(0xff);
  Serial1.write(0xff);
  Serial1.write(0xff);
  lastNXtrans = nr;
}
