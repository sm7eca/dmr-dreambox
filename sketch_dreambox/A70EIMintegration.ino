
char  EIMrepeaterUrl[] = "http://api.dmrdream.com/repeater/";
char  EIMrepeaterDMRUrl[] = "http://api.dmrdream.com/dmr/";
char  EIMhotspotUrl[] = "http://api.dmrdream.com/hotspot/callsign/";
char  EIMstatusUrl[] = "http://api.dmrdream.com/system/info";

void  EIMeraseRepHotspot(int k)
{
  dmrSettings.repeater[k].zone  = 0;
  dmrSettings.repeater[k].dmrId = 0;
}
void  EIMreadStatus()
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    http.begin(EIMstatusUrl);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        StaticJsonDocument<300> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (error)
        {
          Serial.print(F("deserializeJson() failed: "));
          Serial.println(error.f_str());
          return;
        }
        const char* uptime = doc["uptime"]; // "134882s"
        const char* version = doc["version"]; // "0.1.1"
        const char* maintainer = doc["maintainer"]; // "Arne Nilsson"
        long repeater = doc["repeater"]; // 15431        switch (err.code())
        Serial.println(uptime);
        Serial.println(version);
        Serial.println(maintainer);
        Serial.println(repeater);
      }
    }
  }
}
boolean EIMdeserializeRepHot(String payload)
{
  //  Serial.println(payload);
  StaticJsonDocument<384> doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error)
  {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return false;
  }
  long dmr_id = doc["dmr_id"];            // 24060811
  long tx = doc["tx"];                    // 436600000
  long rx = doc["rx"];                    // 432600000
  int cc = doc["cc"];                     // 4
  int max_ts = doc["max_ts"];             // 1
  const char *name = doc["name"];         // "SQ7JSK"
  const char *location = doc["location"]; // "Falkenberg"
  Serial.println(dmr_id);
  Serial.println(tx);
  Serial.println(rx);
  Serial.println(cc);
  Serial.println(max_ts);
  Serial.println(name);
  Serial.println(location);
}
boolean EIMreadRepeatersMaster(int master, int limit, int skip)
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 50];
    sprintf(combinedArray, "%smaster/%u?limit=%u&skip=%u", EIMrepeaterUrl, master, limit, skip); // with word space
    Serial.println("EIMreadRepeatersMaster");
    Serial.println(combinedArray);
    http.begin(combinedArray);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        if (EIMdeserializeRepHot(payload))
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
}
boolean EIMreadRepeatersDistance(char* city, char* country, int distance, int limit, int skip)
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 80];
    sprintf(combinedArray, "%slocation?city=%s&country=%s&distance=%u&limit=%u&skip=%u", EIMrepeaterUrl, city, country, distance, limit, skip); // with word space
    Serial.println("EIMreadRepeatersDistance");
    Serial.println(combinedArray);
    http.begin(combinedArray);
    int httpCode = http.GET();
    Serial.print(httpCode);
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        if (EIMdeserializeRepHot(payload))
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
}

boolean EIMreadHotspots(char* callsign)
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 50];
    sprintf(combinedArray, "%s%s", EIMhotspotUrl, callsign); // with word space
    Serial.println("EIMreadHotspots");
    Serial.println(combinedArray);
    http.begin(combinedArray);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        if (EIMdeserializeRepHot(payload))
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
}
boolean EIMdeserializeSingleRepeater(String input, int k)
{
  // String input;

  StaticJsonDocument<1536> doc;

  DeserializationError error = deserializeJson(doc, input);

  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return false;
  }

  dmrSettings.repeater[k].dmrId = doc["dmr_id"]; // 240701
  dmrSettings.repeater[k].tx = doc["tx"]; // 434587500
  dmrSettings.repeater[k].rx = doc["rx"]; // 432587500
  dmrSettings.repeater[k].cc = doc["cc"]; // 7
  dmrSettings.repeater[k].timeSlot = 1;
  dmrSettings.repeater[k].timeSlotNo = doc["max_ts"]; // 0
  strcpy(dmrSettings.repeater[k].repeaterName, doc["name"]); // "SK7RJL"
  const char* location = doc["location"]; // "55.720459,13.222694"
  strcpy(dmrSettings.repeater[k].repeaterLoc, doc["city"]); // "Lund"
  int x=0;
  for (JsonObject elem : doc["tg"].as<JsonArray>()) 
  {
    if (x < 10)
    {
      if (elem["tg_id"] != 0)
      {
        dmrSettings.repeater[k].groups[x].tg_id = elem["tg_id"];
        dmrSettings.repeater[k].groups[x].ts = elem["ts"];
        //    bool is_dynamic = elem["is_dynamic"];
      }
      else
      {
        dmrSettings.repeater[k].groups[x].tg_id = 0;
        dmrSettings.repeater[k].groups[x].ts = 0;
      }
    }
    x++;
  }
  sprintf(NXrepeaterName, "%s. %s", dmrSettings.repeater[k].repeaterName, dmrSettings.repeater[k].repeaterLoc);
  return true;
}
boolean EIMreadRepeaterDMRid(char* DMRid, int k)
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    char combinedArray[sizeof(EIMrepeaterUrl)  + 1536];
    sprintf(combinedArray, "%s%s", EIMrepeaterDMRUrl, DMRid); // with word space
    Serial.println("EIMreadRepeaterDMRid");
    Serial.println(combinedArray);
    http.begin(combinedArray);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        if (EIMdeserializeSingleRepeater(payload, k))
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
}
