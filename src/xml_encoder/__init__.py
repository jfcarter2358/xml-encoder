import base64
import os
import re
import sys
import xml.etree.ElementTree

def ascii_replace(text: str):
    """
    replace quotes with their ASCII character representation

    Args:
        text (str): text to replace in

    Returns:
        str: replaced text
    """
    text = text.replace("'", "&#39;")
    text = text.replace("[&#39;", "['")

    text = text.replace("&#39;]", "']")

    return text


def get_namespaces(contents: str, namespaces: dict = None):
    """
    Find all namespaces in XML document

    Args:
        contents (str): Text contents of XML file
        namespaces (dict, optional): Existing namespaces to update. Defaults to
            None.

    Returns:
        dict: All namespaces found in document
    """

    if namespaces is None:
        namespaces = {}
    matches = re.findall(r'xmlns:([a-zA-Z0-9]*)="(\S*)"', contents)
    for name, url in matches:
        namespaces[url] = name
    return namespaces


def indent(elem: xml.etree.ElementTree.Element, level: int = 0):
    """
    Indent xml text

    Args:
        elem (xml.etree.ElementTree.Element): Element to indent
        level (int, optional): Indentation level. Defaults to 0.

    Returns:
        xml.etree.ElementTree.Element: Element with proper indentation applied
    """

    i = "\n" + level * "  "
    j = "\n" + (level - 1) * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


def print_table(header: list, data: list, min_width: int = 8):
    """
    Print dictionary output as an ASCII table

    Args:
        header (list): Column name strings
        data (list): Data to print out with each row contained in a list or
            tuple
        min_width (int, optional): Minimum column width. Defaults to 8.
    """

    column_widths = []
    for name in header:
        if len(name) > min_width:
            column_widths.append(len(name))
        else:
            column_widths.append(min_width)
    for datum in data:
        for i, width in enumerate(column_widths):
            if len(str(datum[i])) > width:
                column_widths[i] = len(str(datum[i]))

    lines = []

    # create top border
    line = "+-"
    for column_width in column_widths:
        line += "-" * column_width
        line += "-+-"
    line = line[:-1]
    lines.append(line)

    # create header
    line = "| "
    for i, column_width in enumerate(column_widths):
        line += header[i] + (" " * (column_width - len(header[i])))
        line += " | "
    line = line[:-1]
    lines.append(line)

    # create header divider line
    line = "+="
    for column_width in column_widths:
        line += "=" * column_width
        line += "=+="
    line = line[:-1]
    lines.append(line)
    for datum in data:
        # print data
        line = "| "
        for i, column_width in enumerate(column_widths):
            line += str(datum[i]) + (" " * (column_width - len(str(datum[i]))))
            line += " | "
        line = line[:-1]
        lines.append(line)

    # create bottom border
    line = "+-"
    for column_width in column_widths:
        line += "-" * column_width
        line += "-+-"
    line = line[:-1]
    lines.append(line)

    # output
    print("\n".join(lines))


