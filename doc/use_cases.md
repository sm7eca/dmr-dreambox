
# Terms

- DDB - Dmr Database


# Init State

User has received a new unit or managed to build the
kit and powers up the unit for the first time.

- no Wifi settings
- no connection to Internet nor DDB

## Setup Wifi

- User is entering Wifi related settings through Nextion
- test before safing to EEPROM


## Setup Own Call Sign

### Prerequisites
- internet connection
- user needs a valid callsign and DMR ID registered with that callsign

### Actions
- through Nextion
- idea: if internet connection exists, try to search Radioid.net, no match => no idea to continue
- Safe to EEPROM
- (optional) with callsign we could indentify hotspots via Brandmeister, fetch all Hotspot definitions that are owned by users callsign.


## Repeater Setup

### Prerequisites
- internet connection


### Actions
- enter the country, or first 3 digits