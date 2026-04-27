import requests

CONTROLLER_IP = '10.3.3.106'
REST_PORT = '8181'

url = f'http://{CONTROLLER_IP}:{REST_PORT}/restconf/operational/opendaylight-inventory:nodes'
headers = {
    'Accept': 'application/json',
}
auth = ('admin', 'admin')
try:
    response = requests.get(url,headers=headers,auth=auth)
    if response.status_code == 200:
        data = response.json()
        if 'node' in data['nodes']:
            nodes = data['nodes']['node']
            links = sum(len(node.get('node-connector', [])) for node in nodes)
            host_count = sum(1 for node in nodes if node.get('node-connector', []) and node.get('node-type') == 'OF')
            print(f'Switches = {len(nodes)} | Links = {(links-len(nodes))} | Hosts = {host_count}')#odl adds one local link for each sw
        else:
            print('nothing')
    else:
        print(f"Error: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")