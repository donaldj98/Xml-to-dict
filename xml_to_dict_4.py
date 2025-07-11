import uuid
import re
import xml.etree.ElementTree as ET

class BluePrismToNowRPARelease():
    def __init__(self, file_path):
        self.tree = ET.parse(file_path)
        self.node_map = {
                        }
    

    def strip_namespace(self, tag):
        return re.sub(r'\{.*\}', '', tag)

    def xml_to_dict(self, element):
        node = {self.strip_namespace(k): v for k, v in element.attrib.items()}

        if element.text and element.text.strip():
            return {self.strip_namespace(element.tag): element.text.strip()}

        for child in element:
            tag_name = self.strip_namespace(child.tag)

            child_dict = self.xml_to_dict(child)
            if tag_name not in node:
                node[tag_name] = child_dict
            else:
                if not isinstance(node[tag_name], list):
                    node[tag_name] = [node[tag_name]]
                node[tag_name].append(child_dict)

        return node

    # def convert_types(self, child,xml_dict, key_count):
            
    #     key = child.attrib.get("name", "default")
    #     if key in xml_dict:
    #         if key in key_count:
    #             key_count[key] +=1
    #         else:
    #             key_count[key] = 1
    #         key = f"{key}_{key_count[key]}"
    #     else:
    #         key_count[key] = 0

    #     xml_dict[key] = self.xml_to_dict(child)


    def convert_types(self,child, xml_dict, key_count):
        if child.get("type") == "Action":
            s= child.iter("{http://www.blueprism.co.uk/product/process}resource")
            for i in s:
                key = i.get("action")

                if key in xml_dict:
                    if key in key_count:
                        key_count[key] +=1
                    else:
                        key_count[key] = 1
                    key = f"{key}_{key_count[key]}"
                else:
                    key_count[key] = 0

                xml_dict[key] = self.xml_to_dict(child)

        elif child.get("type") == "SubSheet":

            key = "SubSheet"

            if key in xml_dict:
                if key in key_count:
                    key_count[key] +=1
                else:
                    key_count[key] = 1
                key = f"{key}_{key_count[key]}"
            else:
                key_count[key] = 0

            xml_dict[key] = self.xml_to_dict(child)
            xml_dict[key]["in_arg_check"] = False
            xml_dict[key]["out_arg_check"] = False   
                
            if child.find("inputs") is not None or child.find("outputs") is not None:
                input = []
                output = []

                for i in child.iter("input"):
                    input.append({"Name" : i.get("name"),
                    "Value" : i.get("expr"),
                    "Type" : f"InArgument({i.get('type')})"})
                xml_dict[key]["in_arg"] = input

                for i in child.iter("output"):
                    output.append({"Name" : i.get("stage"),
                    "Type" : f"OutArgument({i.get('type')})"})
                xml_dict[key]["out_arg"] = output
                
                if len(xml_dict[key]["in_arg"]) > 0:
                    xml_dict[key]["in_arg_check"] = True
                if len(xml_dict[key]["out_arg"]) > 0:
                    xml_dict[key]["out_arg_check"] = True

        elif child.get("type") == "Data" or child.get("type") == "Collection" or child.get("type") == "Block":

            key = "Variables"

            if key in xml_dict:
                if key in key_count:
                    key_count[key] +=1
                else:
                    key_count[key] = 1
                key = f"{key}_{key_count[key]}"
            else:
                key_count[key] = 0

            xml_dict[key] = self.xml_to_dict(child)
        
        else:
        
            key = child.attrib.get("type", "default")

            if key in xml_dict:
                if key in key_count:
                    key_count[key] +=1
                else:
                    key_count[key] = 1
                key = f"{key}_{key_count[key]}"
            else:
                key_count[key] = 0

            xml_dict[key] = self.xml_to_dict(child)

    # Extracting the elements
    def get_all_elements(self):

        root = self.tree.getroot()
        first_object = root.find('.//{http://www.blueprism.co.uk/product/process}object')
        inner_process = first_object.find('.//{http://www.blueprism.co.uk/product/process}process')
        inner_appdef = inner_process.find('.//{http://www.blueprism.co.uk/product/process}appdef')
        main_element = inner_appdef.find('.//{http://www.blueprism.co.uk/product/process}element')

        xml_dict = {}
        key_count = {}    
        for element in main_element:
            if element.get("name") is not None:
                self.convert_types(element, xml_dict, key_count)
        return xml_dict

    def get_all_objects(self):

        root = self.tree.getroot()
        ob_dict = dict()
        counter = 0
        first_object = root.findall('.//{http://www.blueprism.co.uk/product/process}object')
        for process in first_object:
            inner_process = process.find('.//{http://www.blueprism.co.uk/product/process}process')
            name = process.get("name")
            xml_dict = {}
            key_count = {}
            for object in inner_process:
                self.convert_types(object, xml_dict, key_count)
            if name in ob_dict:
                counter+=1
                ob_dict[f"{name}{counter}"]
            else:
                ob_dict[name] = xml_dict
        return ob_dict   

    # get all object files and get only if it's published
    def get_object_sheets(self, ob_dict):
        obj_sheets = dict()
        for i, j in ob_dict.items():
            sheet = dict()
            for k, l in j.items(): 
                if l.get("type") == "Normal" and l.get("published") == "True":
                    sheet[l.get("subsheetid")] = l["name"]["name"]
            obj_sheets[i] = sheet 
        return obj_sheets
    
    def add_parent(self, node, parent_key):
        """
        This function adds parent stageid to node
        """
        if node.get('parent_key'):
                    node.get('parent_key', []).append(parent_key)
        else:
            node['parent_key'] = [parent_key]

    def add_child(self, node, child_key):
        """
        This function adds child stageid to node
        """
        child = node.get('child', [])
        if child:
            if not child_key in child:
                child.append(child_key)
        else:
            node['child'] = [child_key]


    # Structring Without Logs

    def structure_dict(self,input_data, node_map={}):

        skip_list = ["start", "end"] # Add the elements in lower case that need to be skipped
        output = {}
        visited = {}  # visited nodes

        def traverse(stage_id, parent_key=None, node_map={}, on_false=False):

            for key, node in input_data.items():
                if node.get("stageid") == stage_id:
                    # debug_info = f"Processing node with stageid: {stage_id}, key: {key}"
                    # print(debug_info)

                    self.add_parent(node=node, parent_key=parent_key)

                    # If the node was visited before, add a node_map entry
                    if key in visited and node.get("type").lower() not in skip_list :
                        node.get("node_map", {}).get(
                            "p_c_out_port_id", []
                        ).append(node_map.get("c_out_port_id"))
                        node.get("node_map", {}).get(
                            "p_c_comp_id", []
                        ).append(node_map.get("c_comp_id"))

                        return  # Stop further processing for this path

                    # Mark this node as visited
                    visited[key] = parent_key
                    output[key] = node  # Add node to output dictionary

                    condition_id = node_map.get("c_out_condition_id")
                    node_map = {
                        "p_c_comp_id": [node_map.get("c_comp_id")],
                        "p_c_out_port_id": [node_map.get("c_out_port_id")],
                        "c_comp_id": str(uuid.uuid4()),
                        "c_in_port_id": str(uuid.uuid4()),
                        "c_out_port_id": str(uuid.uuid4()),
                    }

                    # Process onsuccess (handle nested dictionary or direct string)
                    if node.get("type", "").lower() in skip_list:
                        return
                    
                    # Check if current node is on onsuccess node
                    if "onsuccess" in node:
                        if isinstance(node["onsuccess"], dict):
                            next_stage_id = node["onsuccess"]["onsuccess"]
                        else:
                            next_stage_id = node["onsuccess"]

                        # If onflase flag is set map p_c_out_port_id to condition_id                        
                        if on_false:
                            node_map.update(
                                { "p_c_out_port_id": [condition_id],}
                            )
                        node.update({"node_map": node_map})
                        self.add_child(node=node, child_key=key)
                        traverse(next_stage_id, key, node_map=node_map)

                    # if node contains ontrue and onfalse then add c_out_condition_id to map
                    if "ontrue" in node and "onfalse" in node or "choices" in node:
                        node_map.update(
                            {"c_out_condition_id": str(uuid.uuid4())}
                        )

                    if "choices" in node:
                        choices = node.get("choices")
                        if isinstance(choices, list):
                            for choice in choices:
                                choice = node.get("choice")
                                if choice and 'ontrue' in choice:
                                    if isinstance(node["ontrue"], dict):
                                        next_stage_id = node["ontrue"]["ontrue"]
                                    else:
                                        next_stage_id = node["ontrue"]
                                    node.update({"node_map": node_map})
                                    self.add_child(node=node, child_key=key)
                                    traverse(next_stage_id, key, node_map=node_map)

                        if isinstance(choices, dict):
                            choice = node.get("choice")
                            if choice and 'ontrue' in choice:
                                if isinstance(node["ontrue"], dict):
                                    next_stage_id = node["ontrue"]["ontrue"]
                                else:
                                    next_stage_id = node["ontrue"]
                                node.update({"node_map": node_map})
                                self.add_child(node=node, child_key=key)
                                traverse(next_stage_id, key, node_map=node_map)

                    # check if current node is ontrue node
                    if "ontrue" in node:
                        if isinstance(node["ontrue"], dict):
                            next_stage_id = node["ontrue"]["ontrue"]
                        else:
                            next_stage_id = node["ontrue"]

                        node.update({"node_map": node_map})
                        self.add_child(node=node, child_key=key)
                        traverse(next_stage_id, key, node_map=node_map)

                    # check if current node is a onflase node
                    if "onfalse" in node:
                        if isinstance(node["onfalse"], dict):
                            next_stage_id = node["onfalse"]["onfalse"]
                        else:
                            next_stage_id = node["onfalse"]

                        node.update({"node_map": node_map})
                        self.add_child(node=node, child_key=key) 
                        traverse(next_stage_id, key, node_map=node_map, on_false=True)

                    break

        # Start node
        for key, node in input_data.items():
            if node.get("type") == "Start":
                start_stage_id = node.get("onsuccess", {}).get("onsuccess", node.get("onsuccess"))
                output[key] = node

                node_map = {
                    "p_c_comp_id": [node_map.get("c_comp_id")],
                    "p_c_out_port_id": [node_map.get("c_out_port_id")],
                    "c_comp_id": str(uuid.uuid4()),
                    "c_in_port_id": str(uuid.uuid4()),
                    "c_out_port_id": str(uuid.uuid4())}
                node.update({"node_map": node_map})

                # print(f"Starting traversal from Start node: {key}, stageid: {start_stage_id}")
                traverse(start_stage_id, key)
                break
        return output
    

    def structure_dict_object(self,input_data, node_map={}):

        skip_list = ["start", "end"] # Add the elements in lower case that need to be skipped
        output = {}
        visited = {}  # visited nodes
        loop_counter = 1

        def traverse(stage_id, parent_key=None, node_map={}, on_false=False):

            nonlocal loop_counter
            loop_id = loop_counter
            loop_counter += 1

            for key, node in input_data.items():
                if node.get("stageid") == stage_id:
                    # debug_info = f"Processing node with stageid: {stage_id}, key: {key}"
                    # print(debug_info)

                    # If the node was visited before, add a node_map entry
                    if key in visited and node.get("type").lower() not in skip_list :
                        node.get("node_map", {}).get(
                            "p_c_out_port_id"
                        ).append(node_map.get("c_out_port_id"))
                        node.get("node_map", {}).get(
                            "p_c_comp_id"
                        ).append(node_map.get("c_comp_id"))

                        return  # Stop further processing for this path

                    # Mark this node as visited
                    visited[key] = parent_key
                    output[key] = node  # Add node to output dictionary

                    condition_id = node_map.get("c_out_condition_id")
                    node_map = {
                        "p_c_comp_id": [node_map.get("c_comp_id")],
                        "p_c_out_port_id": [node_map.get("c_out_port_id")],
                        "c_comp_id": str(uuid.uuid4()),
                        "c_in_port_id": str(uuid.uuid4()),
                        "c_out_port_id": str(uuid.uuid4()),
                    }

                    # Process onsuccess (handle nested dictionary or direct string)
                    if node.get("type", "").lower() in skip_list:
                        return
                    
                    if "onsuccess" in node:
                        if isinstance(node["onsuccess"], dict):
                            next_stage_id = node["onsuccess"]["onsuccess"]
                        else:
                            next_stage_id = node["onsuccess"]
                        # print(f"Following onsuccess path to stageid: {next_stage_id}")

                        traverse(next_stage_id, key, node_map=node_map)

                    if "choices" in node:
                        node_map.update(
                            {"c_out_condition_id": str(uuid.uuid4())}
                        )                        
                    
                    if "choices" in node:
                        if isinstance(node["choices"]["choice"]["ontrue"], dict):
                            next_stage_id = node["choices"]["choice"]["ontrue"]["ontrue"]
                        else:
                            next_stage_id = node["ontrue"]

                        node.update({"node_map": node_map})
                        # print(f"Following ontrue path to stageid: {next_stage_id}")
                        traverse(next_stage_id, key, node_map=node_map)

                    break  

        # Start node
        for key, node in input_data.items():
            if node.get("type") == "Start":
                start_stage_id = node.get("onsuccess", {}).get("onsuccess", node.get("onsuccess"))
                output[key] = node

                node_map = {
                    "p_c_comp_id": [node_map.get("c_comp_id")],
                    "p_c_out_port_id": [node_map.get("c_out_port_id")],
                    "c_comp_id": str(uuid.uuid4()),
                    "c_in_port_id": str(uuid.uuid4()),
                    "c_out_port_id": str(uuid.uuid4())}
                node.update({"node_map": node_map})

                # print(f"Starting traversal from Start node: {key}, stageid: {start_stage_id}")
                traverse(start_stage_id, key)
                break
        return output


    # Structuring the Object files and adding the elements into it if it's called

    # structures the object dict
    def structure_object(self, ob_dict):
        Object_collection = dict()
        tem_di = {}
        for obj_name, obj_val  in self.get_object_sheets(ob_dict).items():
            for sub_obj_id, sub_obj_name in obj_val.items():
                for i, j in ob_dict.items():
                    for k, l in j.items():
                        if isinstance(l.get("subsheetid"), dict) and "subsheetid" in l["subsheetid"] and l["subsheetid"]["subsheetid"] == sub_obj_id:
                            tem_di[k] = l
                Object_collection[f"{obj_name}({sub_obj_name})"] = self.structure_dict_object(tem_di, self.node_map)
                tem_di = {}
        return Object_collection

    # returns the objects element

    def get_object_element(self,ob_dict_items, ele_id):
        for i,j in ob_dict_items.items():
            # for k,l in j.items():
                # print(j)
                if isinstance(j.get('id'), dict) and j["id"]["id"] == ele_id:
                    # print(j['id']["id"])
                    return {i:j}
        return None
                
    # Appends in the element dict where it is called
    # def element_called_within_object(self, Object_collection):
    #     for i, j in Object_collection.items():
    #         # print(i)
    #         for k,l in j.items():
    #             # if l.get("step"):
    #             if "step" in l:
    #                 print(l["step"]["element"]["id"])
    #                 l["ele_file"] = self.get_object_element(self.get_all_elements(), l["step"]["element"]["id"])
    #     return Object_collection

    def element_called_within_object(self, Object_collection):
        for i, j in Object_collection.items():
            # print(i)
            for k,l in j.items():
                # if l.get("step"):
                ele = ""
                if "step" in l:
                    # print("step")
                    try:
                        # print(l["step"]["element"]["id"])
                        ele = l["step"]["element"]["id"]
                    except : 
                        # print(l["step"][0]["element"]["id"])
                        ele = l["step"][0]["element"]["id"]

                elif "choices" in l:
                    # print("choice")
                    # print(l["choices"]["choice"]["element"]["id"]) 
                    ele = l["choices"]["choice"]["element"]["id"]
                if ele != "":
                    l["ele_file"] = self.get_object_element(self.get_all_elements(), ele)
        return Object_collection   

    # print(element_called_within_object(structure_object(get_all_objects(tree))))

    # Process from BP release file

    def process_file(self):

        root = self.tree.getroot()

        first_process = root.find('.//{http://www.blueprism.co.uk/product/process}process')
        second_processes = first_process.findall('.//{http://www.blueprism.co.uk/product/process}process')

        for process in second_processes:
            tree = ET.ElementTree(process)
            root = tree.getroot()

        def strip_namespace(tag):
            return re.sub(r'\{.*\}', '', tag)

        def parse_inputs_or_outputs(element, key_attr, value_attr):
            return {item.get(key_attr) : item.get(value_attr) for item in element}

        # def xml_to_dict(element):
        #     node = {strip_namespace(k): v for k, v in element.attrib.items()}

        #     if element.text and element.text.strip():
        #         return {strip_namespace(element.tag): element.text.strip()}

        #     for child in element:
        #         tag_name = strip_namespace(child.tag)

        #         # Check for "inputs" and "outputs" processing based on stage type and child tag
        #         if tag_name == "inputs" and element.get("type") == "Action":
        #             node[tag_name] = parse_inputs_or_outputs(child, "name", "expr")
        #         elif tag_name == "outputs" and element.get("type") == "Action":
        #             node[tag_name] = parse_inputs_or_outputs(child, "name", "stage")
        #         else:
        #             child_dict = xml_to_dict(child)
        #             if tag_name not in node:
        #                 node[tag_name] = child_dict
        #             else:
        #                 if not isinstance(node[tag_name], list):
        #                     node[tag_name] = [node[tag_name]]
        #                 node[tag_name].append(child_dict)

        #     return node

        def get_all_sheets():
            sheets = []
            for child in root:
                if child.get("type") == "Normal":
                    sheets.append(child.get("subsheetid"))
            return sheets

        def get_subsheet_name(sheet):
            for child in root:
                if child.find("{http://www.blueprism.co.uk/product/process}subsheetid") is not None and child.find("{http://www.blueprism.co.uk/product/process}subsheetid").text == sheet:
                    if child.get("type") == "SubSheetInfo":
                        sub_name = child.get("name")
            return sub_name

        def find_all_calcu_nodes(xml_dict):
            data_nodes = []
            for node_key, node_value in xml_dict.items():
                if node_value.get("type") == "Data" or node_value.get("type") == "Collection" or node_value.get("type") == "Block" or node_key[0:8] == "Argument":
                    data_nodes.append((node_key, node_value))
            return data_nodes

        def insert_all_calc_nodes(struct_dict, xml_dict):
            structured_dict = list(struct_dict.items())
            calc_dict = list(find_all_calcu_nodes(xml_dict))
            structured_dict[1:1] = calc_dict
            return dict(structured_dict)

        def start_page():
            xml_dict = {}
            key_count = {}
            for child in root:
                if child.find("{http://www.blueprism.co.uk/product/process}subsheetid") is None:
                    self.convert_types(child, xml_dict, key_count)
            return insert_all_calc_nodes(self.structure_dict(xml_dict, self.node_map), xml_dict)

        def structured_sheet_collection_for_process():
            Sheet_collections = {}
            if start_page() != {}:
                Sheet_collections["start_page"] = start_page()
            else:
                print("Process file has not been attached... Kindly attach and try again...!")
            for sheet in get_all_sheets():
                xml_dict = {}
                key_count = {}
                for child in root:
                    
                    if child.find("{http://www.blueprism.co.uk/product/process}subsheetid") is not None and child.find("{http://www.blueprism.co.uk/product/process}subsheetid").text == sheet:
                        self.convert_types(child, xml_dict, key_count)
                
                Sheet_collections[get_subsheet_name(sheet) + "_" + sheet] = insert_all_calc_nodes(self.structure_dict(xml_dict, self.node_map), xml_dict)
            return Sheet_collections
        return structured_sheet_collection_for_process()

    # res = process_file()

	
