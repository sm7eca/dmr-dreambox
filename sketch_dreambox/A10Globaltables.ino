//============================================================ Main table area
//----------------------------------------------------------- Channel base struct
//typedef struct  {
//  //Digital hotspot and repeater data
//  uint8_t  zone;            //zone no = collection of repeaters or hotspots, not used yet
//  uint8_t  chnr;            //internal channel for sorting and scrolling
//  uint32_t DMRid;           //DMRid för repeater eller Hotspot
//  uint32_t tx;              // tx freq
//  uint32_t rx;              // rx freq
//  uint8_t  cc;              //color code0~15
//  uint8_t  TimeSlot;        //0:slot 1 1:slot 2  TS numbering like the 22 command states (Current time slot when active)
//  uint8_t  TimeSlotNo;       //number of time slots 1 or 2.
//  uint8_t  ChannelMode;     //0:direct connection mode 4: true dual slot (DMR tier 2)
//  char     Name[15];        //name of the channel, 14 chars
//  char     Location[15];    //location of device Hotspot or repeater, 14 chars
//} digCh;
//
//--------------------------------- new version digChS 
//typedef struct digChS{
//  uint8_t chnr;
//  RepeaterS digRep;
//}digChS;


//--------------------------------- temporay Channel while scrolling on page 4 and 5
RepeaterS tmpdigCh;

//----------------------------------------------------------- Repeater static TG
//typedef struct  {
//  uint32_t  DMRid;
//  uint32_t  TG;
//  uint8_t  TS;
//} repTG;

//uint16_t maxrepTGlist = 200;      //current highest index of records in repTGlist (number of records - 1)
//
//repTG currepTG;
//repTG repTGlist[200];
//----------------------------------------------------------- replace by tmpdigCh.groups


//----------------------------------------------------------- Talk Groups
typedef struct {              // Talk Group list
  uint32_t  TG;
  char  TGname[20];
  uint8_t calltype;
  uint8_t rxgroup;
} TG ;
uint8_t  maxTGlist = 29;  //current highest index of records in TGlist (number of records - 1)
TG  curTG;
TG TGlist[29] =
{
  {7, "Lokalt kluster", 1, 0},
  {8, "Lokalt kluster", 1, 0},
  {9, "Lokalt repeater", 1, 1},
  {240, "Sweden", 1, 1},
  {2400, "Regional SM0", 1, 1},
  {2401, "Regional SM1", 1, 1},
  {2402, "Regional SM2", 1, 1},
  {2403, "Reg. SM3", 1, 1},
  {2404, "Reg. SM4", 1, 1},
  {2405, "Reg. SM5", 1, 1},
  {2406, "Reg. SM6", 1, 1},
  {2407, "Reg. SM7", 1, 1},
  {2410, "Nat.QSO grp", 1, 1},
  {2411, "Nat.QSO grp", 1, 1},
  {2412, "Nat.QSO grp", 1, 1},
  {2415, "Nat.QSO grp", 1, 1},
  {2416, "Swedenlink", 1, 1},
  {9990, "Parrot", 0, 0},
  {24062, "Reg. Taktisk SM6", 1, 1},
  {24077, "SM7 QSO grupp", 1, 1},
  {240711, "Östersjölänken", 1, 1},
  {24098, "Robust Packet", 1, 1},
  {240216, "Swedenhub", 1, 1},
  {240240, "Brygga till D-Star", 1, 1},
  {240850, "Teknikrummet", 1, 1},
  {240888, "SM Openspot", 1, 1},
  {240907, "JOTA SE", 1, 1},
  {240999, "APRS", 0, 0},
  {9999999, "the end ", 0, 0}
};
//----------------------------------------------------------- Call types struct
typedef struct
{
  uint8_t calltype;
  char    ctname[10];
} callType;
uint8_t  maxCTlist = 3; //current highest index of records in CTlist (number of records - 1)
callType  curcalltype;
callType CTlist[3] =
{
  {0, "Personal"},
  {1, "Group"},
  {99, "the end"}
};
//========================================================== Display variables
//digCh NXp4Ch[10];
//repTG NXp5repTG[10];
RepeaterS NXp4Ch[10];
TalkGroupS NXp5repTG[10];

