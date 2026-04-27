import requests
import threading
import time
from arguments_parser import parser

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
        url = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/topology/devices'
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

def evaluate_max_throughput(controller, CONTROLLER_IP, REST_PORT, max_requests, duration):
    step = 10  # Number of concurrent requests increment per step
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
    args = parser('throughput')

    max_requests = args.max_requests
    duration = args.duration

    max_throughput = evaluate_max_throughput(args.controller_name, args.controller_ip, args.rest_port, max_requests, duration)

    print(f"Max Throughput: {max_throughput} requests per second")