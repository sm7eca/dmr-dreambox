//----------------------------------------------------------- WiFi
void wifiGetDMRIDint();
WiFiMulti wifiMulti;
char radioIdUrl[] = "https://database.radioid.net/api/dmr/user/?id=";
char sweIdUrl[] = "https://fbg.johanneberg.com/services/radioid/?id=";
char dmrdreamUrl[] = "http://dmrdream.com/api/v1/user/";
long timezone = 1;
byte daysavetime = 1;

boolean  wifiConnect()
//----------------------------------------------------------- wifiConnect
//
{
  uint32_t Connecttimer = 10000; // max time to wait för WLAN connect
  uint32_t starttime;
  uint8_t y = 0;
  for (uint8_t x = 0; x < 4; x++)
  {
    if (&dmrSettings.wifisettings[x].ssid[0] != " ")
    {
      wifiMulti.addAP(dmrSettings.wifisettings[y].ssid, dmrSettings.wifisettings[x].passwd);
      y++;
    }
  }
  Serial.println("Connecting ...");
  uint8_t i = 0;
  starttime = millis();
  while (wifiMulti.run() != WL_CONNECTED and (millis() - starttime) < Connecttimer) { // Wait for the Wi-Fi to connect: scan for Wi-Fi networks, and connect to the strongest of the networks above
    delay(1000);
    Serial.print('.');
  }
  if (wifiMulti.run() == WL_CONNECTED)
  {
    Serial.println('\n');
    Serial.print("Connected to ");
    Serial.println(WiFi.SSID());              // Tell us what network we're connected to
    Serial.print("IP address:\t");
    Serial.println(WiFi.localIP());           // Send the IP address of the ESP8266 to the computer
    return true;
  }
  return false;
}
void WiFisetTime()
{
  if (BwifiOn)
  {
    configTime(3600 * timezone, daysavetime * 3600, "time.nist.gov", "0.pool.ntp.org", "1.pool.ntp.org");
    struct tm tmstruct ;
    delay(2000);
    tmstruct.tm_year = 0;
    getLocalTime(&tmstruct, 5000);
    Serial.printf("\nNow is : %d-%02d-%02d %02d:%02d:%02d\n", (tmstruct.tm_year) + 1900, ( tmstruct.tm_mon) + 1, tmstruct.tm_mday, tmstruct.tm_hour , tmstruct.tm_min, tmstruct.tm_sec);
    Serial.println("");
  }
}
void wifiGetDMRID()
//----------------------------------------------------------- wifiGetDMRID
{
  if (BwifiOn)
  {
    wifiGetDMRIDswe();
  }
}
void wifiGetDMRIDswe()
//----------------------------------------------------------- wifiGetDMRID
//  dmrdream.com EIM user
{

  if ((wifiMulti.run() == WL_CONNECTED))
  {
    HTTPClient http;
    WIFIcallfound = false;
    char combinedArray[sizeof(dmrdreamUrl) + sizeof(rxContactChar) + 1];
    sprintf(combinedArray, "%s%s", dmrdreamUrl, rxContactChar); // with word space
//    Serial.println(combinedArray);
    http.begin(combinedArray);
    // start connection and send HTTP header
    int httpCode = http.GET();
    // httpCode will be negative on error
    if (httpCode > 0)
    {
      if (httpCode == HTTP_CODE_OK)
      {
        WIFIcallfound = true;
        String payload = http.getString();
//        Serial.println("wifiGetDMRIDswe: ");
//        Serial.println(payload);
        StaticJsonDocument<300> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (error) {
          Serial.print(F("deserializeJson() failed: "));
          Serial.println(error.f_str());
          return;
        }

        long dmr_id = doc["dmr_id"]; // 2400530
        const char* call_sign = doc["call_sign"]; // "SM7ECA"
        const char* name = doc["name"]; // "Arne Nilsson"
        const char* city = doc["city"]; // "MalmÃ¶"
        const char* state = doc["state"]; // ""
        const char* country = doc["country"]; // "Sweden"
//        Serial.println(call_sign);

        ri_callsign = String(call_sign);
        ri_city = String(city);
        ri_country = String(country);
        ri_fname = String(name);
        ri_surname = "";
        ri_state = String(state);
        ri_id = dmr_id;
        if (ri_id == 0)
        {
          ri_id = rxContact;
        }
        insertradioid();
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
        Serial.print(" ");
        Serial.print("(SE-DD) ");
      }
    }
    else
    {
      Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
  }
  else {
    Serial.print("wifi not connected");
  }
}

////----------------------------------------------------------- wifiGetDMRID
//  the radioid app returns a json structure. Problem is that it is not consistent.
//  Some ids miss surname and state info
//  de deserialize function is not putting valid info in those fields if missing
//  in the json struct.
//{
//  if ((wifiMulti.run() == WL_CONNECTED))
//  {
//    HTTPClient http;
//    WIFIcallfound = false;
//    char combinedArray[sizeof(radioIdUrl) + sizeof(rxContactChar) + 1];
//    sprintf(combinedArray, "%s%s", radioIdUrl, rxContactChar); // with word space
//    Serial.println(combinedArray);
//    http.begin(combinedArray);
//    // start connection and send HTTP header
//    int httpCode = http.GET();
//    // httpCode will be negative on error
//    if (httpCode > 0)
//    {
//      // HTTP header has been send and Server response header has been handled
//      //           Serial.printf("[HTTP] GET... code: %d\n", httpCode);
//      // file found at server
//      if (httpCode == HTTP_CODE_OK)
//      {
//        WIFIcallfound = true;
//        String payload = http.getString();
//        Serial.println(payload);
//        size_t capacity = JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(2) + JSON_OBJECT_SIZE(8) + 200;
//        DynamicJsonDocument doc(capacity);
//        DeserializationError err = deserializeJson(doc, payload);
//        switch (err.code())
//        {
//          //  case DeserializationError::Ok:
//          //    Serial.print(F("Deserialization succeeded"));
//          //    break;
//          case DeserializationError::InvalidInput:
//            Serial.print(F("Invalid input!"));
//            break;
//          case DeserializationError::NoMemory:
//            Serial.print(F("Not enough memory"));
//            break;
//          default:
//            //                 Serial.print(F("Deserialization failed"));
//            break;
//        }
//        int count = doc["count"]; // 1
//        JsonObject results_0 = doc["results"][0];
//        String results_0_callsign = results_0["callsign"]; // "WA0CNG"
//        String results_0_city = results_0["city"]; // "Florissant"
//        String results_0_country = results_0["country"]; // "United States"
//        String results_0_fname = results_0["fname"]; // "Dan F"
//        long results_0_id = results_0["id"]; // 3165777
//        String results_0_remarks = results_0["remarks"]; // "DMR"
//        String results_0_state = results_0["state"]; // "Missouri"
//        String results_0_surname = results_0["surname"]; // "Zanitsch"
//
//        ri_callsign = results_0_callsign;
//        ri_city = results_0_city;
//        ri_country = results_0_country;
//        ri_fname = results_0_fname;
//        ri_surname = results_0_surname;
//        ri_state = results_0_state;
//        ri_id = results_0_id;
//        insertradioid();
//        Serial.print(ri_callsign);
//        Serial.print(" ");
//        Serial.print(ri_fname);
//        Serial.print(" ");
//        Serial.print(ri_surname);
//        Serial.print(" ");
//        Serial.print(ri_city);
//        Serial.print(" ");
//        Serial.print(ri_state);
//        Serial.print(" ");
//        Serial.print(ri_country);
//        Serial.print(" ");
//        Serial.print("(US-DB) ");
//      }
//    }
//    else
//    {
//      Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
//    }
//    http.end();
//  }
//  else {
//    Serial.print("wifi not connected");
//  }
//}