TG    NXp5TG[10];
TG    NXp6TG[10];
//----------------------------------------------------------- DMRid of received messages
// this is a list of last heard DMRids. Maintained mainly to avoid doing excess Internet calls
// to the Webservices Radioid and the swedish local list that I set up myself for this project
//

Radioid ri_list[100];
uint8_t numradioid = 0;     //number of filled positions = maxradioid when tabel is filled
uint8_t maxradioid = 99;    //maximum in list

void readradioid(uint32_t rxContact)
//----------------------------------------------------- readradioid
//  the last received DMRids are stored in ri_list.
//  Search this list before accessing radioid.org
{
  for (int8_t i = 0; i <= numradioid; i++)
  {
    //        if (ri_list[i].ri_id==rxContact and ri_list[i].ri_talkgroup==rxGroup
    if (ri_list[i].ri_id == rxContact)
    {
      ri_callsign = ri_list[i].ri_callsign;
      ri_talkgroup = rxGroup;
      ri_fname = ri_list[i].ri_fname;
      ri_surname = ri_list[i].ri_surname;
      ri_state = ri_list[i].ri_state;
      ri_city = ri_list[i].ri_city;
      ri_country = ri_list[i].ri_country;
      ri_id = ri_list[i].ri_id;
      ri_list[i].ri_count++;
      ri_count = ri_list[i].ri_count;
      for (int8_t j = i - 1; j >= 0; j--)
      {
        ri_list[j + 1].ri_callsign = ri_list[j].ri_callsign;
        ri_list[j + 1].ri_talkgroup = ri_list[j].ri_talkgroup;
        ri_list[j + 1].ri_fname = ri_list[j].ri_fname;
        ri_list[j + 1].ri_surname = ri_list[j].ri_surname;
        ri_list[j + 1].ri_state = ri_list[j].ri_state;
        ri_list[j + 1].ri_city = ri_list[j].ri_city;
        ri_list[j + 1].ri_country = ri_list[j].ri_country;
        ri_list[j + 1].ri_id = ri_list[j].ri_id;
        ri_list[j + 1].ri_count = ri_list[j].ri_count;
      }
      ri_list[0].ri_callsign = ri_callsign;
      ri_list[0].ri_talkgroup = ri_talkgroup;
      ri_list[0].ri_fname =   ri_fname;
      ri_list[0].ri_surname = ri_surname;
      ri_list[0].ri_state = ri_state;
      ri_list[0].ri_city = ri_city;
      ri_list[0].ri_country = ri_country;
      ri_list[0].ri_id = ri_id;
      ri_list[0].ri_count = ri_count;

      Serial.print("** ");
      Serial.print(ri_callsign);
      Serial.print(" ");
      Serial.print(ri_fname);
      Serial.print(" ");
      Serial.print(ri_surname);
      Serial.print(" ");
      Serial.print(ri_city);
      Serial.print(" ");
      Serial.print(ri_state);
      Serial.print(" ");
      Serial.print(ri_country);
      Serial.print(", ");
      Serial.print(ri_list[i].ri_count);
      return;
    }
  }
  Serial.println("Goto wifiGetDMRID(): ");
  wifiGetDMRID();
}
void insertradioid()
//------------------------------------------------------ insert radioid
// when an DMRid is found at radioid.org, the info is stored in ri_list
// the last xx calls are stored in the list. It is round robin logic when
// new id shall be stored.
{
  for (int8_t j = numradioid; j >= 0; j--)
  {
    Serial.println("insertradioid()-1");
    Serial.println(numradioid);
    Serial.println(j);
    ri_list[j + 1].ri_callsign = ri_list[j].ri_callsign;
    ri_list[j + 1].ri_talkgroup = ri_list[j].ri_talkgroup;
    ri_list[j + 1].ri_fname = ri_list[j].ri_fname;
    ri_list[j + 1].ri_surname = ri_list[j].ri_surname;
    ri_list[j + 1].ri_state = ri_list[j].ri_state;
    ri_list[j + 1].ri_city = ri_list[j].ri_city;
    ri_list[j + 1].ri_country = ri_list[j].ri_country;
    ri_list[j + 1].ri_id = ri_list[j].ri_id;
    ri_list[j + 1].ri_count = ri_list[j].ri_count;
  }
  Serial.println("insertradioid()-2");
  ri_list[0].ri_callsign = ri_callsign;
  ri_list[0].ri_talkgroup = rxGroup;
  ri_list[0].ri_fname =   ri_fname;
  ri_list[0].ri_surname = ri_surname;
  ri_list[0].ri_state = ri_state;
  ri_list[0].ri_city = ri_city;
  ri_list[0].ri_country = ri_country;
  ri_list[0].ri_id = ri_id;
  ri_list[0].ri_count = 1;
  numradioid++;
  if (numradioid >= maxradioid)
  {
    numradioid = maxradioid;
  }
}
//boolean DBgetChannel(uint8_t rowno)
//------------------------------------------------------ DBgetChannel
//{
//  for (uint8_t i = 0; i <= maxdigChlist; i++)
//  {
//    if (digChlist[i].chnr == 255)
//    {
//      return false;
//    }
//    if (digChlist[i].chnr == rowno)
//    {
//      curdigCh = digChlist[rowno];
//      return true;
//    }
//  }
//  return false;
//}
//boolean DBgetrepTG(uint32_t DMRid, uint32_t TG)
////------------------------------------------------------ DBgetrepTG
//{
//  for (uint8_t i = 0; i <= maxrepTGlist; i++)
//  {
//    if (repTGlist[i].DMRid == 9999999)
//    {
//      return false;
//    }
//    if (repTGlist[i].DMRid == DMRid and repTGlist[i].TG == TG)
//    {
//      currepTG = repTGlist[i];
//      if (!DBgetTG(repTGlist[i].TG))
//      {
//        Serial.print("TG not found ");
//        Serial.print(repTGlist[i].TG);
//      }
//      return true;
//    }
//  }
//  return false;
//}

