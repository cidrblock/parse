#!/usr/bin/env python
import re
import json
from flask import Flask, render_template, request, url_for, jsonify
import yaml

from yaml.representer import Representer
from yaml.dumper import Dumper
from yaml.emitter import Emitter
from yaml.serializer import Serializer
from yaml.resolver import Resolver


app = Flask(__name__, static_url_path='')

class MyRepresenter(Representer):
    def represent_none(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:null', u'')
    def unicode_representer(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:str', data.encode('utf-8'))

class MyDumper(Emitter, Serializer, MyRepresenter, Resolver):
    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        MyRepresenter.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style)
        Resolver.__init__(self)

MyRepresenter.add_representer(type(None), MyRepresenter.represent_none)
MyRepresenter.add_representer(unicode, MyRepresenter.unicode_representer)

def remove_lines(lines,regexs):
    for r_str in regexs:
        regex = re.compile(r_str)
        lines = [i for i in lines if not regex.search(i)]
    return lines

def next_is(entry):
    if isinstance(entry,dict):
        return 'dict'
    if isinstance(entry,list):
        return 'list'
    else:
        print "Error: next is nothing"

def parse(lines, global_keywords, prepend = None):
    response = {}
    # check what we came in with, could be a list if a context
    if isinstance(global_keywords, dict):
        parsed = {}
    if isinstance(global_keywords, list):
        parsed = []
    lines_index = 0
    lines_length = len(lines)
    while lines_index < lines_length:
        current_root = global_keywords
        parsed_root = parsed
        if not lines[lines_index].startswith(' '):
            if not prepend:
                new_line = []
            else:
                new_line = ['<span></span>']
            line_index = 0
            line_parts = lines[lines_index].split()
            if line_parts[0] == 'no':
                line_parts.pop(0)
                negate = True
                new_line.append('<span class="keyword">no</span>')
            else:
                negate = False
            line_length = len(line_parts)
            depth = 0
            while line_index < line_length:
                working_word = line_parts[line_index]
                crt = type(current_root).__name__
                wildcard = False
                gobble = False
                remainer_specified = False
                remainder_word = 'values'
                if crt == 'dict':
                    vars = [k for k in  current_root if k.startswith('$')]
                    if vars:
                        if len(vars) != 1:
                            print "Error: more than one $ in current root"
                        else:
                            wildcard = True
                            wildcard_actual = vars[0]
                            wildcard_parsed = vars[0][1:]
                    if 'remainder' in current_root:
                        remainer_specified = True
                        remainder_word = current_root['remainder']
                if crt == 'list':
                    cr_strings = [s for s in current_root if isinstance(s,str)]
                    cr_dicts = [d for d in current_root if isinstance(d,dict)]
                    if line_index < depth + len(cr_strings):
                        if cr_strings[line_index - depth].startswith('$'):
                            wildcard = True
                            wildcard_actual = cr_strings[line_index - depth]
                            wildcard_parsed = cr_strings[line_index - depth][1:]
                    for cr_dict in cr_dicts:
                        if 'remainder' in cr_dict.keys():
                            remainer_specified = True
                            remainder_word = cr_dict.get('remainder', remainder_word)
                if current_root:
                    if crt == 'dict' and working_word in current_root:
                        if not working_word in parsed_root:
                            if isinstance(current_root[working_word], dict):
                                vars = [k for k in current_root[working_word].keys() if k.startswith('$')]
                                if vars:
                                    if len(vars) != 1:
                                        print "Error: more than one $ in current root"
                                    else:
                                        parsed_root[working_word] = []
                                else:
                                    parsed_root[working_word] = {}
                            if isinstance(current_root[working_word], list):
                                parsed_root[working_word] = []
                            if current_root[working_word] is None:
                                parsed_root[working_word] = {}

                        parsed_root = parsed_root[working_word]
                        current_root = current_root[working_word]
                        depth += 1
                        new_line.append('<span class="keyword">' + working_word + '</span>')
                        line_index += 1

                    elif crt == 'dict' and wildcard:
                        if isinstance(parsed_root, dict):
                            parsed_root[working_word] = {}
                            parsed_root = parsed_root[working_word]
                        if isinstance(parsed_root, list):
                            exisiting = None
                            for entry in parsed_root:
                                if entry.get(wildcard_parsed) == working_word:
                                    exisiting = entry
                            if exisiting:
                                parsed_root = exisiting['entries']
                            else:
                                parsed_root.append({ wildcard_parsed: working_word, 'entries': [] })
                                parsed_root = parsed_root[-1]['entries']
                        current_root = current_root[wildcard_actual]
                        depth += 1
                        new_line.append('<span class="value">' + working_word + '</span>')
                        line_index += 1
                    elif crt == 'list' and wildcard:
                        if isinstance(parsed_root, list):
                            parsed_root.append({})
                            parsed_root = parsed_root[-1]
                        parsed_root[wildcard_parsed] = working_word
                        new_line.append('<span class="value">' + working_word + '</span>')
                        line_index += 1
                    else:
                      gobble = True
                else:
                    gobble = True
                if gobble:
                    if remainder_word.endswith('s') and remainder_word != 'values':
                        parsed_root[remainder_word] = line_parts[line_index:]
                        for word in line_parts[line_index:]:
                            new_line.append('<span class="value">' + word + '</span>')
                    else:
                        if not remainder_word in parsed_root:
                            parsed_root[remainder_word] = []
                        parsed_root[remainder_word].append((' ').join(line_parts[line_index:]))
                        new_line.append('<span class="value">' + (' ').join(line_parts[line_index:]) + '</span>')
                    line_index = line_length
                if negate and line_index == line_length:
                    if isinstance(parsed_root, list):
                        parsed_root.append({})
                        parsed_root = parsed_root[-1]
                    parsed_root['negate'] = True
            lines[lines_index] = (' ').join(new_line)

            if lines_index + 2 < lines_length:
                if lines[lines_index + 1 ].startswith(' '):
                    lines_index += 1
                    context_lines = []
                    start_line = lines_index
                    while lines[lines_index].startswith(" "):
                        context_lines.append(lines[lines_index].strip())
                        #watch for EOF
                        if lines_index == lines_length - 1 :
                            lines_index += 1
                            break
                        lines_index += 1
                    if current_root:
                        dicts = [d for d in current_root if isinstance(d,dict)]
                    else: dicts = []
                    context = None
                    for entry in dicts:
                        for key in entry:
                            if key == 'context':
                                context = entry['context']
                    if current_root and 'context' in current_root:
                        context = current_root['context']
                    if context:
                        result = parse(context_lines, context, True)
                        for line in result['config']:
                            line = " " + line
                        # print "took", len(context_lines)
                        # print "are", context_lines
                        # print "before", len(lines)
                        # print "result_length", len(result['config'])
                        # print "swapping", len(lines[start_line:lines_index])
                        lines[start_line:lines_index] = result['config']
                        # print "after", len(lines)

                        if 'values' in parsed_root:
                            parsed_root['values'][-1]['context'] = result['parsed']
                        else:
                            parsed_root['context'] = result['parsed']
                    lines_index -= 1
        lines_index += 1
    response['config'] = lines
    response['parsed'] = parsed
    return response

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/api/parse', methods=['POST'])
def api():
    incoming = request.json
    try:
        template = (yaml.safe_load(incoming['template']))
        lines = incoming['config'].split('\n')
        if 'remove_lines' in template['config']:
            lines = remove_lines(lines, template['config']['remove_lines'])
        global_keywords = template['global_keywords']
        response = parse(lines, global_keywords)
        response['parsed'] = yaml.dump(response['parsed'], allow_unicode=False, indent=2, Dumper=MyDumper, default_flow_style=False)
        response['config'] = ('\n').join(response['config'])
        return jsonify({ 'config': response['config'], 'result': response['parsed'] })

    except SyntaxError:
        return 400

@app.route('/api/sort', methods=['POST'])
def sort():
    incoming = request.json
    try:
        template = yaml.safe_load(incoming['template'])
        return jsonify({ 'template': yaml.dump(template, allow_unicode=True, indent=2, Dumper=MyDumper, default_flow_style=False ) })

    except SyntaxError:
        return 400

if __name__ == '__main__':
    app.run(debug=True)
