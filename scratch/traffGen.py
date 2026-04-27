#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import RemoteController
import time


def list_and_capture(host, filename):
    host.cmd('nc -lk 5000 &')
    host.cmd('tcpdump -w {} &'.format(filename))
    time.sleep(1)
def stop_server(host):
    host.cmd('kill %nc')
    host.cmd('kill %tcpdump')

def stop_process(host, process_name):
    process = host.popen('pgrep {}'.format(process_name))
    pid = process.stdout.read().decode('utf-8').strip()
    process.terminate()
    process.wait()
    host.cmd('kill -9 {}'.format(pid))

def run_sourcesonoff():
    h1, h2= net.get('h1', 'h2')

    # configure h1 as the transmitter and h2 as the receiver
    tx_host, rx_host = h1.IP(), h2.IP()

    
    cmd = 'sourcesonoff -v -t -d {} --port-number 5000 --doff-type=weibull --don-min=10 --don-max=1000 --doff-min=1s --doff-max=2s --turn 3 > log_trf.txt'.format(rx_host)

    # start the sourcesonoff traffic generator command on the transmitter host
    h1.cmd(cmd)


if __name__ == '__main__':
    net = Mininet(topo=None, controller=RemoteController)

    # create two hosts
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')

    net.addLink(h1, h2)

    # start the network
    net.start()
    

    current_time = time.strftime("%H%M%S")
    filename = "capture_" + current_time + ".pcap"
    list_and_capture(h2,filename)
    run_sourcesonoff()
    stop_process(h2,'tcpdump')
    stop_process(h2,'nc')
    net.stop()
