//========================================================================== startup
void NXend(int nr);

void NX_P3_statusDisplay(const String msg)
{
  NextionCmd.print("DMRlogga.t0");
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print(msg);
  NextionCmd.print("\"");
  NXend(300);
}
void NXinitDisplay(const String msg)
//----------------------------------------------------- NXinitDisplay
//    start Nextion Screen
{
  NextionCmd.print("page 3");   //page 3
  NXend(2);
  NX_P3_statusDisplay(msg);
}
void NXinitialSetup()
//----------------------------------------------------------- Initial setup screen (
//
{
  NextionCmd.print("page 13");
  NXend(201);
}

void NXdimdisplay(uint8_t func)
//----------------------------------------------------------- Initial setup screen (
//
{
  if (func == 1)
  {
    NextionCmd.print("dim=25");
    NXend(202);
  }
  else
  {
    NextionCmd.print("dim=100");
    NXend(203);
  }

}
boolean NX_isvalidnum(char* charval)
//-----------------------------------------------------------
//
{
  Debug.println("check if num ");
  boolean num = true;
  uint8_t m = 99;
  uint8_t p = 0;
  if (strlen(charval) < 3)
  {
    return false;
  }
  for (int i = 0; i < strlen(charval); i++)
  {
    if (charval[i] == '-')
    {
      m = i;
    }
    else if (charval[i] == '.')
    {
      p = i;
    }
    else if (!(charval[i] >= '0' and charval[i] <= '9'))
    {
      num = false;
    }
    Debug.println(i);
    Debug.println(charval[i]);
    Debug.println(m);
    Debug.println(p);
  }
  Debug.println();
  if (num)
  {
    if (!(m == 0 or m == 99))
    {
      num = false;
      Debug.println("!(m == 0 or m == 99)");
    }
    if (p == 0)
    {
      num = false;
      Debug.println("p == 0");
    }
    if (m == 0 and p > 4)
    {
      num = false;
      Debug.println("m == 0 and p > 4");

    }
    if (num)
    {
      if (!(m == 0 and p == 2 or m == 0 and p == 3 or m == 0 and p == 4 and charval[1] == '1' or
            m == 99 and p == 1 or m == 99 and p == 2 or m == 99 and p == 3 and charval[0] == '1'))
      {
        num = false;
        Debug.println("num but wrong . placement");
      }
    }
  }
  Debug.print(num);
  return num;
}
//========================================================================== page 0
void NX_P0_DisplayMainPage()
//----------------------------------------------------------- DisplayMainPage
//
{
  NextionCmd.print("page main");
  NXend(24);
}
void NX_P0_DisplayCurrent()
//----------------------------------------------------------- DisplayCurrent
//
{
  // ---- input to display on "channel screen"
  //prepare those strings
  String tempS = String(dmrSettings.repeater[dmrSettings.chnr].rx);
  String fR = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
  tempS = String(dmrSettings.repeater[dmrSettings.chnr].tx);
  String fT = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
  String fullName = String(dmrSettings.repeater[dmrSettings.chnr].repeaterName) + " " + String(dmrSettings.repeater[dmrSettings.chnr].repeaterLoc);
  fullName.trim();
  String firstBlock = String(dmrSettings.localID);
  NextionCmd.print("main.t0.txt=\"");
  NextionCmd.print(firstBlock);
  NextionCmd.print("\"");
  NXend(8);
  NextionCmd.print("main.t2.txt=\"");
  NextionCmd.print(fullName);
  NextionCmd.print("\"");
  NXend(9);
  NextionCmd.print("main.t3.txt=\"");
  NextionCmd.print(dmrSettings.callSign);
  NextionCmd.print("\"");
  NXend(4);
  //these lines are for "TX:444.88250"
  NextionCmd.print("main.t5.txt=\"");
  NextionCmd.print(fT);
  NextionCmd.print("\"");
  NXend(10);
  switch (digData.power)
  {
    case 0:
      NextionCmd.print("main.t4.txt=\"1 W\"");
      break;
    case 1:
      NextionCmd.print("main.t4.txt=\"5 W\"");
      break;
    default:
      NextionCmd.print("main.t4.txt=\"1 W\"");
      break;
  }
  NXend(11);
  //these for large receiving frequency
  NextionCmd.print("main.t6.txt=\"");
  NextionCmd.print(fR.substring(0, 7));
  NextionCmd.println(fR.substring(7, 9));
  NextionCmd.print("\"");
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
      NextionCmd.print("main.t1.txt=\"Individual\"");
      break;
    case 1:
      NextionCmd.print("main.t1.txt=\"Group Call\"");
      break;
    default:
      NextionCmd.print("main.t1.txt=\"Group Call\"");
      break;
  }
  NXend(13);
  NextionCmd.print("main.n5.val=");
  NextionCmd.print(digData.tx_contact);
  NXend(14);
  NX_P0_DisplayCurrentTS();
  NextionCmd.print("main.n3.val=");
  NextionCmd.print(digData.cc);
  NXend(16);
}
void  NX_P0_DisplayCurrentTS()
//----------------------------------------------------------- DisplayCurrentTS
//
{
  NextionCmd.print("main.n2.val=");
  NextionCmd.print(digData.InboundSlot + 1);
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
    NextionCmd.print("main.t5.txt=\"");
    NextionCmd.print(tempS);
    NextionCmd.print("\"");
    NXend(17);
    NxSetStatus(String("TX"), 65535, 63488, true);    // white on red background, centered
    rxS = String(digData.tx_freq);
    NextionCmd.print("main.t6.txt=\"");
    NextionCmd.print(rxS.substring(0, 3));
    NextionCmd.print(F("."));
    NextionCmd.print(rxS.substring(3, 6));
    NextionCmd.print(rxS.substring(6, 40));
    NextionCmd.print("\"");
    NXend(19);
  }
  else
  {
    tempS = String(digData.tx_freq);
    tempS = tempS.substring(0, 3) + "." + tempS.substring(3, 8);
    NextionCmd.print("main.t5.txt=\"");
    NextionCmd.print(tempS);
    NextionCmd.print("\"");
    NXend(20);
    NxSetStatus(String("MON"), 65535, 0, true);   // white on black background, centered
    rxS = String(digData.rx_freq);
    NextionCmd.print("main.t6.txt=\"");
    NextionCmd.print(rxS.substring(0, 3));
    NextionCmd.print(F("."));
    NextionCmd.print(rxS.substring(3, 6));
    NextionCmd.print(rxS.substring(6, 40));
    NextionCmd.print("\"");
    NXend(23);
  }
}
void NX_P0_DisplayReceive(boolean rec_on, byte calltype, uint32_t TGId)
//----------------------------------------------------------- DisplayReceive
//
{
  if (rec_on)
  {
    NxSetStatus(String("RX"), 0, 2016, true);   // black on green background, centered
    NextionCmd.print("main.t10.txt=\"");
    NextionCmd.print(rxGroup);
    NextionCmd.print("\"");
    //    switch (calltype)
    //    {
    //    case 0:
    //      NextionCmd.print("main.t10.txt=\"Individual\"");
    //      break;
    //    case 1:
    //      NextionCmd.print("main.t10.txt=\"Group Call\"");
    //      break;
    //    default:
    //      NextionCmd.print("main.t10.txt=\"Group Call\"");
    //      break;
    //    }
    NXend(24);
    NextionCmd.print("main.n4.val=");
    NextionCmd.print(TGId);
    NXend(25);
    if (WIFIcallfound)
    {
      NextionCmd.print("main.t12.txt=\"");
      NextionCmd.print(ri_callsign);
      NextionCmd.print("\"");
      NXend(26);
      NextionCmd.print("main.t17.txt=\"");
      NextionCmd.print(ri_fname);
      NextionCmd.print(",");
      if (ri_surname != "null")
      {
        NextionCmd.print(ri_surname);
        NextionCmd.print(",");
      }
      NextionCmd.print(ri_city);
      NextionCmd.print("\"");
      NXend(27);
      NextionCmd.print("main.t18.txt=\"");
      if (ri_state.length() != 0)
      {
        NextionCmd.print(ri_state);
        NextionCmd.print(",");
      }
      NextionCmd.print(ri_country);
      NextionCmd.print("\"");
      NXend(27);
    }
    else
    {
      NextionCmd.print("main.t12.txt=\"");
      NextionCmd.print("-- ");
      NextionCmd.print("\"");
      NXend(28);
      NextionCmd.print("main.t17.txt=\"");
      NextionCmd.print(" ");
      NextionCmd.print("\"");
      NXend(29);
      NextionCmd.print("main.t18.txt=\"");
      NextionCmd.print(" ");
      NextionCmd.print("\"");
      NXend(29);
    }
  }
  else
  {
    //    NextionCmd.print("main.t10.txt=\"Last\""); Ska kanske vara byte av färg istället?
    //    NXend(30);
    NxSetStatus(String("MON"), 65535, 0, true);   // white on black background, centered
    NXend(31);
    //   NextionCmd.print("main.t8.txt=\"     \"");
    //   NXend(31);
  }
}
void NX_P0_updateRSSI(uint8_t rssi)
//----------------------------------------------------- NX_P0_updateRSSI

