//============================================================ Main table area
//----------------------------------------------------------- Channel base struct
typedef struct  {
  //Digital hotspot and repeater data
  uint8_t  zone;            //zone no = collection of repeaters or hotspots, not used yet
  uint8_t  chnr;            //internal channel for sorting and scrolling
  uint32_t DMRid;           //DMRid för repeater eller Hotspot
  uint32_t tx;              // tx freq
  uint32_t rx;              // rx freq
//  uint16_t IARUchannel;      //freq.channel according to IARU like RUxxx and Uxxx, but saved without prefix.
//  uint8_t  power;           //0:low power  1：high power
  uint8_t  cc;              //color code0~15
  uint8_t  TimeSlot;        //0:slot 1 1:slot 2  TS numbering like the 22 command states (Current time slot when active)
  uint8_t  TimeSlotNo;       //number of time slots 1 or 2.
  uint8_t  ChannelMode;     //0:direct connection mode 4: true dual slot (DMR tier 2)
  char     Name[15];        //name of the channel, 14 chars
  char     Location[15];    //location of device Hotspot or repeater, 14 chars
} digCh;
uint16_t maxdigChlist = 100; //current highest index of records in CHlist (number of records - 1)
uint16_t startrow = 0;    //only c channels will show on  the display at a time. Will be incremented
// or decremented with p4_numRows when scrolling on page 4
digCh digChlist[100] = {
  {0,   0, 240048102, 433262500,433262500,    1, 2, 1 ,0, "Min Hotspot",   "At home"},
  {0,   1, 240618,    434587500,432587500,    6, 1, 2, 0, "SK6JX",         "Falkenberg"},
  {0,   2, 240701,    434587500,432587500,    7, 1, 2, 0, "SK7RJL",        "Lund"},
  {0,   3, 240711,    434775000,432775000,    7, 1, 2, 0, "SK7RJL",        "Malmö"},
  {0,   4, 240048103, 433262500,433262500,    1, 1, 1, 0, "BMin Hotspot",  "At home"},
  {0,   5, 240619,    434587500,432587500,    6, 1, 2, 0, "BSK6JX",        "Falkenberg"},
  {0,   6, 240702,    434587500,432587500,    7, 1, 2, 0, "BSK7RJL",       "Lund"},
  {0,   7, 240712,    434775000,432775000,    7, 1, 2, 0, "BSK7RJL",       "Malmö"},
  {0, 255, 0,         0,        0,            0, 0, 0, 0, " ",              " "}
};

digCh curdigCh;

//----------------------------------------------------------- Repeater static TG
typedef struct  {
  uint32_t  DMRid;
  uint32_t  TG;
  uint8_t  TS;
} repTG;

uint16_t maxrepTGlist = 200;      //current highest index of records in repTGlist (number of records - 1)

repTG currepTG;
repTG repTGlist[200] =
{
  {240618, 240, 2},
  {240618, 2406, 1},
  {240618, 2407, 2},
  {240618, 9990, 1},
  {240701, 240, 2},
  {240701, 2401, 1},
  {240701, 2402, 1},
  {240701, 2403, 1},
  {240701, 2404, 1},
  {240701, 2405, 1},
  {240701, 2406, 1},
  {240701, 2407, 1},
  {240701, 2407, 2},
  {240701, 9990, 1},
  {240701, 240240, 1},
  {240711, 8, 2},
  {240711, 2401, 1},
  {240711, 2402, 1},
  {240711, 2403, 1},
  {240711, 2404, 1},
  {240711, 2405, 1},
  {240711, 2406, 1},
  {240711, 2407, 1},
  {240711, 9990, 1},
  {240711, 240711, 2},
  {240048102, 2401, 2},
  {240048102, 2402, 2},
  {240048102, 2403, 2},
  {240048102, 2404, 2},
  {240048102, 2405, 2},
  {240048102, 2406, 2},
  {240048102, 2407, 2},
  {240048102, 2410, 2},
  {240048102, 2412, 2},
  {240048102, 9990, 2},
  {240048102, 24061, 2},
  {240048102, 24062, 2},
  {240048102, 24077, 2},
  {240048102, 240850, 2},
  {240048102, 240240, 2},
  {240619, 240, 2},
  {240619, 2406, 1},
  {240619, 2407, 2},
  {240619, 9990, 1},
  {240702, 240, 2},
  {240702, 2401, 1},
  {240702, 2402, 1},
  {240702, 2403, 1},
  {240702, 2404, 1},
  {240702, 2405, 1},
  {240702, 2406, 1},
  {240702, 2407, 1},
  {240702, 2407, 2},
  {240702, 9990, 1},
  {240702, 240240, 1},
  {240712, 8, 2},
  {240712, 2401, 1},
  {240712, 2402, 1},
  {240712, 2403, 1},
  {240712, 2404, 1},
  {240712, 2405, 1},
  {240712, 2406, 1},
  {240712, 2407, 1},
  {240712, 9990, 1},
  {240712, 240711, 2},
  {240048103, 2401, 2},
  {240048103, 2402, 2},
  {240048103, 2403, 2},
  {240048103, 2404, 2},
  {240048103, 2405, 2},
  {240048103, 2406, 2},
  {240048103, 2407, 2},
  {240048103, 2410, 2},
  {240048103, 2412, 2},
  {240048103, 9990, 2},
  {240048103, 24061, 2},
  {240048103, 24062, 2},
  {240048103, 24077, 2},
  {240048103, 240850, 2},
  {240048103, 240240, 2},
  {9999999,   0,      0}
};
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
  {240711,"Östersjölänken",1,1},
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
digCh NXp4Ch[6];
repTG NXp5repTG[6];
TG    NXp5TG[6];
TG    NXp6TG[6];
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
  for (int i = 0; i <= numradioid; i++)
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
      for (int j = i - 1; j >= 0; j--)
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

  wifiGetDMRID();
}
void insertradioid()
//------------------------------------------------------ insert radioid
// when an DMRid is found at radioid.org, the info is stored in ri_list
// the last xx calls are stored in the list. It is round robin logic when
// new id shall be stored.
{
  for (int j = numradioid; j >= 0; j--)
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
boolean DBgetChannel(uint8_t rowno)
//------------------------------------------------------ DBgetChannel
{
  for (int i = 0; i <= maxdigChlist; i++)
  {
    if (digChlist[i].chnr == 255)
    {
      return false;
    }
    if (digChlist[i].chnr == rowno)
    {
      curdigCh = digChlist[rowno];
      return true;
    }
  }
  return false;
}
boolean DBgetrepTG(uint32_t DMRid, uint32_t TG)
//------------------------------------------------------ DBgetrepTG
{
  for (int i = 0; i <= maxrepTGlist; i++)
  {
    if (repTGlist[i].DMRid == 9999999)
    {
      return false;
    }
    if (repTGlist[i].DMRid == DMRid and repTGlist[i].TG == TG)
    {
      currepTG = repTGlist[i];
      if (!DBgetTG(repTGlist[i].TG))
      {
        Serial.print("TG not found ");
        Serial.print(repTGlist[i].TG);
      }
      return true;
    }
  }
  return false;
}

boolean DBgetTG(uint32_t TG)
//------------------------------------------------------ DBgetrepTG
{
  for (int j = 0; j <= maxTGlist; j++)
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
