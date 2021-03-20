
uint16_t PcCheckSum(uint8_t * buf, int len)

//----------------------------------------------------------- PcCheckSum
//-----------------calculate checksum
{
  uint32_t sum = 0;
  uint16_t      Pcksum = 4;             // checksum position in buff
  while (len > 1)
  {
    sum += 0xFFFF & (*buf << 8 | *(buf + 1));
    buf += 2;
    len -= 2;
  }
  if (len)
  {
    sum += (0xFF & *buf) << 8;
  }
  while (sum >> 16)
  {
    sum = (sum & 0xFFFF) + (sum >> 16);
  }
  int cksum = ( (uint16_t) sum ^ 0xFFFF);
  buff[Pcksum + 1] = (cksum & 0x00ff);
  buff[Pcksum] = (cksum >> 8) & 0x00ff;
  return ( (uint16_t) sum ^ 0xFFFF);    // redundant - return code not used in this program
}

int CheckCkSum(int len, uint8_t * buf)
//----------------------------------------------------------------- CheckCkSum
//---------------Check if check sum correct
{
  uint16_t sum, cksum;
  uint16_t      Pcksum = 4;             // checksum position in buff
  sum = buf[Pcksum];
  buf[Pcksum] = 0;
  sum = (sum << 8);
  sum = sum + buf[Pcksum + 1];
  buf[Pcksum + 1] = 0;
  cksum = PcCheckSum(buf, len);
  buf[Pcksum + 1] = (sum & 0xff);
  buf[Pcksum] = (sum >> 8) & 0xff;
  if (sum == cksum)
  {
    //AckToPC(buf[Pcmd],ok);
    return 1;
  }
  else
  {
    //AckToPC(buf[Pcmd],ChkError);
    return 0;
  }
}

void DMRhandler()
//----------------------------------------------------------------- CheckCkSum
{
  DMRlisten();
  if (buff[1] == 0x3D)
  {
    if (buff[8] == 0)              // is it a message 0x3D start voice call?
    {
      DMRvoicemessageStart();
      return;
    }
    if (buff[8] == 1)
    {
      DMRvoicemessageEnd();
      return;
    }
    Serial.print("DMRhandler: message thrown away ");
    Serial.print(buff[1], HEX);
    Serial.print("");
    Serial.println(buff[8], HEX);
  }
  if (buff[1] == 0x2D)          // receiving SMS
  {
    DMRcheckSMSRec();
    return;
  }
  Serial.print("DMRhandler: message thrown away: ");
  Serial.print(buff[1], HEX);
  Serial.print("");
  Serial.println(buff[8], HEX);
}

void DMRvoicemessageStart()
//----------------------------------------------------------------- DMRvoicemessageStart

{
  Serial.print("start 3xD ");
  UnitState = REC_DMR_STATE;
  bRecVoicemessage = true;
  DMRqueryReceived(true);
  if (DMRcheckRSSI())
  {
    NX_P0_updateRSSI(buff[8]);
  }
  RSSItimer = millis();
}
void DMRvoicemessageEnd()
//----------------------------------------------------------------- DMRvoicemessageEnd

{
  Serial.println("- end 3xD ");
  //   DisplayReceive(false, 0, 0);
  NX_P0_DisplayReceive(false, 0, 0);
  NX_P0_updateRSSI(0);                    // reset s-meter
  tsSwitchLast = millis();            // wait at this ts one extra scan cycle - maybe response is coming
  bRecVoicemessage = false;
  if (UnitState == REC_DMR_STATE)
  {
    UnitState = IDLE_STATE;
  }
  Serial.print(" Voice message end free heap ");
  Serial.print(ESP.getFreeHeap());
  Serial.print(" min heap ");
  Serial.println(ESP.getMinFreeHeap());
  Serial.print(" numradioid. ");
  Serial.println(numradioid);
}
void DMRsendTo(int len) {
  //--------------------------------------------------------------- DMRsendTo
#ifdef INC_DMR_CALLS
  uint8_t antsent;

  if (DMRDebug)
  {
    Serial.print ("To X DMR:");
  }
  for (int i = 0; i < len; i++)
  {
    antsent = Serial2.write(buff[i]);
    if (DMRDebug)
    {
      if (antsent > 0)
      {
        Serial.print(buff[i], HEX);
        if  (i == 70 or i == 140)
        {
          Serial.println();
        }
        Serial.print(" ");
      }
      else
      {
        Serial.print("Send buffer overflow");
        Serial.println("");
      }
    }
    if (buff[i] == 0x10)
    {
      break;
    }
  }
  if (DMRDebug)
  {
    Serial.println();
  }
#endif
}

