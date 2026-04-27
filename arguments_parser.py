import argparse

def parser(program):
    if program == 'topology-script':
        parser = argparse.ArgumentParser(description='RFC8456 SDN Benchmarking - Topology Discovery - Script.')
        
        parser.add_argument('-ip','--controller_ip', help='Controller IP address', default='localhost')
        parser.add_argument('-p','--controller_port', help='Controller port number',default=6653)
        parser.add_argument('-n','--controller_name', help='Controller name')
        parser.add_argument('-r','--rest_port', help='REST API port number',default=8181)
        #parser.add_argument('target_length', help='Target Topology Length',type=int)
        parser.add_argument('-if','--iface', help='Interface to listen',default='eth0')
        parser.add_argument('-t','--topology', choices=['3-tier', 'star', 'mesh', 'leaf-spine'], help='Topology type')
        parser.add_argument('--num-cores', type=int, help='Number of core switches (for 3-tier topology)')
        parser.add_argument('--num-aggs', type=int, help='Number of aggregation switches (for 3-tier topology)')
        parser.add_argument('--num-access', type=int, help='Number of access switches (for 3-tier topology)')
        parser.add_argument('--num-switches', type=int, help='Number of switches (for star/mesh topology)')
        parser.add_argument('--hub-switch', type=int, help='Hub switch index (for star topology)')
        parser.add_argument('--num-leafs', type=int, help='Number of leaf switches (for leaf-spine topology)')
        parser.add_argument('--num-spines', type=int, help='Number of spine switches (for leaf-spine topology)')
        parser.add_argument('-q','--query-interval', help='Interval between next topology size query',type=int)
        parser.add_argument('-c','--consec-failures', help='How many consecutive failures before stop querying',type=int)
        parser.add_argument('-cl','--consec_link_failures', help='How many consecutive link failures before stop querying',type=int,default=50)
        parser.add_argument('-s','--start', help='Initial value for i (initial topology size)',type=int)
        parser.add_argument('-tr','--trials', help='Number of trials',type=int,default=10)
        parser.add_argument('-d','--diff', help='Commom difference between each topology size of the next experiment ',type=int,default=5)
        parser.add_argument('-max','--maxsize', help='Max topology size',type=int,default=1000)
        parser.add_argument('-k', '--no_links', action=argparse.BooleanOptionalAction, default=False,help='Enable or disable link discovery time count')
        args = parser.parse_args()
        return args
    elif program == 'workload':
        parser = argparse.ArgumentParser(description='Workload Generator for SDN-BM experiments')
        parser.add_argument('-ip','--controller_ip', help='Controller IP address', default='localhost')
        parser.add_argument('-n','--controller_name', help='Controller name')
        parser.add_argument('-p','--controller_port', help='Controller port number',default=6653,type=int)
        parser.add_argument('-r','--rest_port', help='REST API port number',default=8181)
        parser.add_argument('-t','--topology', choices=['3-tier', 'star', 'mesh', 'leaf-spine'], help='Topology type')
        parser.add_argument('--num-cores', type=int, help='Number of core switches (for 3-tier topology)')
        parser.add_argument('--num-aggs', type=int, help='Number of aggregation switches (for 3-tier topology)')
        parser.add_argument('--num-access', type=int, help='Number of access switches (for 3-tier topology)')
        parser.add_argument('--num-switches', type=int, help='Number of switches (for star/mesh topology)')
        parser.add_argument('--hub-switch', type=int, help='Hub switch index (for star topology)')
        parser.add_argument('--num-leafs', type=int, help='Number of leaf switches (for leaf-spine topology)')
        parser.add_argument('--num-spines', type=int, help='Number of spine switches (for leaf-spine topology)')
        parser.add_argument('-l', '--links', action=argparse.BooleanOptionalAction, default=False,help='Enable or disable link discovery time count')
        parser.add_argument('--hosts', action=argparse.BooleanOptionalAction, default=False,help='Enable or disable host discovery time count')
        parser.add_argument('--hosts_to_add', type=int, default=0, help='Number of hosts to be added after start')
        parser.add_argument('--links_to_add', type=int, help='Number of links to be added after start')
        args = parser.parse_args()

        topology_type = args.topology
        if topology_type == '3-tier':
            num_cores = args.num_cores
            num_aggs = args.num_aggs
            num_access = args.num_access
            return [topology_type, [num_cores, num_aggs, num_access],[args.controller_ip,args.controller_port]], args
        elif topology_type == 'star':
            num_switches = args.num_switches
            hub_switch = args.hub_switch
            return [topology_type, [num_switches, hub_switch],[args.controller_ip,args.controller_port]], args
        elif topology_type == 'mesh':
            num_switches = args.num_switches
            return [topology_type, [num_switches],[args.controller_ip,args.controller_port]], args
        elif topology_type == 'leaf-spine':
            num_leafs = args.num_leafs
            num_spines = args.num_spines
            return [topology_type, [num_leafs, num_spines],[args.controller_ip,args.controller_port]], args
    elif program == 'topology':
        parser = argparse.ArgumentParser(description='RFC8456 SDN Benchmarking - Topology Discovery.')
        
        parser.add_argument('-ip','--controller_ip', help='Controller IP address', default='localhost')
        parser.add_argument('-p','--controller_port', help='Controller port number',default=6653)
        parser.add_argument('-n','--controller_name', help='Controller name')
        parser.add_argument('-r','--rest_port', help='REST API port number',default=8181)
        parser.add_argument('-l','--target_length', help='Target Topology Length',type=int)
        parser.add_argument('-q','--query_interval', help='Interval between next topology size query',type=int)
        parser.add_argument('-c','--consec_failures', help='How many consecutive failures before stop querying',type=int)
        parser.add_argument('-cl','--consec_link_failures', help='How many consecutive link failures before stop querying',type=int,default=50)
        parser.add_argument('-if','--iface', help='Interface to listen',default='lo')
        parser.add_argument('-k', '--no_links', action=argparse.BooleanOptionalAction, default=False,help='Enable or disable link discovery time count')
        return parser.parse_args()
    elif program == 'northbound_api':
        parser = argparse.ArgumentParser(description='Throughput and Average Time for SDN Controller respond to API Topo Requests')
        parser.add_argument('-rt', '--request_time', action=argparse.BooleanOptionalAction, default=False,help='Enable Request Time Measurement')
        parser.add_argument('-ip','--controller_ip', help='Controller IP address', default='localhost')
        parser.add_argument('-p','--controller_port', help='Controller port number',default=6653)
        parser.add_argument('-n','--controller_name', help='Controller name')
        parser.add_argument('-r','--rest_port', help='REST API port number',default=8181)
        parser.add_argument('-s','--topo_size', help='Topology Size',type=int)
        parser.add_argument('-q','--query_interval', help='Interval between next topology size query',type=int)
        parser.add_argument('-nt','--num_tests', help='Number of tests',type=int)
        parser.add_argument('-t','--topology', choices=['3-tier', 'star', 'mesh', 'leaf-spine'], help='Topology type')
        parser.add_argument('-tp', '--throughput', action=argparse.BooleanOptionalAction, default=False,help='Enable Thput Measurement')
        parser.add_argument('-mr','--max_requests', help='Max number of requests',type=int)
        parser.add_argument('-d','--duration', help='Duration of the test',type=int)
        parser.add_argument('-i','--step', help='Increment step',type=int)
        return parser.parse_args()
