FROM grafana/grafana:latest

USER grafana

ARG GF_INSTALL_PLUGINS=""

##Setting up the DB
#We paste our own DB configuration
COPY src/grafana/datasources/datasources.yaml etc/grafana/provisioning/datasources/

### Pre installing our dashboards
#We copy our sample.yaml to tell where to search for our dashboards
COPY src/grafana/dashboards/dashboards.yaml /etc/grafana/provisioning/dashboards/
#We copy our dashboards in the repertory we tell to search for
COPY src/grafana/dashboards/*.json /var/lib/grafana/dashboards/



RUN if [ ! -z "${GF_INSTALL_PLUGINS}" ]; then \
    OLDIFS=$IFS; \
        IFS=','; \
    for plugin in ${GF_INSTALL_PLUGINS}; do \
        IFS=$OLDIFS; \
        grafana-cli --pluginsDir "$GF_PATHS_PLUGINS" plugins install ${plugin}; \
    done; \
fi