def encode_elem(
    elem: xml.etree.ElementTree.Element,
    parent: int,
    encoded: str,
    counter: int,
    tags: list = None,
    attrib_keys: list = None,
    attrib_values: list = None,
    namespaces: dict = None,
):
    """
    Encode XML into format of {parent}|{tag}|{attrib_name_code_1}:
        {attrib_value_1}:{attrib_name_code_2}:{attrib_value_2}:...|{text},

    Args:
        elem (xml.etree.ElementTree.Element): Element to encode
        parent (int): Index of parent element
        encoded (str): Encoded string
        counter (int): Element index in document
        tags (list, optional): Global list of element tag strings. Defaults to
            None.
        attrib_keys (list, optional): Global list of element attribute key
            strings. Defaults to None.
        attrib_values (list, optional): Global list of element attribute value
            strings. Defaults to None.
        namespaces (dict, optional): XML document namespaces. Defaults to None.

    Returns:
        str, list, list, list, int: Encoded element, updated tags, updated,
            attrib_keys, updated attrib_values, updated counter
    """
    if namespaces is None:
        namespaces = {}
    if tags is None:
        tags = []
    if attrib_keys is None:
        attrib_keys = []
    if attrib_values is None:
        attrib_values = []

    parent_str = str(parent)

    raw_attribs = elem.attrib
    raw_tag = "{}:{}".format(
        namespaces[elem.tag.split("}")[0][1:]], elem.tag.split("}")[1]
    )
    text = elem.text
    if text:
        text = text.strip()

    tag = -1
    attribs = ""

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
        value = raw_attribs[k]
        if value in attrib_values:
            val = str(attrib_values.index(value))
        else:
            val = str(len(attrib_values))
            attrib_values.append(value)
        attribs += f"{key}:{val}:"
    attribs = attribs[:-1]
    if text:
        text_bytes = text.encode("utf-8")
        base64_bytes = base64.b64encode(text_bytes)
        base64_text = base64_bytes.decode("utf-8").rstrip("=")
        out = f"{parent_str}|{tag}|{attribs}|{base64_text},"
    else:
        out = f"{parent_str}|{tag}|{attribs},"
    encoded += out

    ident = counter
    counter += 1

    for child in elem:
        encoded, tags, attrib_keys, attrib_values, counter = encode_elem(
            child,
            ident,
            encoded,
            counter,
            tags=tags,
            attrib_keys=attrib_keys,
            attrib_values=attrib_values,
            namespaces=namespaces,
        )

    return encoded, tags, attrib_keys, attrib_values, counter


def encode(path_in: str, path_out: str):
    """
    Encode XML document

    Args:
        path_in (str): Path to file to encode
        path_out (str): Path to file to decode
    """
    encoded = ""
    tags = []
    attrib_keys = []
    attrib_values = []

    tree = xml.etree.ElementTree.parse(path_in)
    root = tree.getroot()

    with open(path_in) as file_obj:
        namespaces = get_namespaces(file_obj.read())

    del namespaces["http://www.w3.org/2001/XMLSchema-instance"]

    encoded, tags, attrib_keys, attrib_values, _ = encode_elem(
        root, -1, encoded, 0, namespaces=namespaces
    )
    encoded = encoded[:-1]

    tag_string = ""
    attrib_keys_string = ""
    attrib_values_string = ""
    namespaces_string = ""

    for namespace in namespaces:
        n_bytes = f"{namespace}|{namespaces[namespace]}".encode("utf-8")
        base64_bytes = base64.b64encode(n_bytes)
        base64_n = base64_bytes.decode("utf-8").rstrip("=")
        namespaces_string += base64_n + ":"
    namespaces_string = namespaces_string[:-1]
    for tag in tags:
        t_bytes = tag.encode("utf-8")
        base64_bytes = base64.b64encode(t_bytes)
        base64_t = base64_bytes.decode("utf-8").rstrip("=")
        tag_string += base64_t + ":"
    tag_string = tag_string[:-1]
    for key in attrib_keys:
        k_bytes = key.encode("utf-8")
        base64_bytes = base64.b64encode(k_bytes)
        base64_k = base64_bytes.decode("utf-8").rstrip("=")
        attrib_keys_string += base64_k + ":"
    attrib_keys_string = attrib_keys_string[:-1]
    for value in attrib_values:
        v_bytes = value.encode("utf-8")
        base64_bytes = base64.b64encode(v_bytes)
        base64_v = base64_bytes.decode("utf-8").rstrip("=")
        attrib_values_string += base64_v + ":"
    attrib_values_string = attrib_values_string[:-1]

    encoded = f"{namespaces_string}|{tag_string}|{attrib_keys_string}|" + \
        f"{attrib_values_string},{encoded}"

    with open(path_out, "w") as file_obj:
        file_obj.write(encoded)


