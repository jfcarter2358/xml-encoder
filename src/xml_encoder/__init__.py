import xml.etree.ElementTree as ET
import base64
import os
import sys

global counter
counter = 0
global encoded
encoded = ''
global decoded
decoded = ET.Element
global namespaces
namespaces = {
    'http://www.omg.org/spec/BPMN/20100524/MODEL': 'bpmn',
    'http://www.omg.org/spec/BPMN/20100524/DI': 'bpmndi', 
    'http://www.omg.org/spec/DD/20100524/DC': 'dc',
    'http://camunda.org/schema/1.0/bpmn': 'camunda',
    'http://www.w3.org/2001/XMLSchema-instance': 'xsi',
    'http://www.omg.org/spec/DD/20100524/DI': 'di'
}
global tags
tags = []
global attrib_keys
attrib_keys = []
global attrib_values
attrib_values = []

def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem   

def print_table(header, data, min_width=8):
    column_widths = []
    for h in header:
        if len(h) > min_width:
            column_widths.append(len(h))
        else:
            column_widths.append(min_width)
    for d in data:
        for i in range(0, len(column_widths)):
            if len(d[i]) > column_widths[i]:
                column_widths[i] = len(d[i])

    lines = []
    # create top border
    line = '+-'
    for cw in column_widths:
        line += '-' * cw
        line += '-+-'
    line = line[:-1]
    lines.append(line)
    # create header
    line = '| '
    for i in range(0, len(column_widths)):
        line += header[i] + (' ' * (column_widths[i] - len(header[i])))
        line += ' | '
    line = line[:-1]
    lines.append(line)
    # create header divider line
    line = '+='
    for cw in column_widths:
        line += '=' * cw
        line += '=+='
    line = line[:-1]
    lines.append(line)
    for d in data:
        # print data
        line = '| '
        for i in range(0, len(column_widths)):
            line += d[i] + (' ' * (column_widths[i] - len(d[i])))
            line += ' | '
        line = line[:-1]
        lines.append(line)
    # create bottom border
    line = '+-'
    for cw in column_widths:
        line += '-' * cw
        line += '-+-'
    line = line[:-1]
    lines.append(line)
    
    # output
    print('\n'.join(lines))

# encode XML into format of {parent}|{tag}|{attrib_name_code_1}:{attrib_value_1}:{attrib_name_code_2}:{attrib_value_2}:...|{text},
def encode_elem(elem, parent):
    global counter
    global encoded
    global namespaces
    global tags
    global attrib_keys
    global attrib_values

    parent_str = str(parent)
    
    raw_attribs = elem.attrib
    raw_tag = '{}:{}'.format(namespaces[elem.tag.split('}')[0][1:]], elem.tag.split('}')[1])
    text = elem.text
    if text:
        text = text.strip()
    
    tag = -1
    attribs = ''

    if raw_tag in tags:
        tag = str(tags.index(raw_tag))
    else:
        tag = str(len(tags))
        tags.append(raw_tag)
    for k in raw_attribs:
        key = -1
        val = -1
        if k in attrib_keys:
            key = str(attrib_keys.index(k))
        else:
            key = str(len(attrib_keys))
            attrib_keys.append(k)
        v = raw_attribs[k]
        if v in attrib_values:
            val = str(attrib_values.index(v))
        else:
            val = str(len(attrib_values))
            attrib_values.append(v)
        attribs += f'{key}:{val}:'
    attribs = attribs[:-1]
    if text:
        text_bytes = text.encode('utf-8')
        base64_bytes = base64.b64encode(text_bytes)
        base64_text = base64_bytes.decode('utf-8').rstrip('=')
        out = f'{parent_str}|{tag}|{attribs}|{base64_text},'
    else:
        out = f'{parent_str}|{tag}|{attribs},'
    encoded += out
    
    ident = counter
    counter += 1

    for child in elem:
        encode_elem(child, ident)

