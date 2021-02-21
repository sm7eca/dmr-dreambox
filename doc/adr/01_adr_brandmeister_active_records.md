
# Issue

- The Brandmeister API contains huge number of repeater and hotspots
  that haven't been updated for quite some time.

# Solution

- We've decided to keep all entries in the database.
- We've decided to return only those items that have been a timestamp
  of less than 24 hours ago. This can be achieved in the API code.

# Consequences

- A little bit of overhead in the API code but this will be easy to fix.
