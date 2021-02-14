
# Introduction

EIM - External Information Management

# Data Sources

## Google Maps

- Used to translate a city into LONG, LAT

## RadioId.net

- map DMR ID to name, surname, location, callsign

## Brandmeister

- https://wiki.brandmeister.network/index.php/API/Halligan_API
- fetch all repeater
- fetch all talk groups

### Repeater-Status

- 4: hotspot
- 3: repeater
- 2: ??
- 1: ??


# Endpoints

/repeater?loclat=76887687?loclong=7687687687?range=

source: own DB

[
	{
		dmr_id: 45345345345,
		tx: 432600000,
		rx: 434600000,
		cc: 4,		//  [0:15]
		ts: 1,		//  [1,2]
		max_ts: 1,	//	[1,2]
		name: SK6JX //  callsign, string, limit to 14 chars
		location: 	//  string, limit to 14 chars
		tg: [
			{
				tg: 24060,
				ts: 1 		[1,2]
			}
		]
	}

]

/repeater?master=2401

filter status=3
filter lastKnownMaster=master

/repeater?city=falkenberg?country=se?range=30km

filter status=3
filter range=30km


/hotspots?callsign=SM7ECA

filter status=4
filter callsign

output: same as /repeater

/tg
