import subprocess
import re

def delete_hub_flows(switch_name):
    # Get the flows of the switch using ovs-ofctl command
    command = ['ovs-ofctl', 'dump-flows', switch_name]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Parse the flows and delete hub-like flows
    flows = result.stdout.split('\n')
    
    for flow in flows:
        if 'actions=' in flow:
            match_cookie = re.search(r'cookie=0x([0-9a-f]+)', flow)
            if match_cookie:
                cookie = match_cookie.group(1)
                
                if int(cookie, 16) != 65535:  # Skip flows with cookie 65535 (controller flows)
                    match_uuid = re.search(r'uuid=([0-9a-f\-]+)', flow)
                    print(match_uuid)
                    if match_uuid:
                        flow_uuid = match_uuid.group(1)
                        delete_command = ['ovs-vsctl', '--', 'remove', 'Flow_Table', flow_uuid]
                        print(delete_command)
                        subprocess.run(delete_command)

# Replace 'switch_name' with the actual name or identifier of your OpenFlow switch
switch_name = 's1'

# Call the function to delete hub-like flows based on their cookies
delete_hub_flows(switch_name)
