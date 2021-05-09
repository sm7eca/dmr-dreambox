
char  EIMrepeaterUrl[] = "http://dmrdream.com/api/v1/repeater/callsign/";
char  EIMrepeaterLocationUrl[] = "http://dmrdream.com/api/v1/repeater/location";
char  EIMDMRUrl[] = "http://dmrdream.com/api/v1/dmr/";

char  EIMhotspotUrl[] = "http://dmrdream.com/api/v1/hotspot/callsign/";
char  EIMstatusUrl[] = "http://dmrdream.com/api/v1/system/info";

void  EIMeraseRepHotspot(uint8_t k)
//-----------------------------------------------------------------------------------
{
  dmrSettings.repeater[k].zone  = 0;
  dmrSettings.repeater[k].dmrId = 0;
}
boolean  EIMreadStatus()
//-----------------------------------------------------------------------------------
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    http.begin(EIMstatusUrl);
    uint16_t httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Debug.println(payload);
        StaticJsonDocument<300> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (error)
        {
          Debug.print(F("deserializeJson() failed: "));
          Debug.println(error.f_str());
          return false;
        }
        const char* uptime = doc["uptime"]; // "134882s"
        const char* version = doc["version"]; // "0.1.1"
        const char* maintainer = doc["maintainer"]; // "Arne Nilsson"
        uint32_t repeater = doc["repeater"]; // 15431        switch (err.code())
                Debug.println(uptime);
                Debug.println(version);
                Debug.println(maintainer);
                Debug.println(repeater);
        return true;
      }
    }
  }
  return false;
}
boolean EIMdeserializeRepHot(String payload)
//-----------------------------------------------------------------------------------
{
  //  Debug.println(payload);
  StaticJsonDocument<384> doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error)
  {
    Debug.print(F("deserializeJson() failed: "));
    Debug.println(error.f_str());
    return false;
  }
  uint32_t  dmr_id = doc["dmr_id"];
  uint32_t  tx = doc["tx"];
  uint32_t  rx = doc["rx"];
  uint8_t cc = doc["cc"];
  uint8_t max_ts = doc["max_ts"];
  const char *name = doc["name"];
  const char *location = doc["location"];
  return true;
}
boolean EIMreadRepeatersMaster(uint16_t master, uint8_t limit, uint8_t skip)
//-----------------------------------------------------------------------------------
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 50];
    sprintf(combinedArray, "%smaster/%u?limit=%u&skip=%u", EIMrepeaterUrl, master, limit, skip); // with word space
    Debug.println("EIMreadRepeatersMaster");
    Debug.println(combinedArray);
    http.begin(combinedArray);
    uint16_t httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Debug.println(payload);
        if (EIMdeserializeRepHot(payload))
        {
          return true;
        }
      }
    }
  }
  return false;
}

boolean EIMdeserializeRepHotList(String payload)
//-----------------------------------------------------------------------------------
{
  DynamicJsonDocument doc(9000);
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Debug.print(F("deserializeJson() failed: "));
    Debug.println(error.f_str());
    return false;
  }
  reptemplistCurLen = 0;
  uint8_t k = 0;
  for (JsonObject elem : doc.as<JsonArray>())
  {
    uint32_t  dmr_id = elem["dmr_id"];
    uint32_t  tx = elem["tx"];
    uint32_t  rx = elem["rx"];
    uint8_t cc = elem["cc"];
    const char* name = elem["name"];
    const char* location = elem["location"];
    const char* city = elem["city"];
    if (tx > 432000000 and tx < 439000000 and dmr_id < 9999999
        and reptemplistCurLen <= reptemplistMaxLen)
    {

      reptemplist[k].dmrId = dmr_id;
      reptemplist[k].tx = rx;
      reptemplist[k].rx = tx;
      reptemplist[k].cc = cc;
      reptemplist[k].timeSlot = 1;
      //     reptemplist[k].timeSlotNo = max_ts;
      strcpy(reptemplist[k].repeaterName, name);
      const char* location = location;
      strcpy(reptemplist[k].repeaterLoc, city);
      k++;
      reptemplistCurLen = k;
    }
  }
  Debug.println(reptemplistCurLen);
  return true;
}