# bpr = BluePrismToNowRPARelease(r"C:\Users\donald.j\Downloads\UIActions.bprelease")
# bpr = BluePrismToNowRPARelease(r"C:\Users\donald.j\Downloads\BluePrism Files\Testfile.bprelease")
# bpr = BluePrismToNowRPARelease(r"C:\Users\donald.j\Downloads\Release03_12_2024.bprelease")
# bpr = BluePrismToNowRPARelease(r"C:\Users\donald.j\Downloads\ExistingRelease.bprelease")

bpr = BluePrismToNowRPARelease(r"C:\Users\donald.j\Downloads\ACME Login.bprelease")



#### For Process File

print("\nProcess_file\n")
for i,j in bpr.process_file().items():   
    print(f"\n{i}")
    for k,l in j.items():
        print(k,l)

#### For Object File
print("\nObject_file\n")
if bpr.element_called_within_object(bpr.structure_object(bpr.get_all_objects())) != {}:
    for i,j in bpr.element_called_within_object(bpr.structure_object(bpr.get_all_objects())).items():
        print(i)
        for k,l in j.items():
            print(k,l)
else:
    print("Object file has not been attached... Kindly attach and try again...!")
# object_elements = BluePrismToNowRPARelease.get_all_elements()

# object_struct =  bpr.structure_object(bpr.get_all_objects())
# for i,j in bpr.structure_object(bpr.get_all_objects()).items():
#     print(i)
#     for k,l in j.items():
#         print(k,l)
