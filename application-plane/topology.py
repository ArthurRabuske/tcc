import sys
import requests
import time
from scapy.all import *
from scapy.contrib.openflow import OFPTFeaturesRequest, OFPTFeaturesReply, OFPTPacketIn
sys.path.append('../')
from arguments_parser import parser


QUERY_INTERVAL = 1

def get_topology(controller,CONTROLLER_IP, REST_PORT):
    if controller == 'onos':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/topology'
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers,auth=('onos','rocks'))
        response_data = response.json()
        #print(response_data)
        # Extract the topology information from the response
        topology = response_data['devices']
        return topology
    elif controller == 'floodlight':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/wm/core/controller/switches/json'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                switches = response.json()
                return len(switches)
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
    elif controller == 'odl':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/restconf/operational/opendaylight-inventory:nodes'
        headers = {
            'Accept': 'application/json',
        }
        auth = ('admin', 'admin')
        try:
            response = requests.get(url,headers=headers,auth=auth)
            if response.status_code == 200:
                data = response.json()
                if 'node' in data['nodes']:
                    nodes = data['nodes']['node']
                    return len(nodes)
                else:
                    return 0
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")


def compare_topology(topology, len_topology):
    # Check if the topology matches the deployed topology
    if topology == len_topology:
        return True
    else:
        return False

def calculate_topology_discovery_time(start_time, end_time):
    topology_discovery_time = end_time - start_time
    return topology_discovery_time

# Record the time for the first LLDP packet received at the controller
start_time = None

def is_ofpt_features_reply(packet):
    global start_time
    while packet.payload:
        x = packet.payload
        #print(x.summary())
        if 'OFPTFeaturesReply' in x.summary():
            start_time = time.time()
            return True
        packet = x
    return False


def RFC8456_net_topology_discovery_time(len_topology,controller,ctrl_ip, rest_port):
    # Record the time for the first discovery message received at the controller
    print("Waiting for the first OFPTFeaturesReply message...")
    #print(f"ether dst {CONTROLLER_IP}")
    res = sniff(iface=f'{args.iface}',filter=f'tcp and dst port {args.controller_port}',stop_filter=is_ofpt_features_reply)
    #res.summary()

    # Query the controller every t=3 seconds to obtain the discovered network topology information
    consecutive_failures = 0
    while True:
        topology = get_topology(controller,ctrl_ip, rest_port)
        
        # Compare the discovered topology information with the deployed topology information
        topology_match = compare_topology(topology, len_topology)
        if topology_match:
            # Record the time for the last discovery message sent to the controller
            end_time = time.time()
            print(f'End time: {end_time}')
            break
        else:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                with open('output/topo_disc_'+controller+'.txt', 'a') as f:
                    f.write("-1.0\n") #flag for script stop
                break

        time.sleep(QUERY_INTERVAL)

    # Calculate the topology discovery time
    if topology_match:
        topology_discovery_time = calculate_topology_discovery_time(start_time, end_time)
        with open('output/topo_disc_'+controller+'.txt', 'a') as f:
            f.write(f"{topology_discovery_time}\n")

if __name__ == '__main__':

    # Parse the command line arguments
    args = parser('topology')

    # Check if the file exists
    if not os.path.isfile('topo_disc_'+args.controller_name+'.txt'):
        # Create the file
        with open('output/topo_disc_'+args.controller_name+'.txt', 'w') as f:
            pass

    RFC8456_net_topology_discovery_time(args.target_length,
                                        args.controller_name,
                                        args.controller_ip,
                                        args.rest_port)