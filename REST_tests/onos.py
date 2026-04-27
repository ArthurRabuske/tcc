import requests

CONTROLLER_IP = '10.3.3.106'
REST_PORT = '8181'

url = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/topology'
url2 = f'http://{CONTROLLER_IP}:{REST_PORT}/onos/v1/hosts'
headers = {'Accept': 'application/json'}
response = requests.get(url, headers=headers,auth=('onos','rocks'))
response2 = requests.get(url2, headers=headers,auth=('onos','rocks'))
response_data = response.json()
host_Data = response2.json()
topology = response_data['devices']
links = response_data['links']
hosts = len(host_Data['hosts'])

print(f'Topo = {topology} | Links = {links} | Hosts = {hosts}')