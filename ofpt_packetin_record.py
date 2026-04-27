from scapy.all import *
from scapy.contrib.openflow import OFPTFeaturesRequest, OFPTFeaturesReply, OFPTPacketIn
from arguments_parser import parser




def last_ofpt_packet_in(packet):
    last_time_pkt_in = 0
    if 'OFPTPacketIn' in packet.summary():
        #print(packet.summary())
        last_time_pkt_in = time.time()
        with open('output/last_ofpt_packet_in_'+args.controller_name+'.txt', 'a') as f:
            f.write(f"{last_time_pkt_in}\n")
    



if __name__ == '__main__':
    args = parser('packet_in')
    with open('output/last_ofpt_packet_in_' + args.controller_name + '.txt', 'w') as f:
        pass  # Create the file (write mode, overwrites any existing content)
    
    res = sniff(iface=f'{args.iface}',filter=f'tcp and dst port {args.controller_port}',prn=last_ofpt_packet_in)