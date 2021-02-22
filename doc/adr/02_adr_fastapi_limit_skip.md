
# Issue

- The small embedded processor wont be able to receive all active repeater
  for a given DMR master. Thus we need a solution where the ESP32 unit is
  able to loop through the number of repeaters available.
- Findings:
	- status == 3 => repeater
	- status == 4 => hotspot
	- last_updated < 1 day, seems to be an active repeater

# Decision

- Provide _limit_ and _skip_ parameter in the API call.
- Default values:
   - limit: 10
   - skip: 0

# Consequences

- there might be the risk that while the ESP unit is looping through
  the list, the DB has been updated by the harvester with new active repeater.
