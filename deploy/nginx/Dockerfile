FROM nginx:1.27-alpine
RUN apk add --no-cache gettext \
    && rm -f /etc/nginx/conf.d/default.conf
COPY ./deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./deploy/nginx/ssl-entrypoint.sh /ssl-entrypoint.sh
RUN chmod +x /ssl-entrypoint.sh
