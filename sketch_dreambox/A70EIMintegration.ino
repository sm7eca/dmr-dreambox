
char  EIMrepeaterUrl[] = "http://api.dmrdream.com/repeater/master?master=2401";
char  EIMhotspotUrl[] = "http://api.dmrdream.com/hotspot?callsign=";
char  EIMstatusUrl[] = "http://api.dmrdream.com/info";

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

void EIMreadRepeaters()
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    http.begin(EIMrepeaterUrl);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        StaticJsonDocument<384> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (error) {
          Serial.print(F("deserializeJson() failed: "));
          Serial.println(error.f_str());
          return;
        }
        long dmr_id = doc["dmr_id"]; // 24060811
        long tx = doc["tx"]; // 436600000
        long rx = doc["rx"]; // 432600000
        int cc = doc["cc"]; // 4
        int ts = doc["ts"]; // 1
        int max_ts = doc["max_ts"]; // 1
        const char* name = doc["name"]; // "SQ7JSK"
        const char* location = doc["location"]; // "Falkenberg"
        int tg_0_tg_id = doc["tg"][0]["tg_id"]; // 24006
        int tg_0_ts = doc["tg"][0]["ts"]; // 1
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
    }
  }

}

void EIMreadHotspots()
{
  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    http.begin(EIMhotspotUrl);
    int httpCode = http.GET();
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
        Serial.println(payload);
        StaticJsonDocument<384> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (error) {
          Serial.print(F("deserializeJson() failed: "));
          Serial.println(error.f_str());
          return;
        }
        long dmr_id = doc["dmr_id"]; // 24060811
        long tx = doc["tx"]; // 436600000
        long rx = doc["rx"]; // 432600000
        int cc = doc["cc"]; // 4
        int ts = doc["ts"]; // 1
        int max_ts = doc["max_ts"]; // 1
        const char* name = doc["name"]; // "SQ7JSK"
        const char* location = doc["location"]; // "Falkenberg"
        int tg_0_tg_id = doc["tg"][0]["tg_id"]; // 24006
        int tg_0_ts = doc["tg"][0]["ts"]; // 1
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
    }
  }

}