{
  NextionCmd.print("main.j1.val="); // Changing the value of box n1
  uint8_t rssiproc = (100 * rssi) / 33;
  NextionCmd.print(rssiproc); // show set volume level
  NXend(23);
}
void NX_P0_showVol()
//----------------------------------------------------- NXshowVol

{
  NextionCmd.print("main.j0.val="); // Changing the value of progress bar
  int volproc = (100 * (audioVolume - 1)) / (maxAudioVolume - 1);
  NextionCmd.print(volproc); // show set volume level
  NXend(22);
}

void  NX_P0_showState()
//----------------------------------------------------- NX_P0_showState
//
// optimized - only update when changed
{
  if (UnitState != lastUnitState)
  {
    NextionCmd.print("main.n0.val="); // Changing the value of box n0
    NextionCmd.print(UnitState);
    NXend(6);
    lastUnitState = UnitState;
  }
  //  looptime = millis()-loopstartNext;
  //  loopstartNext = millis();
  //  if (abs(looptime)>150)
  //  {
  //    NextionCmd.print("main.n1.val="); // Changing the value of box n1
  //    NextionCmd.print(looptime); // show loop time
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
  uint8_t curRow = 0;
  p4_eof = false;
  //  p4_startRecord = repeaterChnr;
  p4_repeaterChnr--;
  while (DBgetnextChannel(p4_repeaterChnr) and curRow < p4_numRows)
  {
    p4_repeaterChnr = tmpdigCh.chnr;
    NextionCmd.print("b");
    NextionCmd.print(curRow);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(tmpdigCh.repeaterName);
    NextionCmd.print(" ");
    NextionCmd.print(tmpdigCh.repeaterLoc);
    NextionCmd.print(" (");
    NextionCmd.print(tmpdigCh.dmrId);
    NextionCmd.print(")");
    NextionCmd.print("\"");
    NXp4Ch[curRow] = tmpdigCh;
    NXend(23);
    curRow++;
  }
  while (curRow < p4_numRows)
  {
    NextionCmd.print("b");
    NextionCmd.print(curRow);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(" ");
    NextionCmd.print("\"");
    p4_eof = true;
    NXend(24);
    curRow++;
  }
}

