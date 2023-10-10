from helpers import get_connection
from pysros.wrappers import *
import ipaddress

c = get_connection('clab-vr01-sros', 'admin', 'admin', 830)

# I have hard-coded the ip here, but you will be getting the ip from the ehs event notification - be sure to use your variable instead of the ip
my_filter = { 'operational-local-address' : {} }
raw_local_address = c.running.get('/nokia-state:state/router[router-name="Base"]/bgp/neighbor[ip-address="10.11.1.1"]/statistics', filter=my_filter)
# I am just getting only the ip without any yang wrappers
local_address = raw_local_address['operational-local-address'].data


# The paths are different for ipv4 and ipv6, so we need to find out which version we are looking at
ip_version = ipaddress.ip_address(local_address).version

if ip_version == 4:
    intf_filter={ 'ipv4' : { 'primary' : { 'address' : local_address }}}
    all_interfaces = c.running.get('/nokia-conf:configure/router[router-name="Base"]/interface', filter=intf_filter)
    find_interface('ipv4', all_interfaces)
else:
    intf_filter={ 'ipv6' : { 'address' : local_address }}
    all_interfaces = c.running.get('/nokia-conf:configure/router[router-name="Base"]/interface', filter=intf_filter)
    find_interface('ipv6', all_interfaces)

    
def find_interface(ip_version, all_interfaces):
    for k,v in all_interfaces.items():
        if ip_version in v.keys():
            print('Time to disable interface: %s' % k)
            disable_interface(k)
            
            
def disable_interface(interface_name):            
    path = '/nokia-conf:configure/router[router-name="Base"]/interface[interface-name="%s"]' % interface_name
    data = Container({'interface-name': Leaf('%s' % interface_name), 
                      'admin-state' : Leaf('disable'),
                      'description' : Leaf('Disabled by EHS due to BGP neighbor down')})
    c.candidate.set(path, data)
    print('Interface "%s" has been disabled' % interface_name)
