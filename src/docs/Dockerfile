FROM nginx

COPY src/docs/static/index.html /etc/nginx/html/index.html
COPY src/docs/static/assets /etc/nginx/html/assets

COPY src/docs/nginx_no_ssl.conf /etc/nginx/nginx_no_ssl.conf
COPY src/docs/nginx_ssl.conf /etc/nginx/nginx_ssl.conf
COPY src/docs/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
