
FROM nginx:stable-alpine

RUN rm -f /etc/nginx/conf.d/default.conf
COPY conf/api_gateway.conf /etc/nginx/conf.d/eim_api.conf
