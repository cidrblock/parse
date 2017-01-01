#! /usr/bin/env python
import cson
import re
from pprint import pprint

filename = 'seassclrt001.starbucks.net.ios'

with open('cisco.cson') as cson_data:
    d = cson.load(cson_data)

# pprint(d['patterns'])

for entry in d['patterns']:
    for k in entry.keys():
        if k == 'include':
            if entry[k].startswith('#'):
                print entry[k]
            else:
                print "Error: missing # %s" % entry[k]

# for entry in d['patterns']:
#     for k in entry.keys():
#         if k == 'include':
#             print entry[k]
        # if k == 'match':
        #     pattern = re.compile(entry[k])
        #     for i, line in enumerate(open(filename)):
        #         for match in re.finditer(pattern, line):
        #             if not line.startswith('!'):
        #                 length = len(match.groups())
        #                 if length == 1:
        #                     keyword = match.groups()[0]
        #                     print keyword
        #                     print line.split(keyword)