boolean DMRreceive() {
  //----------------------------------------------------------------- DMRreceive
#ifdef INC_DMR_CALLS
  int i = 0;
  int j = 0;
  boolean rcode = false;
  uint32_t startmillis = millis();
  while (Serial2.available() == 0 and ((millis() - startmillis) < 1000)) { // wait for first character
  }
  if (Serial2.available() > 0)                                       // we have a message
  {
    while (Serial2.available() > 0)                                // read rest of message
    {
      buff[i++] = Serial2.read(); //these are received response
      if (buff[i - 1] == 0x10) // and Serial2.available())             // until tail captured
      {
        rcode = false;
        if (buff[3] == 0x0)
        {
          rcode = true;
        }
        break;
      }
      startmillis = millis();
      while (!(Serial2.available() > 0) and (millis() - startmillis) < 10000)
      { // wait max 5s if host is slow
      }
    }
    if (DMRDebug)
    {
      Serial.print("From DMR:");
      if (i > 0)
      {
        while (j < i)
        {
          Serial.print(buff[j++], HEX);
          //            if (j==71 or j==141)
          //            {
          //              Serial.println();
          //            }
          Serial.print(" ");
        }
      }
    }
    if (DMRDebug)
    {
      Serial.print(" < ");
      Serial.print(i);
      Serial.println(" ");
    }
  }
  return rcode;         // return false if not a complete message is captured
#endif
#ifndef INC_DMR_CALLS
  return true;
#endif
}

boolean DMRreceiveReply(uint8_t CMD)
{
  boolean rcode;
  rcode = DMRreceive();
  if (buff[1] == CMD and rcode)       // message returned and correct command
  {
    return rcode;
  }
  // most likely it is a unsolicited message
  switch (buff[1])
  {
    case 0x3D:
      if (buff[8] == 0x0)
      {
        bRecVoicemessageStart = true;
      }
      if (buff[8] == 0x1)
      {
        bRecVoicemessageEnd = true;
      }
      break;
    case 0x2D:
      // !!!måste man kopiera bort från buff?
      bSMSmessageReceived = true;
      break;
  }
  // then try to read one more message
  rcode = DMRreceive();
  if (buff[1] == CMD and rcode)       // message returned and correct command
  {
    return rcode;
  }
  Serial.print ("error wrong command reply ");
  Serial.print (buff[1], HEX);
  Serial.print (" ");
  Serial.println (CMD, HEX);
  return rcode;
}

boolean DMRTransmit(uint8_t mode, uint8_t CMD) {
  //------------------------------------------------------------------ DMRTransmit
  int  len = 10;
  int notused;
  boolean rcode = false;
  buff[0] = 0x68;
  buff[1] = CMD;
  buff[2] = 0x01;
  buff[3] = 0x01;
  buff[4] = 0x00;
  buff[5] = 0x00;
  buff[6] = 0x00;
  buff[7] = 0x01;
  buff[8] = mode;
  buff[9] = 0x10;
  // beräkna checksumma och lägg i 4,5
  notused = PcCheckSum(buff, len);
  //  buff[Pcksum+1] = (cksum&0x00ff);
  //  buff[Pcksum] = (cksum>>8)&0x00ff;
  DMRsendTo(len);
  rcode = DMRreceiveReply(CMD);
  return rcode;
  //return true;        // tillfällig lösning för att hantera 27 27 problemet
}

boolean DMRlisten()
//---------------------------------------------------------------- DMRlisten
//
// if command = 0x3D there is an unsolicited message from Host indicating voice message start or end
// indicates either receive session start (buff[8]=0) or receive session end (buff[9]=1)
{
  //DMRDebug = false;
  unsigned long interruptTime = millis();
  if (interruptTime - lastInterruptTime > 1)
  {
    lastInterruptTime = interruptTime;
    if (DMRreceive())
    {
      //DMRDebug=false;
      if (buff[1] == 0x3D or buff[1] == 0x2D)
      {
        return true;
      }
    }
    return false;
  }
}
// tillfällig fix pga BM visar fel i gränssnittet 20201-03-20
void DMRsetDigChannel(uint32_t tx_freq, uint32_t rx_freq, uint32_t tx_contact,
                      uint8_t ContactType, uint8_t cc, uint8_t ts, uint8_t ChannelMode, uint8_t relay)
