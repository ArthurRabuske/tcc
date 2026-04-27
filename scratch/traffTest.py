from mininet.cli import CLI
from mininet.log import info
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.topo import SingleSwitchTopo

def start_tcp_server(net):
    # Get the second host in the network (assuming it has index 1)
    h2 = net.hosts[1]

    # Start the TCP server on port 5000 using netcat
    h2.cmd('nc -l 5000 &')

if __name__ == '__main__':
    # Create a network with a single switch and two hosts
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, host=CPULimitedHost)

    # Start the network
    net.start()

    # Start the TCP server on the second host
    start_tcp_server(net)

    # Wait for the TCP server to start
    info('Waiting for TCP server to start\n')
    net.pingAll()

    # Start the TCP client on the first host (assuming it has index 0)
    h1 = net.hosts[0]
    h1.cmd('sourcesonoff --transmitter-tcp -d {} --port 5000'.format(net.hosts[1].IP()))

    # Run the CLI to interact with the network
    CLI(net)

    # Stop the network when the CLI is exited
    net.stop()
