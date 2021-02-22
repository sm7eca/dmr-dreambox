#!/bin/bash

set -e

mongo <<EOF
use admin

db.createUser({
  user: '$EIM_DB_USER',
  pwd:  '$EIM_DB_PASSWORD',
  roles: [{
    role: 'readWrite',
    db: '$EIM_DB_NAME'
  }]
})
EOF