//void DMRsetDigChannel(uint32_t rx_freq, uint32_t tx_freq, uint32_t tx_contact,
//                      uint8_t ContactType, uint8_t cc, uint8_t ts, uint8_t ChannelMode, uint8_t relay)

{
  //------------------------------------------------------------------ DMRsetDigChannel
  //       Packet header length = 8

  // now global---  db_digital_info digData;
  int len, cksum, antsent;

  digData.head = 0x68;            //header 0x68
  digData.CMD  = SET_DIGITAL_CHANNEL;            // command
  digData.RW   = 1;               // operation type
  digData.SR   = 1;               // set/response
  digData.CKSUM = 0;              // checksum
  digData.LEN_dummy = 0;
  digData.LEN  = sizeof (digData) - 9; // DATA length

  //        Data length =
  digData.rx_freq = rx_freq;     //receive  frequency    Hotspot
  digData.tx_freq = tx_freq;     //transmit frequency    Hotspot
  digData.localID = dmrSettings.localID; //local     ID1-16776415
  for (int i = 0; i < 32; i++)
  {
    if (dmrSettings.rxTGStatus[i] == 1)
    {
      digData.GroupList[i] = dmrSettings.rxTalkGroup[i]; //receive  group   list
    }
    else
    {
      digData.GroupList[i] = 0;
    }
  }
  digData.tx_contact = tx_contact;    //contact  number  1-16776415
  digData.ContactType = ContactType;
  digData.power = 0;         //0:low power  1：high power
  digData.cc = cc;            //color code0~15
  digData.InboundSlot  = ts - 1; //1:slot 1 1:slot 2
  digData.OutboundSlot = ts - 1; //1:slot 1 1:slot 2
  digData.ChannelMode = ChannelMode;   //0:direct connectionmode 4:true dual slot
  digData.EncryptSw = 2;     //encryption switch 1:enable 2:disable
  for (int i = 0; i < 8; i++)
  {
    digData.EncryptKey[i] = 0; //secret key
  }
  digData.pwrsave = 2;       //power save switch 2:disable 1:enable
  digData.volume = audioVolume;        //Volume 1-9
  digData.mic = micVolume;           //micgain 0-15
  digData.relay = relay;         //relay disconnectnet 2:disable 1:enable
  digData.tail = 0x10;
  DMRupdateDigChannel();
}

boolean DMRupdateDigChannel()
//--------------------------------------------------------------- DMRupdateDigChannel
{
  int len = sizeof(digData);
  digData.localID = dmrSettings.localID; //local
  digData.pwrsave = 2;       //power save switch 2:disable 1:enable
  digData.volume = audioVolume;        //Volume 1-9
  digData.mic = micVolume;           //micgain 0-15
  // digData.relay = relay;         //relay disconnectnet 2:disable 1:enable
  digData.tail = 0x10;

  memcpy (buff, &digData, sizeof (digData));
  PcCheckSum(buff, len);
  //    buff[Pcksum+1] = (cksum&0xff);
  //    buff[Pcksum] = (cksum>>8)&0xff;
  DMRsendTo(len);
  return DMRreceiveReply(SET_DIGITAL_CHANNEL);
}

