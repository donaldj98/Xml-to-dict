import xml.etree.ElementTree as ET

def xml_to_dict(element):
    node = {k:v for k,v in element.attrib.items()}

    if element.text and element.text.strip():
        return {element.tag : element.text.strip()}

    for child in element:
        child_dict = xml_to_dict(child)
    
        if child.tag not in node:
            node[child.tag] = child_dict
        else:
            if not isinstance(node[child.tag], list):
                node[child.tag] = [node[child.tag]]
            node[child.tag].append(child_dict)

    return node 

tree =  ET.parse(r"C:\Users\donald.j\Downloads\data (11).xml")
root = tree.getroot()
xml_dict = xml_to_dict(root)

xml_dict = {}
key_count = {}

for child in root:
    key = child.attrib.get("name", "default")

    if key in xml_dict:
        if key in key_count:
            key_count[key] +=1
        else:
            key_count[key] = 1
        key = f"{key}_{key_count[key]}"
    else:
        key_count[key] = 0

    xml_dict[key] = xml_to_dict(child)


# print(xml_dict)
for i,j in xml_dict.items():
    # print(f"{i} : {j}")
    for k,l in j.items():
        print(f"{k} : {l}")

