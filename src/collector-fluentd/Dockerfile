FROM fluent/fluentd:v0.12.33

USER root
WORKDIR /home/fluent

ENV PATH /fluentd/vendor/bundle/ruby/2.3.0/bin:$PATH
ENV GEM_PATH /fluentd/vendor/bundle/ruby/2.3.0
ENV GEM_HOME /fluentd/vendor/bundle/ruby/2.3.0
ENV FLUENTD_DISABLE_BUNDLER_INJECTION 1

COPY src/collector-fluentd/Gemfile* /fluentd/
RUN set -ex \
    && apk upgrade --no-cache \
    && apk add --no-cache ruby-bundler \
    && apk add --no-cache --virtual .build-deps \
        build-base \
        ruby-dev \
        libffi-dev \
    && gem install bundler --version 1.16.1 \
    && bundle config silence_root_warning true \
    && bundle install --gemfile=/fluentd/Gemfile --path=/fluentd/vendor/bundle \
    && apk del .build-deps \
    && gem sources --clear-all \
    && rm -rf /tmp/* /var/tmp/* /usr/lib/ruby/gems/*/cache/*.gem

COPY src/collector-fluentd/conf/fluent.conf /fluentd/etc/
COPY src/collector-fluentd/plugins /fluentd/plugins/
COPY src/collector-fluentd/entrypoint.sh /fluentd/entrypoint.sh

ENV FLUENTD_OPT=""
ENV FLUENTD_CONF="fluent.conf"

# Run Fluentd
CMD ["/fluentd/entrypoint.sh"]
