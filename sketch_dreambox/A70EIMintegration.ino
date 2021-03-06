
char  EIMrepeaterUrl[] = "http://api.dmrdream.com/repeater/";
char  EIMrepeaterDMRUrl[] = "http://api.dmrdream.com/repeater/dmr/";
char  EIMhotspotUrl[] = "http://api.dmrdream.com/hotspot/callsign/";
char  EIMstatusUrl[] = "http://api.dmrdream.com/system/info";

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
        StaticJsonDocument<192> doc;
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
  int ts = doc["ts"];                     // 1
  int max_ts = doc["max_ts"];             // 1
  const char *name = doc["name"];         // "SQ7JSK"
  const char *location = doc["location"]; // "Falkenberg"
  int tg_0_tg_id = doc["tg"][0]["tg_id"]; // 24006
  int tg_0_ts = doc["tg"][0]["ts"];       // 1
  Serial.println(dmr_id);
  Serial.println(tx);
  Serial.println(rx);
  Serial.println(cc);
  Serial.println(ts);
  Serial.println(max_ts);
  Serial.println(name);
  Serial.println(location);
  Serial.println(tg_0_tg_id);
  Serial.println(tg_0_ts);
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

  dmrSettings.repeater[k+4].dmrId = doc["dmr_id"]; // 240701
  dmrSettings.repeater[k+4].tx = doc["tx"]; // 434587500
  dmrSettings.repeater[k+4].rx = doc["rx"]; // 432587500
  dmrSettings.repeater[k+4].cc = doc["cc"]; // 7
  dmrSettings.repeater[k+4].timeSlot = doc["ts"]; // 1
  dmrSettings.repeater[k+4].timeSlotNo =  2;
//  int max_ts = doc["max_ts"]; // 0
  strcat(dmrSettings.repeater[k+4].repeaterName,doc["name"]); // "SK7RJL"
  const char* location = doc["location"]; // "55.720459,13.222694"
  strcat(dmrSettings.repeater[k+4].repeaterLoc,doc["city"]); // "Lund"
//  long dmr_id = doc["dmr_id"]; // 240701
//  long tx = doc["tx"]; // 434587500
//  long rx = doc["rx"]; // 432587500
//  int cc = doc["cc"]; // 7
//  int ts = doc["ts"]; // 1
//  int max_ts = doc["max_ts"]; // 0
//  const char* name = doc["name"]; // "SK7RJL"
//  const char* location = doc["location"]; // "55.720459,13.222694"
//  const char* city = doc["city"]; // "Lund"

  for (JsonObject elem : doc["tg"].as<JsonArray>()) {

    if (elem<10)
    {
      dmrSettings.repeater[k+4].groups[elem].tg_id = elem["tg_id"];
//    int master_id = elem["master_id"];
//    long rep_id = elem["rep_id"];
      dmrSettings.repeater[k+4].groups[elem].ts = elem["ts"];
//    bool is_dynamic = elem["is_dynamic"];
//    int tg_id = elem["tg_id"]; // 240, 240, 2400, 2401, 2402, 2403, 2404, 2405, 2406, 2407, 2407
//    int master_id = elem["master_id"]; // 2401, 2401, 2401, 2401, 2401, 2401, 2401, 2401, 2401, 2401, 2401
//    long rep_id = elem["rep_id"]; // 240701, 240701, 240701, 240701, 240701, 240701, 240701, 240701, 240701, ...
//    int ts = elem["ts"]; // 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2
//    bool is_dynamic = elem["is_dynamic"]; // false, false, false, false, false, false, false, false, false, ...
    Serial.println(dmrSettings.repeater[k+4].groups[elem].tg_id);
    Serial.println(dmrSettings.repeater[k+4].groups[elem].ts);
    }
  }
  Serial.println(dmrSettings.repeater[k+4].repeaterName);
  Serial.println(dmrSettings.repeater[k+4].repeaterLoc);
  sprintf(NXrepeaterName, "%s %s",dmrSettings.repeater[k+4].repeaterName,dmrSettings.repeater[k+4].repeaterLoc);
  Serial.println(NXrepeaterName);
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
        if (EIMdeserializeSingleRepeater(payload,k))
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
