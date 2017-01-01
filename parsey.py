#! /usr/bin/env python
import json
import os
import sys
import traceback
import re

from netmiko import ConnectHandler

class bcolors:
    m = '\033[95m'
    v = '\033[94m'
    k = '\033[92m'
    # WARNING = '\033[93m'
    # FAIL = '\033[91m'
    ENDC = '\033[0m'
    # BOLD = '\033[1m'
    # UNDERLINE = '\033[4m'

def remove_comments(lines):
    lines = [line for line in lines if not line.startswith('!')]
    return lines

def remove_banners(lines):
    length = len(lines)
    index = 0
    banners = []
    while index < length:
        if lines[index].startswith('banner'):
            banner_begin = index
            # print "%s --- %s" % (index, lines[index])
            delim = lines[index].split(' ')[2][0:2]
            while not (lines[index].startswith(delim) or  lines[index].startswith('!')):
                index += 1
                # print "%s --- %s" % (index, lines[index])
            else:
                banner_end = index
                banners.append(range(banner_begin, banner_end + 1))
        else:
            index += 1

    for banner in reversed(banners):
        for line in reversed(banner):
            # print line
            del lines[line]
    return lines


def remove_empty(lines):
    lines = [line for line in lines if line != '']
    return lines

def remove_end(lines):
    lines = [line for line in lines if line != 'end']
    return lines

def revert_no(lines):
    for index, line in enumerate(lines):
        if line.startswith('no '):
            lines[index] = (" ").join(line.split(' ')[1:])
    return lines

def parse_keywords(lines):
    keywords = set()
    for line in lines:
        if (not line.startswith(' ')):
            # print "---[%s]---" % line
            keyword = line.split(' ')[0]
            keywords.add(keyword)
    return keywords

def parse_help(lines):
    commands = {}
    for line in lines.split('\n'):
        if line.startswith('  '):
            cmd_desc = re.split("\s+", line.strip(), 1)
            commands[cmd_desc[0]] = {}
            if len(cmd_desc) == 2:
                commands[cmd_desc[0]]['hint'] = cmd_desc[1]
    return commands

def issue_help_command(device, starters):
    response = {}
    cisco = {
        'device_type': 'cisco_ios',
        'ip':   device,
        'username': 'a-bthornto',
        'password': '(9$3MJ5a2bw:YZ=',
        'verbose': False,       # optional, defaults to False
    }
    net_connect = ConnectHandler(**cisco)
    for starter in starters:
        config_commands = ([starter + ' ?'])
        try:
            output = net_connect.send_config_set(config_commands)
            schema = parse_help(output)
            response[starter] = schema
        except:
            print "Unexpected error:", sys.exc_info()[0]
            traceback.print_exc()
    return response

keywords = {}
basedir = '../network-configurations'

parser = {}
for filename in os.listdir(basedir):
    if filename.endswith("seassclsw001.starbucks.net.cfg"):
        if 'version 12' in open(basedir + '/' + filename).read():
            with open(basedir + '/' + filename) as f:
                lines = f.read().splitlines()
                lines = remove_banners(lines)
                lines = remove_comments(lines)
                lines = remove_empty(lines)
                lines = revert_no(lines)
                lines = remove_end(lines)
                for line in lines:
                    root = parser
                    if not line.startswith(' '):
                        print root
                        print bcolors.k + "Warning: No active frommets remain. Continue?" + bcolors.ENDC
                        print "Line: %s" % line
                        print "Length: %s" % len(line.split(' '))
                        response = raw_input('Enter the mask or (s)kip or (h)elp: ')
                        if response == 's' or response == 'h':
                            print 'skipped'
                        else:
                            response_parts = list(response)
                            line_parts = line.split(' ')
                            length = len(response_parts)
                            index = 0
                            while index < length:
                                if response_parts[index] == 'k':
                                    if not line_parts[index] in root:
                                        root[line_parts[index]] = {}
                                    root = root[line_parts[index]]
                                if response_parts[index] == 'v':
                                    if not 'WORD' in root:
                                        root['WORD'] = {}
                                    root = root['WORD']
                                if response_parts[index] == 'm':
                                    if not 'modifiers' in root:
                                        root['modifiers'] = set()
                                    root['modifiers'].add(line_parts[index])
                                index += 1



                        # start_at = root
                        # words = line.split(' ')
                        # globals.add(words[0])
                        # for word in words:
                        #     if not word in start_at:
                        #         start_at[word] = {}
                        #     start_at = start_at[word]

print json.dumps(parser,sort_keys=True, indent=4, separators=(',', ': '))


# globals = parse_keywords(lines)

# print globals
# print lines
#print banners
# remove the banners
# for index in lines.length():
#     print index
#
#
# for index, line in enumerate(lines):
#     if line.startswith('banner'):
#         delim = line.split(' ')[2]
#
#         print delim
# #     if not line.startswith(' '):
#         print line
#
#
# keywords = []
# for line in lines:
#     if not line.startswith(' '):
#         print line

#
# for line in reversed(lines):
#
#
#     print line

# for filename in os.listdir(basedir):
#     device_keywords = {}
#     if filename.endswith(".cfg"):
#         if 'version 12' in open(basedir + '/' + filename).read():
#             with open(basedir + '/' + filename) as f:
#                 lines = f.read().splitlines()
#
#             lines = remove_banners(lines)
#             lines = remove_comments(lines)
#             lines = remove_empty(lines)
#             lines = revert_no(lines)
#
#             length = len(lines)
#             index = 0
#
#             while index < length:
#                 print lines[index]
#                 if not lines[index].startswith(' '):
#                     keyword = lines[index].split(' ')[0]
#                     if keyword in device_keywords:
#                         device_keywords[keyword]['multiline'] = True
#                     else:
#                         device_keywords[keyword] ={}
#                     if not index + 1 == length:
#                         if lines[index + 1].startswith(' '):
#                             device_keywords[keyword]['contextable'] = True
#                 index += 1
#     keywords.update(device_keywords)
#
# print json.dumps(keywords,sort_keys=True, indent=4, separators=(',', ': '))
