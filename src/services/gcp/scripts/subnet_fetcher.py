import ipaddress
import random
network="192.168.0.0/16"
blocks = list(ipaddress.IPv4Network(network).subnets(new_prefix=28))
print(str(random.choice(blocks)))