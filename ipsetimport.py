# This script creates a new IPset in AWS WAF based on input from a TXT file
# Last change by sstein on 10/10/2017
# --
# Input: sys.argv[0] == IPset name; sys.argv[1] == path to TXT file
# --
# Boto3 Documentation: https://boto3.readthedocs.io/en/latest/reference/services/waf.html

import sys
import boto3
import ipaddress

# PUT IN YOUR AWS CREDS HERE
aws_datacenter = ''
aws_accesskey = ''
aws_securekey = ''

client = boto3.client(
    'waf-regional',
    region_name=aws_datacenter,
    aws_access_key_id=aws_accesskey,
    aws_secret_access_key=aws_securekey
)

ipset_name = sys.argv[0] # Example: Germany
cidr_file = sys.argv[1] # Example: de.txt

# Creates a new IP set in AWS WAF
def create_ipset(ipset_name):
    cToken = client.get_change_token()
    return client.create_ip_set(
        Name = ipset_name,
        ChangeToken = cToken['ChangeToken']
    )

# Adds a list of CIDRs to an AWS WAF IP set
def update_ipset(ipset, ip_list):
    # Build list of updates to process
    updates = []
    for ip in ip_list:
        action = {
            'Action': 'INSERT',
            'IPSetDescriptor': {
                'Type': 'IPV4',
                'Value': ip
            }
        }
        updates.append(action)
    # Break up list of updates to comply with API limitations
    roundsof10 = int(updates.__len__() / 10)
    updateround = []
    j_last = 0
    for i in range(roundsof10):
        del updateround[:]
        for j in range((i*10),(i*10)+10):
            updateround.append(updates[j])
        # Make API call to add 10 networks
        client.update_ip_set(
            ChangeToken = client.get_change_token()['ChangeToken'],
            IPSetId = ipset['IPSet']['IPSetId'],
            Updates = updateround
        )
        print('Added networks ' + str((i * 10)) + ' to ' + str(j) + ' out of ' + str(updates.__len__()) + '.')
        j_last = j
    del updateround[:]
    for i in range((j_last+1), updates.__len__()):
        updateround.append(updates[i])
    client.update_ip_set(
        ChangeToken=client.get_change_token()['ChangeToken'],
        IPSetId=ipset['IPSet']['IPSetId'],
        Updates=updateround
    )
    return True

# Minimize list of IPv4 networks:
# 1. collapses networks smaller than /16 into /16 supernet
# 2. divides networks larger than /16 into /16 subnets
# 3. removes duplicates from the resulting list of /16 networks
# prefixlength is adjustable (doesn't need to be 16)
def minimize_networkList(cidrlist, prefixlength = 16):
    pruned_cidrlist = []
    for cidr in cidrlist:
        network = ipaddress.ip_network(cidr)
        # normalize all networks on prefixlength
        if network.prefixlen >= prefixlength:
            supernet = network.supernet(new_prefix = prefixlength)
            pruned_cidrlist.append(supernet.__str__())
        if network.prefixlen < prefixlength:
            subnets = network.subnets(new_prefix = prefixlength)
            for subnet in subnets:
                pruned_cidrlist.append(subnet.__str__())
        # remove duplicates
    pruned_cidrlist = (set(pruned_cidrlist))
    return pruned_cidrlist

# Reads a TXT file that contains a CIDR per line and returns a list of cidrs
def read_TXTlist(file):
    file_object = open(file, 'r')
    cidrlist = []
    for line in file_object:
        cidrlist.append(line[:-1])
    return cidrlist

def main():
    # Receive all existing IP sets from AWS WAF
    ipsets = client.list_ip_sets(Limit = 100)['IPSets']
    # Check whether an IP set with this name already exists (Abort if it does.)
    for ipset in ipsets:
        if ipset['Name'] == ipset_name:
            print('IP set "' + ipset_name + '" already exists - Script aborted.')
            return False

    # Read list of networks in CIDR notation from TXT file
    cidrlist_raw = read_TXTlist(cidr_file)
    print('Read ' + str(cidrlist_raw.__len__()) + ' lines from ' + cidr_file + '.')

    # Prune the list of networks
    cidrlist_16 = minimize_networkList(cidrlist_raw,16)
    print('Pruned list of networks to ' + str(cidrlist_16.__len__()) + ' /16 networks.')

    # Create new IP set in AWS WAF and update it with the list of pruned networks
    new_ipset = create_ipset(ipset_name)
    update_ipset(new_ipset, cidrlist_16)
    print('New IP set ' + ipset_name + ' with ' + str(cidrlist_16.__len__()) + ' networks has been created.')


if __name__ == "__main__":
    main()