boolean EIMreadRepeatersLocation(char* longitude, char* latitude, uint16_t distance)
//-----------------------------------------------------------------------------------
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterLocationUrl)  + 100];
    sprintf(combinedArray, "%s?longitude=%s&latitude=%s&distance=%u&limit=14&skip=0", EIMrepeaterLocationUrl, longitude, latitude, distance); // with word space
    Debug.println("EIMreadRepeatersLocation");
    Debug.println(combinedArray);
    http.begin(combinedArray);
    uint16_t httpCode = http.GET();
    Debug.println(httpCode);
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        if (EIMdeserializeRepHotList(payload))
        {
          return true;
        }
        else
        {
          return false;
        }
      }
    }
  }
  return false;
}

boolean EIMreadHotspots(char* callsign)
//-----------------------------------------------------------------------------------
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 50];
    sprintf(combinedArray, "%s%s", EIMhotspotUrl, callsign); // with word space
    Debug.println("EIMreadHotspots");
    Debug.println(combinedArray);
    http.begin(combinedArray);
    uint16_t httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Debug.println(payload);
        if (EIMdeserializeRepHot(payload))
        {
          return true;
        }
      }
    }
  }
  return false;
}
boolean EIMdeserializeSingleRepeater(String input, uint8_t k)
//-----------------------------------------------------------------------------------
{
  // String input;
  StaticJsonDocument<1536> doc;

  DeserializationError error = deserializeJson(doc, input);

  if (error) {
    Debug.print(F("deserializeJson() failed: "));
    Debug.println(error.f_str());
    return false;
  }
  dmrSettings.repeater[k].dmrId = doc["dmr_id"]; // 240701
  dmrSettings.repeater[k].rx = doc["tx"]; // 434587500
  dmrSettings.repeater[k].tx = doc["rx"]; // 432587500
  dmrSettings.repeater[k].cc = doc["cc"]; // 7
  dmrSettings.repeater[k].timeSlot = 1;
  dmrSettings.repeater[k].timeSlotNo = doc["max_ts"]; // 0
  strcpy(dmrSettings.repeater[k].repeaterName, doc["name"]); // "SK7RJL"
  const char* location = doc["location"]; // "55.720459,13.222694"
  strcpy(dmrSettings.repeater[k].repeaterLoc, doc["city"]); // "Lund"
  uint8_t num_tg = doc["num_tg"];
  uint8_t x = 0;
  for (uint8_t i = 0; i < 10; i++)
  {
    dmrSettings.repeater[k].groups[i].tg_id = 0;
    dmrSettings.repeater[k].groups[i].ts = 0;
  }
  if (num_tg > 0)
  {
    if (num_tg > 10)
    {
      num_tg = 10;
    }
    for (JsonObject elem : doc["tg"].as<JsonArray>())
    {
      if (x < num_tg)
      {
        dmrSettings.repeater[k].groups[x].tg_id = elem["tg_id"];
        dmrSettings.repeater[k].groups[x].ts = elem["ts"];
        //    bool is_dynamic = elem["is_dynamic"];
      }
      x++;
    }
  }
  sprintf(NXrepeaterName, "%s. %s", dmrSettings.repeater[k].repeaterName, dmrSettings.repeater[k].repeaterLoc);
//  EIMprintDMRsettingsitem(k);
  return true;
}
boolean EIMreadRepeaterDMRid(char* DMRid, uint8_t k)
//-----------------------------------------------------------------------------------
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 1536];
    sprintf(combinedArray, "%s%s", EIMDMRUrl, DMRid); // with word space
    Debug.println("EIMreadRepeaterDMRid");
    Debug.println(combinedArray);
    http.begin(combinedArray);
    uint16_t httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Debug.println(payload);
        if (EIMdeserializeSingleRepeater(payload, k))
        {
          return true;
        }
      }
    }
  }
  return false;
}
void  EIMprintDMRsettingsitem(uint8_t k)
{
  Debug.println("chnr: ");
  Debug.println(k);
  Debug.print(dmrSettings.repeater[k].chnr);
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].dmrId); // 240701
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].rx); // 434587500
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].tx); // 432587500
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].cc); // 7
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].timeSlot);
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].timeSlotNo); // 0
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].repeaterName); // "SK7RJL"
  Debug.print(" ");
  Debug.print(dmrSettings.repeater[k].repeaterLoc); // "Lund"
  Debug.println();
  for (uint8_t x = 0; x < 10; x++)
  {
    Debug.print(dmrSettings.repeater[k].groups[x].tg_id);
    Debug.print(" ");
    Debug.print(dmrSettings.repeater[k].groups[x].ts);
    Debug.print(" ");
  }
  Debug.println();
}
