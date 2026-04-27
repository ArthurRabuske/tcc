###############################################################
#    Script to evaluate avg and max thput on northbound api   #
###############################################################


import requests, subprocess, threading
from arguments_parser import parser
import time

def get_target(topo, size, type='sep'):
    if topo == 'mesh':
        return size
    elif topo == 'leaf-spine':
        if type == 'sep':
            return size, size*2
        else:
            return (size + size*2)
    elif topo == '3-tier':
        if type == 'sep':
            return size, size, size
        else:
            return (size + size + size)

def run_workload_simulation(controller_ip, controller_port,topology_type, topology_parameters):
    if topology_type == 'leaf-spine':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', controller_port,'-t',topology_type, '--num-leafs', f'{topology_parameters[0]}', '--num-spines', f'{topology_parameters[1]}','--hosts_to_add', '1']
        print(cmd)
    elif topology_type == 'mesh':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', controller_port,'-t',topology_type, '--num-switches', f'{topology_parameters}','--hosts_to_add', '1']
        print(cmd)
    elif topology_type == '3-tier':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', controller_port,'-t',topology_type, '--num-cores', f'{topology_parameters[0]}', '--num-aggs', f'{topology_parameters[1]}', '--num-access', f'{topology_parameters[2]}','--hosts_to_add', '1']
        print(cmd)
    return subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def get_response_time(controller, CONTROLLER_IP, REST_PORT):
    if controller == 'onos':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/topology'
        headers = {'Accept': 'application/json'}
        start_time = time.time()
        response = requests.get(url, headers=headers, auth=('onos', 'rocks'))
        end_time = time.time()
        response_data = response.json()
        #print(response_data)
        # Extract the topology information from the response
        topology = response_data['devices']
        #links = response_data['links']
        if topology > 0:
            response_time = end_time - start_time
        else:
            return 0
        return response_time
    elif controller == 'floodlight':
        url1 = f'http://{CONTROLLER_IP}:{REST_PORT}/wm/core/controller/switches/json'
        #url2 = f'http://{CONTROLLER_IP}:{REST_PORT}/wm/topology/links/json'
        try:
            start_time = time.time()
            response1 = requests.get(url1)
            #response2 = requests.get(url2)
            end_time = time.time()
            if response1.status_code == 200:
                
                if len(response1.json()) > 0:
                    response_time = end_time - start_time
                    return response_time
                else:
                    return 0
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
            start_time = time.time()
            response = requests.get(url, headers=headers, auth=auth)
            end_time = time.time()
            if response.status_code == 200:
                data = response.json()
                if 'node' in data['nodes']:
                    response_time = end_time - start_time
                    return response_time
                else:
                    return 0
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

def send_request(url, headers, auth, result_list):
    try:
        response = requests.get(url, headers=headers, auth=auth)
        if response.status_code == 200:
            result_list.append(1)
    except requests.exceptions.RequestException:
        pass

def measure_throughput(controller, CONTROLLER_IP, REST_PORT, num_requests, duration):
    headers = {'Accept': 'application/json'}
    url = ''
    auth = ()
    if controller == 'onos':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/topology'
        auth = ('onos','rocks')
    elif controller == 'floodlight':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/wm/core/controller/switches/json'
        #auth = ('admin','admin')
    elif controller == 'odl':
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/restconf/operational/opendaylight-inventory:nodes'
        auth = ('admin','admin')

    successful_requests = 0
    result_list = []

    start_time = time.time()

    while time.time() - start_time < duration:
        threads = []
        for _ in range(num_requests):
            t = threading.Thread(target=send_request, args=(url, headers, auth, result_list))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

    successful_requests = len(result_list)

    throughput = successful_requests / duration

    return throughput

def evaluate_max_throughput(controller, CONTROLLER_IP, REST_PORT, max_requests, duration, increment):
    step = increment  # Number of concurrent requests increment per step
    current_requests = step
    max_throughput = 0.0

    while current_requests <= max_requests:
        throughput = measure_throughput(controller, CONTROLLER_IP, REST_PORT, current_requests, duration)
        print(f"Concurrent Requests: {current_requests} | Throughput: {throughput} requests per second")

        if throughput > max_throughput:
            max_throughput = throughput

        current_requests += step

    return max_throughput


if __name__ == '__main__':

    # Parse the command line arguments
    args = parser('northbound_api')

    

    num_tests = args.num_tests
    total_response_time = 0.0

    print('running workload.py')
    run_simulation_proc = run_workload_simulation(args.controller_ip,args.controller_port,args.topology, get_target(args.topology,args.topo_size,'sep'))
    
    if args.request_time:
        succ_test = 0
        while succ_test < (num_tests):
            response_time = get_response_time(args.controller_name, args.controller_ip, args.rest_port)
            if response_time > 0:
                print(response_time)
                succ_test += 1
            time.sleep(args.query_interval)
            total_response_time += response_time
        average_response_time = total_response_time / num_tests
        print(f"Average Response Time: {average_response_time}")
            
    if args.throughput:
        max_throughput = evaluate_max_throughput(args.controller_name, args.controller_ip, args.rest_port, args.max_requests, args.duration, args.step)
        print(f"Max Throughput: {max_throughput} requests per second")
    
    run_simulation_proc.stdin.flush()
    run_simulation_proc.communicate()


    
    run_simulation_proc.wait()
    print('finished workload.py')

    

    