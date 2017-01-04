#! /usr/bin/env python

import requests
import json
import yaml

config = open('sample.cfg', 'r').read()
template = open('ios.yaml', 'r').read()

url = 'http://localhost:5000/api/parse'
payload = {'config': config, 'template': template}
headers = {'content-type': 'application/json'}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print json.dumps(yaml.load(response.json()['result']), sort_keys = True, indent = 2)
