//------------------------------------------------------------------
//-------------------------------MAIN ---STATE --- WAIT LOOP -------
//------------------------------------------------------------------
void  do_idle()
//------------------------------------------------------------------ do_idle
//
// idle waiting for action
{
  // DMRDebug = false;
  if (btnPTT)                                         // PTT button pressed?
  {
    UnitState = TRANSMIT_STATE;
    DMRTransmit(FUNC_ENABLE, SET_TRANSMIT_INFORMATION);
    NX_P0_DisplayTransmit(true);
    Serial.println("PTT down");
    return;
  }
  if (ts_scan and ((millis() - tsSwitchLast) > tsSwitchInterval))
  {
    if (digData.InboundSlot == 0)
    {
      digData.InboundSlot = digData.OutboundSlot = 1;
    }
    else
    {
      digData.InboundSlot = digData.OutboundSlot = 0;
    }
 //   DMRupdateDigChannel();
    //    updateLine49();
 //   NX_P0_updateTXinfo();
    NX_P0_DisplayCurrentTS();
    tsSwitchLast = millis();
  }
}

void  do_transmit()
//------------------------------------------------------------ do_transmit
// PTT pressed - is transmitting state
//
{
  if (!btnPTT)                                  // PTT released
  {
    Serial.println("PTT-up");
    DMRTransmit(FUNC_DISABLE, SET_TRANSMIT_INFORMATION);
    NX_P0_DisplayTransmit(false);
    UnitState = IDLE_STATE;
  }
}

void do_RecDMR()
//------------------------------------------------------------ do_RecDMR
// update RSSI during a voice message
{

  if (millis() - RSSItimer > 5000)        // läs av signalstyrkan och vem som kallar efter 5 s
  {
    if (DMRcheckRSSI())
    {
      if (buff[8] == 0x00)                // We have lost connection = RSSI = 0, go back to idle
      {
        UnitState = IDLE_STATE;
      }

      NX_P0_updateRSSI(buff[8]);
    }
    RSSItimer = millis();
  }
}