def encode(path_in, path_out):
    global counter
    global encoded
    global namespaces
    global tags
    global attrib_keys
    global attrib_values
    counter = 0
    encoded = ''
    tags = []
    attrib_keys = []
    attrib_values = []
    
    tree = ET.parse(path_in)
    root = tree.getroot()

    encode_elem(root, -1)
    encoded = encoded[:-1]

    tag_string = ''
    attrib_keys_string = ''
    attrib_values_string = ''
    for t in tags:
        t_bytes = t.encode('utf-8')
        base64_bytes = base64.b64encode(t_bytes)
        base64_t = base64_bytes.decode('utf-8').rstrip('=')
        tag_string += base64_t + ':'
    tag_string = tag_string[:-1]
    for k in attrib_keys:
        k_bytes = k.encode('utf-8')
        base64_bytes = base64.b64encode(k_bytes)
        base64_k = base64_bytes.decode('utf-8').rstrip('=')
        attrib_keys_string += base64_k + ':'
    attrib_keys_string = attrib_keys_string[:-1]
    for v in attrib_values:
        v_bytes = v.encode('utf-8')
        base64_bytes = base64.b64encode(v_bytes)
        base64_v = base64_bytes.decode('utf-8').rstrip('=')
        attrib_values_string += base64_v + ':'
    attrib_values_string = attrib_values_string[:-1]
    
    encoded = f'{tag_string}|{attrib_keys_string}|{attrib_values_string},{encoded}'

    with open(path_out, 'w') as f:
        f.write(encoded)

def decode_elem(data):
    global counter
    global decoded
    global namespaces
    global tags
    global attrib_keys
    global attrib_values
    parts = data.split('|')

    parent = parts[0]
    tag = tags[int(parts[1])]
    raw_attribs = parts[2].split(':')
    attribs = {}
    text = None
    if len(parts) > 3:
        b64_text = parts[3]
        b64_text += '=' * (len(b64_text) % 4)
        base64_bytes = b64_text.encode('utf-8')
        text_bytes = base64.b64decode(base64_bytes)
        text = text_bytes.decode('utf-8')

    if len(raw_attribs) > 1:
        for i in range(0, len(raw_attribs), 2):
            k_int = int(raw_attribs[i])
            v_int = int(raw_attribs[i + 1])

            attribs[attrib_keys[k_int]] = attrib_values[v_int]
    attribs['encoding_id'] = counter
    counter += 1

    if parent == '-1':
        decoded = ET.Element(tag)
        decoded.attrib = attribs
        if text:
            decoded.text = text
    else:
        parent_elem = None
        for elt in decoded.iter():
            if elt.attrib['encoding_id'] == int(parent):
                parent_elem = elt
        if parent_elem == None:
            raise ValueError('No parent found')
        elem = ET.Element(tag)
        elem.attrib = attribs
        if text:
            elem.text = text
        parent_elem.append(elem)

def decode(path_in, path_out):
    global counter
    global decoded
    global namespaces
    global tags
    global attrib_keys
    global attrib_values
    counter = 0
    decoded = ET.Element
    tags = []
    attrib_keys = []
    attrib_values = []

    with open(path_in) as f:
        data = f.read()

    items = data.split(',')
    header = items[0].split('|')
    items = items[1:]

    for b64_t in header[0].split(':'):
        b64_t += '=' * (len(b64_t) % 4)
        base64_bytes = b64_t.encode('utf-8')
        t_bytes = base64.b64decode(base64_bytes)
        t = t_bytes.decode('utf-8')
        tags.append(t)

    for b64_k in header[1].split(':'):
        b64_k += '=' * (len(b64_k) % 4)
        base64_bytes = b64_k.encode('utf-8')
        k_bytes = base64.b64decode(base64_bytes)
        k = k_bytes.decode('utf-8')
        attrib_keys.append(k)

    for b64_v in header[2].split(':'):
        b64_v += '=' * (len(b64_v) % 4)
        base64_bytes = b64_v.encode('utf-8')
        v_bytes = base64.b64decode(base64_bytes)
        v = v_bytes.decode('utf-8')
        attrib_values.append(v)

    for item in items:
        decode_elem(item)


    indent(decoded)
    for n in namespaces:
        decoded.attrib[f'xmlns:{namespaces[n]}'] = n

    decoded_tree = ET.ElementTree(decoded)

    for elem in decoded_tree.iter():
        del elem.attrib['encoding_id']
    with open(path_out, 'wb') as f:
        decoded_tree.write(f)
    with open(path_out) as f:
        data = f.read()
    data = '<?xml version="1.0" encoding="UTF-8"?>\n' + data
    with open(path_out, 'w') as f:
        f.write(data)