//========================================================================== page 5
void  NX_P5_displayTGlist()
//----------------------------------------------------------- displayChannel
//
// A channel is selected on page 4 - now list TGs
{
  //------------- display page header
  String fullName = String(NXp4Ch[p4_selectedRow].repeaterName) + " " + String(NXp4Ch[p4_selectedRow].repeaterLoc);
  fullName.trim();
  NextionCmd.print("t0.txt=");
  NextionCmd.print("\"");
  NextionCmd.print(fullName);
  NextionCmd.print("\"");
  NXend(26);
  //--------------- display static TGs connected to channel - max p5_numRows on a page
  uint8_t curRow = 0;
  uint8_t i;
  for (uint8_t i = 0; i < p5_numRows; i++)
  {
    curRow = i;
    if (DBgetsinglerepTG(i))
    {
      NXp5repTG[i] = currepTG;
      NextionCmd.print("b");
      NextionCmd.print(curRow);
      NextionCmd.print(".txt=");
//      NXp5repTG[curRow] = repTGlist[i];
      NextionCmd.print("\"");
      NextionCmd.print(String(NXp5repTG[i].tg_id));
      NextionCmd.print(" ");
      if (DBgetTG(NXp5repTG[i].tg_id))
      {
        NextionCmd.print(curTG.TGname);
        //        NXp5TG[curRow] = curTG;
      }
      NextionCmd.print(" ts:");
      NextionCmd.print(String(NXp5repTG[i].ts));
      NextionCmd.print("\"");
      NXend(23);
    }
  }
  for (uint8_t i = curRow+1; i < p5_numRows; i++) // if page not filled blank out the rest
  {
    NextionCmd.print("b");
    NextionCmd.print(i);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(" ");
    NextionCmd.print("\"");
    p5_eof = true;
    NXend(25);
  }
    Debug.println("NXp5repTG ");
    Debug.print(NXselectRep);
    Debug.println("");
    for (uint8_t i=0;i<10;i++)
    {
      Debug.print(NXp5repTG[i].tg_id);
      Debug.print(" ");
      Debug.print(NXp5repTG[i].ts);
      Debug.println(" ");
    }
}
void NX_P5_buttonHandler()
//----------------------------------------- P5_buttonHandler
{
  if (NXbuff[2] == 0x19)
  {
    // --- scroll back to first page
    p5_lastRecord = -1;
    NextionCmd.print("TGlist.va0.val=1");
    NXend(50);
    NextionCmd.print("page 5");
    NXend(51);
  }
  if (NXbuff[2] == 0x20)
  {
    if (!p5_eof)
    {
      NextionCmd.print("TGlist.va0.val=1");
      NXend(52);
      NextionCmd.print("page 5");
      NXend(53);
    }
  }
  if (NXbuff[2] < 18)   // ---- Channel selected
  {
    NextionCmd.print("TGlist.va0.val=0");
    NXend(54);
    p5_lastRecord = -1; // ----- reset scroll page
    if (NXbuff[3] == 1)
    {
      curdigCh =NXp4Ch[p4_selectedRow];
      currepTG = NXp5repTG[NXbuff[2]];
      digData.tx_contact = NXp5repTG[NXbuff[2]].tg_id;
      digData.ContactType = NXp5TG[NXbuff[2]].calltype;
      Debug.println("Selected p5: ");
      Debug.println(curdigCh.chnr);
      Debug.print(" ");
      Debug.print(curdigCh.dmrId);
      Debug.print(" ");
      Debug.print(curdigCh.repeaterName);
      Debug.print(" ");
      Debug.print(currepTG.tg_id);
      Debug.print(" ");
      Debug.print(currepTG.ts);
      Debug.print(" ");
      Debug.print(curdigCh.rx);
      Debug.print(" ");
      Debug.println(curdigCh.tx);
      DMRinitChannel();
      dmrSettings.chnr = curdigCh.chnr;
      dmrSettings.TG =  NXbuff[2];
      settingsWrite(&dmrSettings);

      NextionCmd.print("page 0");
    }
    else
    {
      dmrSettings.chnr = curdigCh.chnr;
      dmrSettings.TG =  NXbuff[2];
      settingsWrite(&dmrSettings);
      NextionCmd.print("page 9");
    }
    Debug.println("cur Chan in settings: ");
    Debug.print(dmrSettings.chnr);
    Debug.print(" ");
    Debug.println(dmrSettings.TG);
    NXend(55);
  }
}
//========================================================================== page 6
void NX_P6_displayTG()
//----------------------------------------------------------------------------NX_P6_display
{
  uint8_t recnr = 0;
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
      NextionCmd.print("b");
      NextionCmd.print(recnr);
      NextionCmd.print(".txt=");
      NextionCmd.print("\"");
      // NextionCmd.print(String(recnr+p6_startRecord));
      // NextionCmd.print(" ");
      NextionCmd.print(TGlist[recnr + p6_startRecord].TG);
      NextionCmd.print(" ");
      NextionCmd.print(TGlist[recnr + p6_startRecord].TGname);
      NextionCmd.print("\"");
      NXp6TG[recnr] = TGlist[recnr + p6_startRecord];
      NXend(33);
    }
    else
    {
      NextionCmd.print("b");
      NextionCmd.print(recnr);
      NextionCmd.print(".txt=");
      NextionCmd.print("\"");
      NextionCmd.print(" ");
      NextionCmd.print("\"");
      p6_eof = true;
      NXend(34);
    }
  }

}
//========================================================================== page 8
void NX_P8_viewSMS(String rxContactChar, String SMStext)
{
  NextionCmd.print("page recSMS");
  NXend(82);
  char combinedArray[sizeof(rxContactChar) + sizeof(ri_callsign) + 3];
  sprintf(combinedArray, "%s %s", rxContactChar, ri_callsign); // with word space
  NextionCmd.print("t11.txt=");
  NextionCmd.print("\"");
  NextionCmd.print(String(combinedArray));
  NextionCmd.print("\"");
  NXend(80);
  //  String SMStext ="fglkj lkjdf gkj dfgkj ödjsf göj dsöfgj sdöfgj södfgj sdlfk60";
  NextionCmd.print("t0.txt=");
  NextionCmd.print("\"");
  NextionCmd.print(SMStext);
  NextionCmd.print("\"");
  NXend(81);
}
//========================================================================== page 9
void NX_P9_displaySSID()
{
  NextionCmd.print("setup.t11.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[0].ssid);
  NextionCmd.print("\"");
  NXend(900);
  NextionCmd.print("setup.t12.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[0].passwd);
  NextionCmd.print("\"");
  NXend(910);
  NextionCmd.print("setup.t13.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[1].ssid);
  NextionCmd.print("\"");
  NXend(901);
  NextionCmd.print("setup.t14.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[1].passwd);
  NextionCmd.print("\"");
  NXend(911);
  NextionCmd.print("setup.t15.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[2].ssid);
  NextionCmd.print("\"");
  NXend(902);
  NextionCmd.print("setup.t16.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[2].passwd);
  NextionCmd.print("\"");
  NXend(912);
  NextionCmd.print("setup.t18.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[3].ssid);
  NextionCmd.print("\"");
  NXend(903);
  NextionCmd.print("setup.t19.txt=\"");
  NextionCmd.print(dmrSettings.wifisettings[3].passwd);
  NextionCmd.print("\"");
  NXend(913);

}
void NX_P9_set_callsign_id()
{
  NextionCmd.print("setup.t8.txt=\"");
  NextionCmd.print(dmrSettings.callSign);
  NextionCmd.print("\"");
  NXend(90);
  NextionCmd.print("setup.n9.val=");
  NextionCmd.print(dmrSettings.localID);
  NXend(91);
}
void NX_P9_set_channelinfo()
//---------------------------------------------------------- get channelinfo from dmrSettings
{
  String fullName = String(dmrSettings.repeater[dmrSettings.chnr].repeaterName) + " " + String(dmrSettings.repeater[dmrSettings.chnr].repeaterLoc);
  fullName.trim();
  NextionCmd.print("setup.t2.txt=\"");
  NextionCmd.print(fullName);
  NextionCmd.print("\"");
  NXend(92);
  NextionCmd.print("setup.n2.val=");
  NextionCmd.print(dmrSettings.repeater[dmrSettings.chnr].groups[dmrSettings.TG].tg_id);
  NXend(93);

}
void NX_P9_displayVersion()
//----------------------------------------------------------- displayVersion
//
// Display software version from current code module
// Query DMR module version and display on oled, last line (unused for now)
{

  NextionCmd.print("t6.txt=\"");
  NextionCmd.print(SoftwareVersion);
  NextionCmd.print("\"");
  NXend(94);
#ifdef INC_DMR_CALLS
  if (DMRgetVersion())
  {
    char ModuleVersion[19] = "                  ";
    for (uint8_t x = 8; x < 26; x++)
    {
      ModuleVersion[x - 8] = char(buff[x]);
    }
    //    ModuleVersion[18] = 0x0;
    NextionCmd.print("t7.txt=\"");
    NextionCmd.print(ModuleVersion);
    NextionCmd.print("\"");
    NXend(95);
  }
#endif
}
void NX_P9_showVol()
//----------------------------------------------------- NXshowVol

{
  NextionCmd.print("j0.val="); // Changing the value of progress bar
  int volproc = (100 * (dmrSettings.audioLevel - 1)) / (maxAudioVolume - 1);
  NextionCmd.print(volproc); // show set volume level
  NXend(96);
}
void NX_P9_showMicVol()
//----------------------------------------------------- NXshowVol

{
  NextionCmd.print("j1.val="); // Changing the value of progress bar
  int volproc = (100 * dmrSettings.micLevel) / maxMicVolume;
  NextionCmd.print(volproc); // show set volume level
  NXend(97);
}
void NX_P9_getCallsign()
//------------------------------------------------------NX_P9_getCallsign
{
  for (uint8_t x = 0; x < 10; x++)
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
void  NX_P9_saveSSID(uint8_t indx)
//------------------------------------------------------NX_P9_saveSSID
{
  char tmp[16];
  for (uint8_t x = 0; x < 16; x++)
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

void  NX_P9_savePasswd(uint8_t indx)
//------------------------------------------------------NX_P9_savePasswd
{
  char tmp[16];
  for (uint8_t x = 0; x < 16; x++)
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
  uint8_t k = 0;
  for (uint8_t i = 0; i < numradioid; i++)
  {
    k++;
    NextionCmd.print("t");
    NextionCmd.print(k);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(ri_list[i].ri_talkgroup);
    NextionCmd.print(" ");
    NextionCmd.print(ri_list[i].ri_id);
    NextionCmd.print(" ");
    NextionCmd.print(ri_list[i].ri_callsign);
    NextionCmd.print(" ");
    NextionCmd.print(ri_list[i].ri_fname);
    NextionCmd.print(" ");
    NextionCmd.print(ri_list[i].ri_city);
    NextionCmd.print(" :");
    NextionCmd.print(ri_list[i].ri_count);
    NextionCmd.print("\"");
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
  uint8_t k = 0;
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
  //  Debug.println(repeaterID);
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
  }
  if (repeaterID != 0)
  {
    if (EIMreadRepeaterDMRid(repeaterIDChar, k))
    {
      NXrepeaterName[29] = 0x0;
    }
    else
    {
      EIMeraseRepHotspot(k);
      NXrepeaterName[0] = 0x0;
      repeaterID = 0;
    }
  }
  else
  {
    EIMeraseRepHotspot(k);
    NXrepeaterName[0] = 0x0;
  }
  settingsWrite(&dmrSettings);
  NextionCmd.print("n");
  NextionCmd.print(k);
  NextionCmd.print(".val=");
  NextionCmd.print(repeaterID);
  NXend(142);

  NextionCmd.print("t");
  NextionCmd.print(k);
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print(NXrepeaterName);
  NextionCmd.print("\"");
  NXend(140);
}

void  NX_P14_fillRepeaterlist()
//---------------------------------------------------------------------P14_fillRepeaterlist
{
  for (uint8_t k = 0; k < numManualRep; k++)
  {
    NextionCmd.print("n");
    NextionCmd.print(k);
    NextionCmd.print(".val=");
    NextionCmd.print(dmrSettings.repeater[k].dmrId);
    NXend(141);
    char charTmp[40] = "";
    if (dmrSettings.repeater[k].dmrId != 0)
    {
      sprintf(charTmp, "%s,%s", dmrSettings.repeater[k].repeaterName, dmrSettings.repeater[k].repeaterLoc);
      charTmp[29] = 0x0;
    }
    NextionCmd.print("t");
    NextionCmd.print(k);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(charTmp);
    NextionCmd.print("\"");
    NXend(142);
  }
}
void NX_P15_getInput()
//---------------------------------------------------------------------
{
  switch (NXbuff[2])
  {
    case 0x16:
      for (uint8_t x = 0; x < 10; x++)
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
      Debug.print("p15_long ");
      Debug.println(p15_long);
      break;
    case 0x17:
      for (uint8_t x = 0; x < 10; x++)
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
      Debug.println("p15_lat ");
      Debug.println(p15_lat);
      break;
    case 0x14:
      p15_dist = (uint32_t)NXbuff[6] << 24 | (uint32_t)NXbuff[5] << 16 |
                 (uint32_t)NXbuff[4] << 8 | (uint32_t)NXbuff[3];
      Debug.println("p15_dist ");
      Debug.println(p15_dist);
      break;
  }
}

void NX_P15_initLongLat()
//---------------------------------------------------------------------
{
  NextionCmd.print("EIMlocation.t");
  NextionCmd.print(0);
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print(dmrSettings.longitude);
  NextionCmd.print("\"");
  NXend(152);
  NextionCmd.print("EIMlocation.t");
  NextionCmd.print(1);
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print(dmrSettings.latitude);
  NextionCmd.print("\"");
  NXend(153);
  NextionCmd.print("EIMlocation.n");
  NextionCmd.print(0);
  NextionCmd.print(".val=");
  NextionCmd.print(dmrSettings.distance);
  NXend(154);
}


void NX_P15_initPage()
//---------------------------------------------------------------------
{
  NextionCmd.print("t");
  NextionCmd.print(33);
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print("");
  NextionCmd.print("\"");
  NXend(151);
}
boolean NX_P15_checkinputfields()
//---------------------------------------------------------------------
{
  char p15_errortext[26] = "";
  if (!NX_isvalidnum(p15_long))
  {
    strcat(p15_errortext, "err:long ");
  }
  if (!NX_isvalidnum(p15_lat))
  {
    strcat(p15_errortext, "err:lat ");
  }
  if (p15_dist == 0 or p15_dist > 200)
  {
    strcat(p15_errortext, "err:dist");
  }
  NextionCmd.print("t");
  NextionCmd.print(33);
  NextionCmd.print(".txt=");
  NextionCmd.print("\"");
  NextionCmd.print(p15_errortext);
  NextionCmd.print("\"");
  NXend(151);

  if (strlen(p15_errortext) > 0)
  {
    return false;
  }
  return true;
}

void  NX_P15_fillRepeaterlist()
//---------------------------------------------------------------------
{
  if (!NX_P15_checkinputfields())
  {
    return;
  }
  if (!EIMreadRepeatersLocation(p15_long, p15_lat, p15_dist))
  {
    reptemplistCurLen = 0;
  }
  for (uint8_t i = 0; i < p15_numRows; i++)
  {
    strcpy(NXrepeaterName, "");
    if (i <= reptemplistCurLen)
    {
      //       sprintf(NXrepeaterName, "%d-%s,%s", reptemplist[i].dmrId, reptemplist[i].repeaterName, reptemplist[i].repeaterLoc);
      sprintf(NXrepeaterName, "%s,%s", reptemplist[i].repeaterName, reptemplist[i].repeaterLoc);
      NXrepeaterName[25] = 0x0;
    }
    NextionCmd.print("t");
    NextionCmd.print(i + 20);
    NextionCmd.print(".txt=");
    NextionCmd.print("\"");
    NextionCmd.print(NXrepeaterName);
    NextionCmd.print("\"");
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
  uint8_t t = reptemplistCurLen;
  uint8_t rl=t;
  if (reptemplistCurLen = 0)
  {
    return;
  }
  if (!EIMreadStatus())
  {
    return;
  }
  uint8_t j = numManualRep;

  boolean manualfound = false;
  for (uint8_t i = 0; i <= rl; i++)
  {
    manualfound = false;
    for (uint8_t k = 0; (k < numManualRep)and !manualfound; k++)
    {
      if (dmrSettings.repeater[k].dmrId == reptemplist[i].dmrId)
      {
        manualfound = true;
        t--;
      }
    }
    if (!manualfound)
    {
      ltoa(reptemplist[i].dmrId, repeaterIDChar, 10);
      EIMreadRepeaterDMRid(repeaterIDChar, j);
      j++;
    }
  }
  for (uint8_t i = t +1+ numManualRep; i < maxRepeaters; i++)          // if you want to zero the repeater list
  {
    dmrSettings.repeater[i].zone  = 0;
    dmrSettings.repeater[i].dmrId = 0;
  }
  strcpy(dmrSettings.longitude,p15_long);
  strcpy(dmrSettings.latitude,p15_lat);
  dmrSettings.distance = p15_dist;
  settingsWrite(&dmrSettings);
  for (uint8_t k=0;k< maxRepeaters;k++)
  {
     EIMprintDMRsettingsitem(k);
  }

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
              NextionCmd.print("main.t4.txt=\"1 W\"");
              break;
            case 1:
              NextionCmd.print("main.t4.txt=\"5 W\"");
              break;
            default:
              NextionCmd.print("main.t4.txt=\"1 W\"");
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
          p4_repeaterChnr = 0;
          NextionCmd.print("replist.va0.val=1");
          NXend(40);
          NextionCmd.print("page 4");
          NXend(41);

          break;
        case 0x20:          // --- scroll to next page if there is
          if (!p4_eof)
          {
            p4_curPage++;
            p4_repeaterChnr++;
            if (p4_curPage > (maxRepeaters / p4_numRows))
            {
              p4_curPage--;
            }
            NextionCmd.print("replist.va0.val=1");
            NXend(42);
            NextionCmd.print("page 4");
            NXend(43);
          }
          break;
      }
      if (NXbuff[2] < 18)   // ---- Channel selected
      {
        p4_selectedRow = NXbuff[2];
        NXselectRep = NXbuff[2] + p4_startRecord;
        NextionCmd.print("TGlist.va0.val=1");
        NXend(42);
        NextionCmd.print("page 5");
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
          NextionCmd.print("txGroup.va0.val=1");
          NXend(60);
          NextionCmd.print("page 6");
          NXend(61);
          break;
        case 0x20:          // --- scroll to next page if there is
          if (!p6_eof)
          {
            p6_curPage++;
            if (p6_curPage > (maxTGlist / p6_numRows))
              p6_curPage--;
            NextionCmd.print("txGroup.va0.val=1");
            NXend(62);
            NextionCmd.print("page 6");
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
        NextionCmd.print("page 0");
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
        //        NX_P14_updateRepHotspotDB(0, maxRepeaters);
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
                       curdigCh.timeSlot = 1;
          }
          else
          {
                       curdigCh.timeSlot = 2;
          }
          break;
        case  0x01:
          if (NXbuff[3] == 1)
          {
                     curdigCh.timeSlot = 2;
          }
          else
          {
                     curdigCh.timeSlot = 1;
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

  switch (NXbuff[1])
  {
    case 0x00:                                      //main page
      //      DMRinitChannel(curChanItem.chnr,curChanItem.TG);
      DMRupdateDigChannel();
      NX_P0_DisplayCurrent();
      break;
    case 0x01:                                      //start page
      NextionCmd.print("t0.txt=\"");
      NextionCmd.print(String(dmrSettings.callSign));
      NextionCmd.print("\"");
      NXend(4);

    case 0x04:                                      //select repeater
      p5_lastRecord = -1;
      if (NXbuff[2] == 0x00)
      {
        p4_curPage = 0;
        p4_repeaterChnr = 0;
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
      for (uint8_t i = 0; i < NXmaxrxTalkgroups; i++)
      {
        if (dmrSettings.rxTalkGroup[i] > 0)
        {
          NextionCmd.print("bt");
          NextionCmd.print(i);
          NextionCmd.print(".txt=\"");
          NextionCmd.print(String(dmrSettings.rxTalkGroup[i]));
          NextionCmd.print("\"");
          NXend(50);
          if (dmrSettings.rxTGStatus[i] == 1)
          {
            NextionCmd.print("bt");
            NextionCmd.print(i);
            NextionCmd.print(".val=1");
            NXend(50);
          }
        }
      }
      break;
    case 0x12:                                      // TS usage setup
      if (digData.InboundSlot == 0)
      {
        NextionCmd.print("bt0.val=1");
        NXend(40);
        NextionCmd.print("bt1.val=0");
        NXend(41);
      }
      else
      {
        NextionCmd.print("bt1.val=1");
        NXend(42);
        NextionCmd.print("bt0.val=0");
        NXend(43);
      }
      if (ts_scan)
      {
        NextionCmd.print("bt2.val=1");
      }
      else
      {
        NextionCmd.print("bt2.val=0");
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
  if (NextionCmd.available() > 0)
  {
    if (idletimer > 0)
    {
      idletimer = millis();
      NXdimdisplay(0);
    }
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
          Debug.print("Error NX message 0x1A ");    // or invalid attribute was used
          Debug.println(lastNXtrans);
          break;
        default:                                   // error message from Nextion
          Debug.print("Error NX message ");
          Debug.print(NXbuff[0], HEX);
          Debug.print(" ");
          Debug.println(lastNXtrans);
          break;
      }
    }
  }
}

//========================================================================== NX helper routines

boolean NXlisten()
//----------------------------------------------------------- NXreceiveFromDisplay
{
  uint8_t i = 0;
  uint8_t j = 0;
  uint8_t ffcount = 0;
  boolean rcode = false;
  uint32_t startmillis = millis();
  while (NextionCmd.available() == 0 and ((millis() - startmillis) < 500)) { // wait for first character
  }
  if (NextionCmd.available() > 0)                                       // we have a message
  {
    while (NextionCmd.available() > 0 and i < 39)                              // read rest of message
    {
      NXbuff[i++] = NextionCmd.read(); //these are received response
      if (NXbuff[i - 1] == 0xFF) // and DmrCmd.available())             // until tail captured (FF FF FF)
      {
        ffcount++;
        if (ffcount == 3)
        {
          rcode = true;
          break;
        }
      }
      startmillis = millis();
      while (!(NextionCmd.available() > 0) and (millis() - startmillis) < 10000)
      { // wait max 5s if host is slow
      }
    }
    if (NXDebug)
    {
      Debug.print("From NX:");
      if (i > 0)
      {
        while (j < i)
        {
          Debug.print(NXbuff[j++], HEX);
          Debug.print(" ");
        }
      }
    }
    if (NXDebug)
    {
      Debug.print(" < ");
      Debug.print(i);
      Debug.println(" ");
    }
  }
  return rcode;         // return false if not a complete message is captured
}

void NXend(int nr)
//----------------------------------------------------------- NXend
{
  NextionCmd.write(0xff);
  NextionCmd.write(0xff);
  NextionCmd.write(0xff);
  lastNXtrans = nr;
}


void NxSetStatus(String text, uint16_t fgc, uint16_t bgc, boolean centered)
{
  /*
    print the status field, supports foreground, background color code as
    well as centering the text
  */
  NextionCmd.print("main.t7.txt=\"" + text + "\"");  // text
  NXend(6533);
  NextionCmd.print("main.t7.pco=" + String(fgc, DEC));   // white foreground
  NXend(6534);
  NextionCmd.print("main.t7.bco=" + String(bgc, DEC));   // red background
  NXend(6535);
  if (centered)
  {
    NextionCmd.print("main.t7.xcen=1");       // centered
  } else
  {
    NextionCmd.print("main.t7.xcen=0");       // left aligned
  }

  NXend(21);
}