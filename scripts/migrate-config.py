#!/usr/bin/python3
import base64
import json
import sys
import xml.etree.ElementTree as ET


def search_and_replace(filedata):
    # Replaces proxy.pac network strings for all files seen in filer
    old_base64_bytes = filedata.encode('utf-8')
    old_message_bytes = base64.b64decode(old_base64_bytes)
    decoded_filedata = old_message_bytes.decode('utf-8')
    updated_filedata = decoded_filedata.replace(
        migration_config['filer']['search_string'], migration_config['filer']['replace_string'])
    new_message_bytes = updated_filedata.encode('utf-8')
    new_base64_bytes = base64.b64encode(new_message_bytes)
    new_base64_message = new_base64_bytes.decode('utf-8')
    return new_base64_message

print("use as python3 migrate-config.py FULL-path-to-virtualhome-config-xml")
print("Will output to the same filename with the appended extension '.new'")

migration_config = {}
with open("network-config.json", "r") as json_file:
    migration_config = json.load(json_file)

# Update Core Values
tree = ET.parse(sys.argv[1])
tree.find("./system/hostname").text = migration_config['general']['hostname']
tree.find('./system/domain').text = migration_config['general']['domain']
tree.find('./interfaces/lan/ipaddr').text = migration_config['general']['ip_address']
tree.find('./dhcpd/lan/range/from').text = migration_config['dhcp']['range_start']
tree.find('./dhcpd/lan/range/to').text = migration_config['dhcp']['range_end']

# Update Rules
firewall_nat_rules = tree.findall('./nat/outbound/rule/source/network')
for network in firewall_nat_rules:
    if network.text == migration_config['rules']['search_source_network']:
        network.text = migration_config['rules']['replace_source_network']

# Update Filer Files
filer_files = tree.findall('./installedpackages/filer/config/')
for properties in filer_files:
    if properties.tag == "filedata":
        properties.text = search_and_replace(properties.text)

tree.write(sys.argv[1] + '.new')
print("check " + sys.argv[1] + ".new for your updated config!")
