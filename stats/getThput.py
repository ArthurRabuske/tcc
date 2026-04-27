import matplotlib.pyplot as plt
from scapy.all import rdpcap, Ether, IP, TCP, UDP
from collections import Counter
import time

def protocol_stats(packets):
    protocols = []
    for packet in packets:
        if IP in packet:
            protocols.append(packet[IP].proto)
        elif Ether in packet:
            protocols.append(packet[Ether].type)
    # Count the occurrence of each protocol
    protocol_counts = {}
    for protocol in protocols:
        protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1

    # Generate a pie chart of the protocol distribution
    protocol_labels = ['TCP', 'ARP']
    protocol_sizes = [] 
    for label in protocol_labels:
        protocol_sizes.append(protocol_counts.get(label, 0))
    
    return protocol_sizes, protocol_labels
# Load the pcap file
packets = rdpcap("./h2.pcap")
print(packets)
# Extract the timestamp and packet size from each packet
timestamps = []
sizes = []
for packet in packets:
    timestamps.append(packet.time)
    sizes.append(len(packet))

# Subtract the timestamp of the first packet to shift the time axis
start_time = timestamps[0]
timestamps = [t - start_time for t in timestamps]

# Calculate the time elapsed between packets
times = [timestamps[i+1]-timestamps[i] for i in range(len(timestamps)-1)]

# Calculate the throughput in bytes per second
throughput = []
for i in range(len(times)):
    if times[i] == 0:
        throughput.append(0)
    else:
        throughput.append(sizes[i+1]/times[i])

# Convert the throughput to Mbits/s
throughput = [t/1000000*8 for t in throughput]

# Plot the throughput data
plt.plot(timestamps[1:], throughput)
plt.xlabel("Time")
plt.ylabel("Throughput (Mbit/s)")
#plt.show()
current_time = time.strftime("%H%M%S")
filename = "thput_" + current_time + ".png"
plt.savefig(filename)

# Calculate protocol distribution
# protocols = []

# protocols = Counter([packet[1].name for packet in packets])

# # Generate pie chart
# fig, ax = plt.subplots()
# ax.pie(protocols.values(), labels=protocols.keys(), autopct='%1.1f%%')
# ax.set_title('Protocol Distribution')
# plt.savefig('protocol_distribution.png')


# Plot the protocol statistics as a pie chart
# sizes, labels = protocol_stats(packets)
# plt.pie(sizes, labels=labels, autopct='%1.1f%%')
# plt.title('IP Distribution')
# plt.axis('equal')
# plt.savefig('ip_distribution.png')
