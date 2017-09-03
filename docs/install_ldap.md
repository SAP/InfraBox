# Configure LDAP with InfraBox

   kubectl -n  infrabox-system create secret generic \
        infrabox-ldap \
        --from-literal=password=<PASSWORD> \
        --from-literal=dn=<DN>
