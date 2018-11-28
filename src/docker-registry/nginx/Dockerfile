FROM nginx:1.15-alpine
RUN apk add --no-cache curl python py-pip openssl && \
    pip install htpasswd && \
    apk del py-pip

COPY src/docker-registry/nginx/nginx.conf /etc/nginx/nginx.conf
COPY src/docker-registry/nginx/entrypoint.sh /entrypoint.sh
COPY src/docker-registry/nginx/get_admin_pw.py /get_admin_pw.py
COPY src/utils/wait-for-webserver.sh /wait-for-webserver.sh

RUN mkdir -p /etc/nginx/html/v1/users
RUN touch /etc/nginx/html/v1/users/index.html

RUN mkdir /home/nginx
RUN chown nginx /home/nginx

RUN touch /var/run/nginx.pid
RUN chown nginx /var/run/nginx.pid

CMD ["/entrypoint.sh"]
