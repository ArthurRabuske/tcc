from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo
from functools import partial


def create_topology(net, topology):
    """
    Create network topology.

    :param net: Mininet object
    :param topology: list of lists specifying network topology
    :return: list of Host objects
    """
    hosts = []

    # Create switches
    switches = [net.addSwitch('s{}'.format(i), protocols='OpenFlow13') for i in range(len(topology))]

    # Create hosts
    for i in range(len(topology)):
        host = net.addHost('h{}'.format(i+1))
        hosts.append(host)

        # Connect host to switch
        net.addLink(host, switches[i])

        # Connect switch to other switches
        for j in topology[i]:
            net.addLink(switches[i], switches[j-1], intfName1='s{}-eth{}'.format(i, j), intfName2='s{}-eth{}'.format(j-1, i+1))

    return hosts

def generate_topology(num_switches, topology_type, topology_parameters):
    if topology_type == 'star':
        hub_switch = topology_parameters[0]
        connections = [[] for _ in range(num_switches)]
        for i in range(1, num_switches+1):
            if i != hub_switch:
                connections[i-1].append(hub_switch)
                #connections[hub_switch-1].append(i) #if bidirectional links
        
        return connections

#"old" version
def get_topology(num_switches, topology_type):
    """
    Returns a list of lists specifying the network topology based on the given parameters.

    :param num_switches: number of switches in the network
    :param topology_type: type of network topology to create
    :return: list of lists specifying network topology
    """
    if topology_type == 'star topology':
        return [[i] for i in range(1, num_switches+1)]
    elif topology_type == 'mesh topology':
        return [[j+1 for j in range(num_switches)] for i in range(num_switches)]
    elif topology_type == 'leaf-spine topology':
        num_leaves = num_switches // 2
        num_spines = num_switches - num_leaves
        topology = []
        for i in range(num_leaves):
            leaves = [i*num_spines + j + num_leaves for j in range(num_spines)]
            for j in range(num_spines):
                topology.append([i*num_spines + j + 1] + leaves[:j] + leaves[j+1:])
        for i in range(num_spines):
            spines = [j*num_spines + i + num_leaves + 1 for j in range(num_leaves)]
            for j in range(num_leaves):
                topology.append([j*num_spines + i + num_leaves + 1] + spines)

        return topology


if __name__ == '__main__':
    setLogLevel('info')

    # Default parameters
    num_switches = 4
    topology_type = 'star'

    # Create Mininet object
    net = Mininet(controller=partial(RemoteController, ip='172.17.0.2', port=6633), autoSetMacs=True)

    # Create network topology
    topology = generate_topology(num_switches, topology_type,[3])

    # Add switches and hosts to network
    hosts = create_topology(net, topology)

    # Start network
    net.start()

    # Start CLI
    CLI(net)

    # Stop network
    net.stop()