void DMRsetAnaChannel() {
  //------------------------------------------------------------------ DMRsetAnaChannel
  //       Packet header length = 8

  // now global db_analog_info anaData;
  int len, cksum;
  anaData.head = 0x68;            //header 0x68
  anaData.CMD  = SET_ANALOG_CHANNEL ;            // command
  anaData.RW   = 1;               // operation type
  anaData.SR   = 1;               // set/response
  anaData.CKSUM = 0;              // checksum
  anaData.LEN_dummy = 0;
  anaData.LEN  = sizeof (anaData) - 9; // DATA length
  //        Data length =
  anaData.rx_freq = 433262500;     //receive  frequency    4000000000-480000000HZ
  anaData.tx_freq = 433262500;     //transmit frequency    4000000000-480000000HZ
  anaData.band = 0;       // 0:narrow 1:wide
  anaData.power = 0;      // 0:low power 1:high power
  anaData.sq = 0;         // SQ level0~9
  anaData.rx_type = 0;    // |0:carrier|1:ctcsss |2:normal DCS|3:inverse DCS
  anaData.rx_subcode = 0; // |0|   0~50  |   0~82   |  0~82
  anaData.tx_type = 0;    // |0:carrier  |1:ctcsss |2:normal DCS|3:inverse DCS
  anaData.tx_subcode = 0; // |0|   0~50  |   0~82   |  0~82
  anaData.pwrsave = 2;       //power save switch 2:disable 1:enable
  anaData.volume = 9;        //Volume 1-9
  anaData.monitor = 0;           //micgain 0~2
  anaData.relay = 1;         //relay disconnectnet 2:disable 1:enable
  anaData.tail = 0x10;
  len = sizeof(anaData);
  //Serial.println(len);
  memcpy (buff, &anaData, sizeof (anaData));
  PcCheckSum(buff, len);
  DMRsendTo(len);
  DMRreceiveReply(anaData.CMD);
}
void DMRsetAnaChannel1(uint32_t rx_freq, uint32_t tx_freq, uint8_t rx_type,
                       uint8_t rx_subcode, uint8_t tx_type, uint8_t tx_subcode)
{
  //------------------------------------------------------------------ DMRsetAnaChannel1
  //       Packet header length = 8

  // now global db_analog_info anaData;
  int len, cksum;
  anaData.head = 0x68;            //header 0x68
  anaData.CMD  = SET_ANALOG_CHANNEL ;            // command
  anaData.RW   = 1;               // operation type
  anaData.SR   = 1;               // set/response
  anaData.CKSUM = 0;              // checksum
  anaData.LEN_dummy = 0;
  anaData.LEN  = sizeof (anaData) - 9; // DATA length
  //        Data length =
  anaData.rx_freq = rx_freq;     //receive  frequency    4000000000-480000000HZ
  anaData.tx_freq = tx_freq;     //transmit frequency    4000000000-480000000HZ
  anaData.band = 0;       // 0:narrow 1:wide
  anaData.power = 1;      // 0:low power 1:high power
  anaData.sq = 3;         // SQ level0~9
  anaData.rx_type = rx_type;    // |0:carrier|1:ctcsss |2:normal DCS|3:inverse DCS
  anaData.rx_subcode = rx_subcode; // |0|   0~50  |   0~82   |  0~82
  anaData.tx_type = tx_type;    // |0:carrier  |1:ctcsss |2:normal DCS|3:inverse DCS
  anaData.tx_subcode = tx_subcode; // |0|   0~50  |   0~82   |  0~82
  anaData.pwrsave = 2;       //power save switch 2:disable 1:enable
  anaData.volume = 8;        //Volume 1-9
  anaData.monitor = 3;           //micgain 0~2
  anaData.relay = 2;         //relay disconnectnet 2:disable 1:enable
  anaData.tail = 0x10;
  len = sizeof(anaData);
  //Serial.println(len);
  memcpy (buff, &anaData, sizeof (anaData));
  PcCheckSum(buff, len);
  //  buff[Pcksum+1] = (cksum&0xff);
  //  buff[Pcksum] = (cksum>>8)&0xff;
  DMRsendTo(len);
  DMRreceiveReply(anaData.CMD);
}