def decode_elem(
    data, decoded, counter, tags=None, attrib_keys=None, attrib_values=None
):
    """
    Decode encoded string into XML element

    Args:
        data (str): Encoded string to Decode
        decoded (xml.etree.ElementTree.Element): XMl Element to hold decoded
            tree
        counter (int): Index of encoded string in document
        tags (list, optional): Global list of element tag strings. Defaults to
            None.
        attrib_keys (list, optional): Global list of element attribute key
            strings. Defaults to None.
        attrib_values (list, optional): Global list of element attribute value
            strings. Defaults to None.

    Raises:
        ValueError: No parent element if found

    Returns:
        xml.etree.ElementTree.Element, list, list, list, int: Decoded element,
            updated tags, updated, attrib_keys, updated attrib_values, updated
            counter
    """

    if tags is None:
        tags = []
    if attrib_keys is None:
        attrib_keys = []
    if attrib_values is None:
        attrib_values = []

    parts = data.split("|")

    parent = int(parts[0])
    tag = tags[int(parts[1])]
    raw_attribs = parts[2].split(":")
    attribs = {}
    text = None

    if len(parts) > 3:
        b64_text = parts[3]
        b64_text += "=" * (len(b64_text) % 4)
        base64_bytes = b64_text.encode("utf-8")
        text_bytes = base64.b64decode(base64_bytes)
        text = text_bytes.decode("utf-8")

    if len(raw_attribs) > 1:
        k_int = None
        v_int = None
        for i, attrib in enumerate(raw_attribs):
            if i % 2 == 0:
                k_int = int(attrib)
            else:
                v_int = int(attrib)
                attribs[attrib_keys[k_int]] = attrib_values[v_int]

    attribs["encoding_id"] = counter
    counter += 1

    if parent == -1:
        decoded = xml.etree.ElementTree.Element(tag)
        decoded.attrib = attribs
        if text:
            decoded.text = text
    else:
        parent_elem = None
        for elt in decoded.iter():
            if elt.attrib["encoding_id"] == int(parent):
                parent_elem = elt
        if parent_elem is None:
            raise ValueError("No parent found")
        elem = xml.etree.ElementTree.Element(tag)
        elem.attrib = attribs
        if text:
            elem.text = text
        parent_elem.append(elem)

    return decoded, tags, attrib_keys, attrib_values, counter


def decode(path_in: str, path_out: str):
    """
    Decode encoded XML document

    Args:
        path_in (str): Path to file to decode
        path_out (str): Path to file to encode
    """

    counter = 0
    decoded = xml.etree.ElementTree.Element
    tags = []
    attrib_keys = []
    attrib_values = []
    namespaces = {}

    with open(path_in) as file_obj:
        data = file_obj.read()

    items = data.split(",")
    header = items[0].split("|")
    items = items[1:]

    for b64_n in header[0].split(":"):
        b64_n += "=" * (len(b64_n) % 4)
        base64_bytes = b64_n.encode("utf-8")
        n_bytes = base64.b64decode(base64_bytes)
        namespace = n_bytes.decode("utf-8")
        key, value = namespace.split("|")
        namespaces[key] = value

    for b64_t in header[1].split(":"):
        b64_t += "=" * (len(b64_t) % 4)
        base64_bytes = b64_t.encode("utf-8")
        t_bytes = base64.b64decode(base64_bytes)
        tag = t_bytes.decode("utf-8")
        tags.append(tag)

    for b64_k in header[2].split(":"):
        b64_k += "=" * (len(b64_k) % 4)
        base64_bytes = b64_k.encode("utf-8")
        k_bytes = base64.b64decode(base64_bytes)
        key = k_bytes.decode("utf-8")
        attrib_keys.append(key)

    for b64_v in header[3].split(":"):
        b64_v += "=" * (len(b64_v) % 4)
        base64_bytes = b64_v.encode("utf-8")
        v_bytes = base64.b64decode(base64_bytes)
        value = v_bytes.decode("utf-8")
        attrib_values.append(value)

    for item in items:
        decoded, tags, attrib_keys, attrib_values, counter = decode_elem(
            item,
            decoded,
            counter,
            tags=tags,
            attrib_keys=attrib_keys,
            attrib_values=attrib_values,
        )
    indent(decoded)

    for namespace in namespaces:
        decoded.attrib[f"xmlns:{namespaces[namespace]}"] = namespace

    decoded_tree = xml.etree.ElementTree.ElementTree(decoded)

    for elem in decoded_tree.iter():
        del elem.attrib["encoding_id"]
    with open(path_out, "wb") as file_obj:
        decoded_tree.write(file_obj)
    with open(path_out) as file_obj:
        data = file_obj.read()
    data = '<?xml version="1.0" encoding="UTF-8"?>\n' + data
    data = ascii_replace(data)
    match = re.search(r'xmlns:ns0="(\S*)"', data)
    if match:
        key = match.group(1)
        data = re.sub(r'xmlns:ns0="(\S*)"', "", data)
        data = re.sub(r"ns0:", namespaces[key] + ":", data)
    with open(path_out, "w") as file_obj:
        file_obj.write(data)


