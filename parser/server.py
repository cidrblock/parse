#!flask/bin/python
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

def parse(lines, global_keywords, prepend = None):
    response = {}
    parsed = {}
    lines_index = 0
    lines_length = len(lines)
    while lines_index != lines_length:
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
            while line_index < line_length:
                if current_root and line_parts[line_index] in current_root:
                    new_line.append('<span class="keyword">' + line_parts[line_index] + '</span>')
                    if not line_parts[line_index] in parsed_root:
                        if current_root[line_parts[line_index]] and isinstance(current_root[line_parts[line_index]], dict):
                            vars = [k for k in  current_root[line_parts[line_index]] if k.startswith('$') and k != '$word']
                            if vars:
                                parsed_root[line_parts[line_index]] = []
                            else:
                                parsed_root[line_parts[line_index]] = {}
                        else:
                            parsed_root[line_parts[line_index]] = {}
                    current_root = current_root[line_parts[line_index]]
                    parsed_root = parsed_root[line_parts[line_index]]
                    line_index += 1
                elif current_root and any([k.startswith('$') for k in [s for s in current_root if isinstance(s,str)]]):
                    if isinstance(current_root, dict):
                        vars = [k for k in  current_root if k.startswith('$')]
                        existing = [d for d in  parsed_root if d[vars[0][1:]] == line_parts[line_index] ]
                        if not existing:
                            parsed_root.append({ vars[0][1:]: line_parts[line_index] })
                        existing = [d for d in  parsed_root if d[vars[0][1:]] == line_parts[line_index] ]
                        new_line.append('<span class="value">' + line_parts[line_index] + '</span>')
                        current_root = current_root[vars[0]]
                        parsed_root = existing[0]
                        line_index += 1
                    if isinstance(current_root, list):
                        remainder = 'string'
                        dicts = [d for d in current_root if isinstance(d,dict)]
                        for entry in dicts:
                            for key in entry:
                                if key == 'remainder':
                                    remainder = entry['remainder']
                        strings = [s for s in current_root if isinstance(s,str)]
                        vars = [k for k in strings if k.startswith('$')]
                        vars_index = 0
                        vars_length = len(vars)
                        entry = {}
                        while vars_index < vars_length:
                            if line_index + vars_index > line_length - 1:
                                entry[vars[vars_index][1:]] = ''
                                vars_index += 1
                            else:
                                if vars[vars_index][1:].endswith('s'):
                                    keyword = vars[vars_index][1:]
                                    entry[keyword] = []
                                    start = vars_index
                                    for line_part in line_parts[line_index + vars_index:]:
                                        entry[keyword].append(line_parts[line_index + vars_index])
                                        new_line.append('<span class="value">' + line_parts[line_index + vars_index] + '</span>')
                                        vars_index += 1
                                    line_index = line_length
                                else:
                                    entry[vars[vars_index][1:]] = line_parts[line_index + vars_index]
                                    new_line.append('<span class="value">' + line_parts[line_index + vars_index] + '</span>')
                                    vars_index += 1
                        if line_index + vars_length < line_length:
                            entry[remainder] = (' ').join(line_parts[line_index + vars_length:]).strip()
                            new_line.append('<span class="value">' + entry[remainder] + '</span>')
                        if not 'lines' in parsed_root:
                            parsed_root['lines'] = []
                        parsed_root['lines'].append(entry)
                        line_index = line_length
                else:
                    value = (' ').join(line_parts[line_index:])
                    if line_index > 0:
                        new_line.append('<span class="value">' + value + '</span>')
                        if not 'lines' in parsed_root:
                            parsed_root['lines'] = []
                        parsed_root['lines'].append({ 'string': value })
                    else:
                        new_line.append('<span class="not_parsed">' + value + '</span>')
                    line_index = line_length
            if negate:
                if 'lines' in parsed_root:
                    parsed_root['lines'][-1]['negate'] = True
                else:
                    parsed_root['negate'] = True
            lines[lines_index] = (' ').join(new_line)
            if not lines_index + 1 >= lines_length - 1:
                if lines[lines_index + 1 ].startswith(' '):
                    context_lines = []
                    start_line = lines_index + 1
                    while lines[lines_index + 1].startswith(" "):
                        context_lines.append(lines[lines_index + 1].strip())
                        lines_index += 1
                    dicts = [d for d in current_root if isinstance(d,dict)]
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
                        lines[start_line:lines_index + 1] = result['config']
                        if 'lines' in parsed_root:
                            parsed_root['lines'][-1]['context'] = result['parsed']
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
