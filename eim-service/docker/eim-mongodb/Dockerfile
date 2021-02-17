FROM mongo:3.6.22-xenial

RUN mkdir -p /home/mongodb
RUN chown -R mongodb:mongodb /home/mongodb

COPY init_db.sh /docker-entrypoint-initdb.d/