if __name__ == '__main__':
    if sys.argv[1] == 'encode':
        if len(sys.argv) > 5:
            extension = sys.argv[5]
        else:
            extension = '.exml'
        sizes = []
        if sys.argv[2] == 'file':
            encode(sys.argv[3], sys.argv[4])
            start_size = os.path.getsize(sys.argv[3])
            end_size = os.path.getsize(sys.argv[4])
            if start_size == 0:
                percentage = 'NA'
            else:
                percentage = "{:.2f}".format(end_size / start_size)
            sizes.append((sys.argv[3], sys.argv[4], str(start_size), str(end_size), percentage))
        elif sys.argv[2] == 'dir':
            files = [f for f in os.listdir(sys.argv[3])]
            for fi in files:
                out_base = fi[:fi.rfind('.')]
                path_in = f'{sys.argv[3]}/{fi}'
                path_out = f'{sys.argv[4]}/{out_base}.{extension}'
                encode(path_in, path_out)
                start_size = os.path.getsize(path_in)
                end_size = os.path.getsize(path_out)
                if start_size == 0:
                    percentage = 'NA'
                else:
                    percentage = "{:.2f}".format(end_size / start_size)
                sizes.append((path_in, path_out, str(start_size), str(end_size), percentage))
            total_start = 0
            total_end = 0
            for s in sizes:
                total_start += int(s[2])
                total_end += int(s[3])
            if total_start == 0:
                percentage = 'NA'
            else:
                percentage = "{:.2f}".format(total_end / total_start)
            sizes.append((sys.argv[3], sys.argv[4], str(total_start), str(total_end), percentage))
        print_table(['in', 'out', 'in_size', 'out_size', 'percentage'], sizes)
    elif sys.argv[1] == 'decode':
        if len(sys.argv) > 5:
            extension = sys.argv[5]
        else:
            extension = '.xml'
        sizes = []
        if sys.argv[2] == 'file':
            decode(sys.argv[3], sys.argv[4])
            start_size = os.path.getsize(sys.argv[3])
            end_size = os.path.getsize(sys.argv[4])
            if start_size == 0:
                percentage = 'NA'
            else:
                percentage = "{:.2f}".format(end_size / start_size)
            sizes.append((sys.argv[3], sys.argv[4], str(start_size), str(end_size), percentage))
        elif sys.argv[2] == 'dir':
            files = [f for f in os.listdir(sys.argv[3])]
            for fi in files:
                out_base = fi[:fi.rfind('.')]
                path_in = f'{sys.argv[3]}/{fi}'
                path_out = f'{sys.argv[4]}/{out_base}.{extension}'
                decode(path_in, path_out)
                start_size = os.path.getsize(path_in)
                end_size = os.path.getsize(path_out)
                if start_size == 0:
                    percentage = 'NA'
                else:
                    percentage = "{:.2f}".format(end_size / start_size)
                sizes.append((path_in, path_out, str(start_size), str(end_size), percentage))
            total_start = 0
            total_end = 0
            for s in sizes:
                total_start += int(s[2])
                total_end += int(s[3])
            if total_start == 0:
                percentage = 'NA'
            else:
                percentage = "{:.2f}".format(total_end / total_start)
            sizes.append((sys.argv[3], sys.argv[4], str(total_start), str(total_end), percentage))
        print_table(['in', 'out', 'in_size', 'out_size', 'percentage'], sizes)