void DMRsendSMS() {
  //------------------------------------------------------------------ DMRsendSMS
  //
  // Message data coded in UCS-2 http://www.columbia.edu/kermit/ucs2.html
  // 4 bytes of header filler that is undocumented (000D 000A)
  // callnum är 3 byte!! took a hell of a time to find out
  // at last I found out by running the command in the Sunrise test app
  //       Packet header length = 8
  //  db_SMSsend_info SMSData;
  int len, cksum, antsent;

  //  SMSData.head = 0x68;            //header 0x68
  //  SMSData.CMD  = 0x2D;            // command
  //  SMSData.RW   = 2;               // operation type
  //  SMSData.SR   = 1;               // set/response
  //  SMSData.CKSUM = 0;              // checksum
  //  SMSData.LEN_dummy =0;
  // // SMSData.LEN  = sizeof (SMSData) - 9; // DATA length
  //  SMSData.LEN  = sizeof (SMSData) - 9-2; // DATA length
  //
  //        Data length =
  //  SMSData.msg_type = 1;   // message typ 1:IP with confirm 2:IP without confirm 3:group call
  //  //SMSData.callNum = 2400481;     // contact DMR ID
  //  SMSData.callNum = 2400481;     // contact DMR ID
  //  SMSData.filler1 = 0x000D;
  //  SMSData.filler2 = 0x000A;
  buff[0] = 0x68;
  buff[1] = 0x2C;
  buff[2] = 0x01;
  buff[3] = 0x01;
  buff[4] = 0x00;
  buff[5] = 0x00;
  buff[6] = 0x00;
  buff[7] = 0x1B;     // len = len after len-field until but including 0x10
  buff[8] = 0x01;

  //   buff[9]=0x61;       // 2406240 om 60 2406241 om 61
  //   buff[10]=0xB7;
  //   buff[11]=0x24;

  buff[9] = 0xE1;     // 2400481
  buff[10] = 0xA0;
  buff[11] = 0x24;
  buff[12] = 0x00;    // message max len 10
  buff[13] = 0x0D;    // message max len 10
  buff[14] = 0x00;    // message max len 10
  buff[15] = 0x0A;    // message max len 10
  buff[16] = 0x00;    // message max len 10
  buff[17] = 'D';    // message max len 10
  buff[18] = 0x00;    // message max len 10
  buff[19] = 'E';    // message max len 10
  buff[20] = 0x00;    // message max len 10
  buff[21] = ' ';    // message max len 10
  buff[22] = 0x00;    // message max len 10
  buff[23] = 'S';    // message max len 10
  buff[24] = 0x00;    // message max len 10
  buff[25] = 'M';    // message max len 10
  buff[26] = 0x00;    // message max len 10
  buff[27] = '7';    // message max len 10
  buff[28] = 0x00;    // message max len 10
  buff[29] = 'E';    // message max len 10
  buff[30] = 0x00;    // message max len 10
  buff[31] = 'C';
  buff[32] = 0x00;
  buff[33] = 'A';
  buff[34] = 0x00;
  buff[35] = 0x10;
  len = 36;
  PcCheckSum(buff, len);
  //  DMRDebug = false;
  DMRsendTo(len);
  DMRreceiveReply(0x2C);
  //  DMRDebug = false;
}

void DMRsendSMS_2D() {
  //------------------------------------------------------------------ DMRsendSMS_2D
  //  0x2D - don´t know how to use this command
  // Message data coded in UCS-2 http://www.columbia.edu/kermit/ucs2.html
  // 4 bytes of header filler that is undocumented (000D 000A)
  // callnum är 3 byte!! took a hell of a time to find out
  // at last I found out by running the command in the Sunrise test app
  //       Packet header length = 8

  //  db_SMSsend_info SMSData;
  int len, cksum, antsent;

  //  SMSData.head = 0x68;            //header 0x68
  //  SMSData.CMD  = 0x2D;            // command
  //  SMSData.RW   = 2;               // operation type
  //  SMSData.SR   = 1;               // set/response
  //  SMSData.CKSUM = 0;              // checksum
  //  SMSData.LEN_dummy =0;
  // // SMSData.LEN  = sizeof (SMSData) - 9; // DATA length
  //  SMSData.LEN  = sizeof (SMSData) - 9-2; // DATA length
  //
  //        Data length =
  //  SMSData.msg_type = 1;   // message typ 1:IP with confirm 2:IP without confirm 3:group call
  //  //SMSData.callNum = 2400481;     // contact DMR ID
  //  SMSData.callNum = 2400481;     // contact DMR ID
  //  SMSData.filler1 = 0x000D;
  //  SMSData.filler2 = 0x000A;
  buff[0] = 0x68;
  buff[1] = 0x2D;
  buff[2] = 0x02;
  buff[3] = 0x01;
  buff[4] = 0x00;
  buff[5] = 0x00;
  buff[6] = 0x00;
  buff[7] = 0x1A;     // len = len after len-field until but including 0x10
  buff[8] = 0x01;
  //   buff[8]=0xE1;       // 2400481
  //   buff[9]=0xA0;
  //   buff[10]=0x24;
  buff[11] = 0x00;    // message max len 10
  buff[12] = 0x0D;    // message max len 10
  buff[13] = 0x00;    // message max len 10
  buff[14] = 0x0A;    // message max len 10
  buff[15] = 0x00;    // message max len 10
  buff[16] = 'D';    // message max len 10
  buff[17] = 0x00;    // message max len 10
  buff[18] = 'E';    // message max len 10
  buff[19] = 0x00;    // message max len 10
  buff[20] = ' ';    // message max len 10
  buff[21] = 0x00;    // message max len 10
  buff[22] = 'S';    // message max len 10
  buff[23] = 0x00;    // message max len 10
  buff[24] = 'M';    // message max len 10
  buff[25] = 0x00;    // message max len 10
  buff[26] = '7';    // message max len 10
  buff[27] = 0x00;    // message max len 10
  buff[28] = 'E';    // message max len 10
  buff[29] = 0x00;    // message max len 10
  buff[30] = 'C';
  buff[31] = 0x00;
  buff[32] = 'A';
  buff[33] = 0x00;
  buff[34] = 0x10;
  len = 35;
  PcCheckSum(buff, len);
  // DMRDebug = false;
  DMRsendTo(len);
  DMRreceiveReply(0x2D);
  // DMRDebug = false;
}
void DMRsetaudioVolume()
//------------------------------------------------------------- DMRsetaudioVolume
{
  DMRTransmit(audioVolume, SET_VOLUME);
  NX_P0_showVol();
}

