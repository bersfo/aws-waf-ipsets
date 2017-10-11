# aws-waf-ipsets - Import a list of networks in CIDR notation to a new IP set in AWS Web Application Firewall
This script creates a new IPset in AWS WAF based on input from a TXT file. It can be used with long lists of networks like the ones you can download from https://www.countryipblocks.net/country_selection.php

In addition to adding the networks to an IP set in AWS WAF, it also prunes the list of networks to a custom prefix length (i.e. /16) by folding smaller networks into their supernets dividing larger networks into their subnets.

## Inputs 
sys.argv[0] == IPset name
sys.argv[1] == path to TXT file

## Example Output
python3 ipsetimport.py Germany de.txt
Read 47765 lines from de.txt.
Pruned list of networks to 3265 /16 networks.
Added networks 0 to 9 out of 3265.
Added networks 10 to 19 out of 3265.
Added networks 20 to 29 out of 3265.
...
Added networks 3240 to 3249 out of 3265.
Added networks 3250 to 3259 out of 3265.
New IP set Germany with 3265 networks has been created.