boolean DBgetTG(uint32_t TG)
//------------------------------------------------------ DBgetrepTG
{
  for (uint8_t j = 0; j <= maxTGlist; j++)
  {
    if (TGlist[j].TG == 9999999)
    {
      return false;
    }
    if (TGlist[j].TG == TG)
    {
      curTG = TGlist[j];
      return true;
    }
  }
  return false;
}
boolean DBgetsingleChannel(uint8_t rowno)
//------------------------------------------------------ 
{
  if (rowno>=maxRepeaters or rowno<0)
  {
    return false;
  }
  if (dmrSettings.repeater[rowno].dmrId==0)
  {
    return false;
  }
  tmpdigCh.chnr=rowno;
  tmpdigCh =dmrSettings.repeater[rowno];
  return true;
}

boolean DBgetnextChannel(int8_t rowno)
//------------------------------------------------------ 
{
//  Serial.println("DBgetnextChannel: ");
  if (rowno+1>=maxRepeaters)
  {
    Serial.print("DBgetnextChannel:end of array ");
    Serial.println(rowno);
    return false;
  }
  rowno++;
  for (uint8_t k=rowno;rowno<numManualRep and (dmrSettings.repeater[rowno].dmrId==0);k++)
  {
      rowno++;
  }
  if (dmrSettings.repeater[rowno].dmrId==0)
  {
    Serial.print("DBgetnextChannel:end of data: ");
    Serial.println(rowno);
    return false;
  }
  tmpdigCh =dmrSettings.repeater[rowno];
  return true;
}
boolean DBgetsinglerepTG(uint8_t rowno)
//------------------------------------------------------ DBgetrepTG
{
  if (rowno>=maxRepTG)
  {
    return false;
  }
  if (NXp4Ch[p4_selectedRow].groups[rowno].tg_id==0)
  {
    return false;
  }
//  tmpdigCh.chnr=rowno;
  currepTG = NXp4Ch[p4_selectedRow].groups[rowno];
  return true;
}
