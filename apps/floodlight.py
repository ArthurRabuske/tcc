import requests
import time
from scapy.all import *


QUERY_INTERVAL = 3
controller_ip = 'localhost'

def get_topology():
    url = f'http://{controller_ip}:8081/wm/core/controller/switches/json'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            switches = response.json()
            return len(switches)
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

start_time = None

def is_ofpt_features_reply(packet):
    global start_time
    while packet.payload:
        x = packet.payload
        print(x.summary())
        if 'OFPTFeaturesReply' in x.summary():
            start_time = time.time()
            return True
        packet = x
    return False

def calculate_topology_discovery_time(start_time, end_time):
    topology_discovery_time = end_time - start_time
    return topology_discovery_time

def RFC8456_net_topology_discovery_time(len_topology):
    # Record the time for the first discovery message received at the controller
    print("Waiting for the first LLDP packet...")
    #print(f"ether dst {CONTROLLER_IP}")
    res = sniff(iface='lo',filter='tcp and dst port 6653',stop_filter=is_ofpt_features_reply)
    #res.summary()

    # Query the controller every t=3 seconds to obtain the discovered network topology information
    consecutive_failures = 0
    while True:
        topology = get_topology()

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
                print('Topology discovery failed')
                break

        time.sleep(QUERY_INTERVAL)

    # Calculate the topology discovery time
    if topology_match:
        topology_discovery_time = calculate_topology_discovery_time(start_time, end_time)
        print(f'Topology discovery time: {topology_discovery_time} seconds')

if __name__ == '__main__':
    RFC8456_net_topology_discovery_time(9)