void DMRsetMicVolume(byte micVolume)
{
  DMRTransmit(micVolume, SET_MIC_GAIN);
}

boolean DMRcheckRSSI()
//------------------------------------------------------------- DMRcheckRSSI
//
// signal strength > 0 = receive audio
{
  DMRTransmit(FUNC_ENABLE, QUERY_SIGNAL_STRENGTH);
  if (buff[8] > 0)
  {
    return true;
  } else return false;
}

boolean DMRcheckSMSRec()
//-------------------------------------------------------------- DMRcheckSMSRec
//
// check SMS received - SMS is copied to a separat buffer when received
{
  String  SMSmessage;
  Serial.print(buff[7], DEC);
  for (int i = 15; i <= 11 + buff[7] - 4; i++)
  {
    if (i & 0x01)
    { // ==> odd     //  bit magic
      SMSmessage = SMSmessage + String((char)buff[i]);
      Serial.print(String((char)buff[i]));
      Serial.print(" ");
    }
  }
  //    rxContact =  (uint32_t)buff[11]<<24|(uint32_t)buff[10]<<16|
  //                        (uint32_t)buff[9]<<8|(uint32_t)buff[8];
  rxContact =  (uint32_t)buff[11] << 16 |
               (uint32_t)buff[10] << 8 | (uint32_t)buff[9];
  ltoa(rxContact, rxContactChar, 10);
  //    Serial.print(rxContactChar);
  readradioid(rxContact);
  NX_P8_viewSMS(rxContactChar, SMSmessage);
}
boolean  DMRqueryReceived(boolean receiving)
//-------------------------------------------------------------- DMRqueryReceived
//
// Display DMR ID and other relevant info of received station
{
  //DMRDebug =false;
  if (DMRTransmit(FUNC_ENABLE, QUERY_DIGITAL_VOICE_INFO) and buff[12] == 0x0) // query received data
  {
    rxContact =  (uint32_t)buff[12] << 24 | (uint32_t)buff[11] << 16 |
                 (uint32_t)buff[10] << 8 | (uint32_t)buff[9];
    rxGroup =  (uint32_t)buff[16] << 24 | (uint32_t)buff[15] << 16 |
               (uint32_t)buff[14] << 8 | (uint32_t)buff[13];
    Serial.print(rxGroup);
    Serial.print(" ");
    Serial.print(rxContact);
    Serial.print(" ts:");
    Serial.print(" ");
    Serial.print(digData.InboundSlot + 1);
    Serial.print(" - ");
  }
  else
  {
    rxContact = 0;
  }
  if (rxContact > 0)
  {
    if (receiving)
    {
      ltoa(rxContact, rxContactChar, 10);
      //      Serial.print(rxContactChar);

      readradioid(rxContact);
      //     DisplayReceive(true, buff[8], rxContact);
      NX_P0_DisplayReceive(true, buff[8], rxContact);
    }
    return true;
  }
  return false;
}

void DMRinitChannel()
//----------------------------------------------------------- DMRinitChannel
{
  DBgetTG(currepTG.tg_id);
  //calculateFreq(curdigCh.IARUchannel);
  DMRsetDigChannel(curdigCh.rx, curdigCh.tx, currepTG.tg_id,
                   curTG.calltype, curdigCh.cc, currepTG.ts, 0, 2);
}

boolean DMRgetVersion()
//----------------------------------------------------------- displayVersion
//
// Query DMR module version and display on oled, last line (unused for now)

{
  return (DMRTransmit(FUNC_ENABLE, QUERY_VERSION));
}