def main():
    """
    Parse arguments and execute encoder
    """

    if sys.argv[1] == "encode":
        if len(sys.argv) > 5:
            extension = sys.argv[5]
        else:
            extension = "exml"
        sizes = []
        if sys.argv[2] == "file":
            encode(sys.argv[3], sys.argv[4])
            start_size = os.path.getsize(sys.argv[3])
            end_size = os.path.getsize(sys.argv[4])
            if start_size == 0:
                percentage = "NA"
            else:
                percentage = "{:.2f}".format(end_size / start_size)
            sizes.append(
                (
                    sys.argv[3],
                    sys.argv[4],
                    str(start_size),
                    str(end_size),
                    percentage
                )
            )
        else:
            files = list(os.listdir(sys.argv[3]))
            for file_name in files:
                out_base = file_name[: file_name.rfind(".")]
                path_in = f"{sys.argv[3]}/{file_name}"
                path_out = f"{sys.argv[4]}/{out_base}.{extension}"
                encode(path_in, path_out)
                start_size = os.path.getsize(path_in)
                end_size = os.path.getsize(path_out)
                if start_size == 0:
                    percentage = "NA"
                else:
                    percentage = "{:.2f}".format(end_size / start_size)
                sizes.append(
                    (
                        path_in,
                        path_out,
                        str(start_size),
                        str(end_size),
                        percentage
                    )
                )
            total_start = 0
            total_end = 0
            for size in sizes:
                total_start += int(size[2])
                total_end += int(size[3])
            if total_start == 0:
                percentage = "NA"
            else:
                percentage = "{:.2f}".format(total_end / total_start)
            sizes.append(
                (
                    sys.argv[3],
                    sys.argv[4],
                    total_start,
                    total_end,
                    percentage
                )
            )
        print_table(["in", "out", "in_size", "out_size", "percentage"], sizes)
    elif sys.argv[1] == "decode":
        if len(sys.argv) > 5:
            extension = sys.argv[5]
        else:
            extension = "xml"
        sizes = []
        if sys.argv[2] == "file":
            decode(sys.argv[3], sys.argv[4])
            start_size = os.path.getsize(sys.argv[3])
            end_size = os.path.getsize(sys.argv[4])
            if start_size == 0:
                percentage = "NA"
            else:
                percentage = "{:.2f}".format(end_size / start_size)
            sizes.append(
                (
                    sys.argv[3],
                    sys.argv[4],
                    str(start_size),
                    str(end_size),
                    percentage
                )
            )
        else:
            files = list(os.listdir(sys.argv[3]))
            for file_name in files:
                out_base = file_name[: file_name.rfind(".")]
                path_in = f"{sys.argv[3]}/{file_name}"
                path_out = f"{sys.argv[4]}/{out_base}.{extension}"
                decode(path_in, path_out)
                start_size = os.path.getsize(path_in)
                end_size = os.path.getsize(path_out)
                if start_size == 0:
                    percentage = "NA"
                else:
                    percentage = "{:.2f}".format(end_size / start_size)
                sizes.append(
                    (
                        path_in,
                        path_out,
                        str(start_size),
                        str(end_size),
                        percentage
                    )
                )
            total_start = 0
            total_end = 0
            for size in sizes:
                total_start += int(size[2])
                total_end += int(size[3])
            if total_start == 0:
                percentage = "NA"
            else:
                percentage = "{:.2f}".format(total_end / total_start)
            sizes.append(
                (
                    sys.argv[3],
                    sys.argv[4],
                    str(total_start),
                    str(total_end),
                    percentage
                )
            )
        print_table(["in", "out", "in_size", "out_size", "percentage"], sizes)


if __name__ == "__main__":
    main()
