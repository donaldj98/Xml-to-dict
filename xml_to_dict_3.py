import uuid
import xml.etree.ElementTree as ET

class BluePrismToNowRPA():
    def __init__(self, file_path):
        tree = ET.parse(file_path)
        self.root = tree.getroot()
        self.arg_count = 0
        self.node_map = {
                            "c_comp_id": "1",
                            "c_out_port_id": "1p"
                        }

    def xml_to_dict(self, element):

        node = {k:v for k,v in element.attrib.items()}

        if element.text and element.text.strip():
            return {element.tag : element.text.strip()}

        for child in element:
            tag_name = child.tag

            child_dict = self.xml_to_dict(child)
            if tag_name not in node:
                node[tag_name] = child_dict
            else:
                if not isinstance(node[tag_name], list):
                    node[tag_name] = [node[tag_name]]
                node[tag_name].append(child_dict)

        return node

    # def parse_inputs_or_outputs(self, element, key_attr, value_attr):
    #     return {item.get(key_attr) : item.get(value_attr) for item in element}

    # def xml_to_dict(self, element):
    #     node = {k:v for k,v in element.attrib.items()}

    #     if element.text and element.text.strip():
    #         return {element.tag : element.text.strip()}

    #     for child in element:
    #         tag_name = child.tag
    #         if tag_name == "inputs" and element.get("type") == "Action":
    #             node[tag_name] = self.parse_inputs_or_outputs(child, "name", "expr")
    #         elif tag_name == "outputs" and element.get("type") == "Action":
    #             node[tag_name] = self.parse_inputs_or_outputs(child, "name", "stage")
    #         else:

    #             child_dict = self.xml_to_dict(child)
            
    #             if child.tag not in node:
    #                 node[child.tag] = child_dict
    #             else:
    #                 if not isinstance(node[child.tag], list):
    #                     node[child.tag] = [node[child.tag]]
    #                 node[child.tag].append(child_dict)

    #     return node

    # To get all the different sheets
    def get_all_sheets(self):
        sheets = []
        for child in self.root:
            if child.get("type") == "Normal":
                sheets.append(child.get("subsheetid"))
        return sheets

    def convert_types(self, child, xml_dict, key_count, arg_count):
        if child.get("type") == "Action":
            s= child.iter("resource")
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
            temp_dict = {
                'in_arg': {},
                'out_arg': {},
                'in_arg_check': False,
                'out_arg_check': False
            }
            if key in xml_dict:
                if key in key_count:
                    key_count[key] +=1
                else:
                    key_count[key] = 1
                key = f"{key}_{key_count[key]}"
            else:
                key_count[key] = 0

            xml_dict[key] = self.xml_to_dict(child)

            pro_id  = child.find("processid").text
            for in_child  in self.root:
                if in_child.get("type")=="Normal" and in_child.get("subsheetid") == pro_id:
                    xml_dict[key]["name"] = in_child.find("name").text
            
                
            if child.find("inputs") is not None or child.find("outputs") is not None:
                input = []
                output = []
                xml_dict[key]["arguments"] = {}

                for i in child.iter("input"):
                    var_name = i.get("name")                    
                    temp_dict["in_arg"][var_name] = {"Name" : var_name, "Value" : i.get("expr"), "Type" : f"InArgument({i.get('type')})"}
                

                for i in child.iter("output"):
                    var_name = i.get("stage").replace("[","").replace("]","")
                    temp_dict["out_arg"][var_name] = {"Name" : var_name, "Value" : i.get("stage"), "Type" : f"OutArgument({i.get('type')})"}
                
                if len(temp_dict["in_arg"]) > 0:
                    temp_dict["in_arg_check"] = True
                if len(temp_dict["out_arg"]) > 0:
                    temp_dict["out_arg_check"] = True

                xml_dict[key]["arguments"].update(temp_dict)
            else:
                xml_dict[key]["arguments"] = temp_dict

        # elif child.get("type") == "Data" or child.get("type") == "Collection" or child.get("type") == "Block":
        elif child.get("type") == "Data" or child.get("type") == "Collection":

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

            # if child.get("type") == "Start": 
                
            #     if child.find("inputs") is not None:
            #         arg_count+=1
            #         di_cou = 0
            #         start_args = dict()
            #         for i in child.iter("input"):
            #             di_cou+=1
            #             start_args[f"input{di_cou}"] = {"Name" : i.get("stage"),
            #                         "Type" : f"InArgument({i.get('type')})"}
            #         xml_dict[f"Argument{arg_count}"] = dict(start_args)        

            # if child.get("type") == "End":
            #     if child.get("type") == "End":
            #         if child.find("outputs") is not None:
            #             arg_count+=1
            #             di_cou = 0
            #             end_args = dict()
            #             for i in child.iter("output"):
            #                 di_cou += 1
            #                 end_args[f"output{di_cou}"] = {"Name" : i.get("stage"),
            #                             "Type" : f"OutArgument({i.get('type')})"}
            #             xml_dict[f"Argument{arg_count}"] = end_args
            if child.get("type") == "Start": 
                if child.find("inputs") is not None:
                    for i in child.iter("input"):
                        self.arg_count+=1
                        xml_dict[f"Arguments{self.arg_count}"] = {"Name": i.get("name"), "Value" : i.get("stage"), "Type" : f"InArgument({i.get('type')})"}   

            if child.get("type") == "End":
                if child.find("outputs") is not None:
                    for i in child.iter("output"):
                        self.arg_count+=1
                        xml_dict[f"Arguments{self.arg_count}"] =  {"Name": i.get("name"), "Value" : i.get("stage"), "Type" : f"OutArgument({i.get('type')})"}


    # Structring Without Logs

    # def structure_dict_Choice(self,start_id, input_data):
    #     output = {}
    #     visited = {}  # visited nodes
    #     loop_counter = 1

    #     def traverse(stage_id, parent_key=None):

    #         nonlocal loop_counter
    #         loop_id = loop_counter
    #         loop_counter += 1

    #         for key, node in input_data.items():
    #             if node.get("stageid") == stage_id:
    #                 # debug_info = f"Processing node with stageid: {stage_id}, key: {key}"
    #                 # print(debug_info)


    #                 # Mark this node as visited
    #                 visited[key] = parent_key
    #                 output[key] = node  # Add node to output dictionary
                    
    #                 if "onsuccess" in node:
    #                     if isinstance(node["onsuccess"], dict):
    #                         next_stage_id = node["onsuccess"]["onsuccess"]
    #                     else:
    #                         next_stage_id = node["onsuccess"]
    #                     # print(f"Following onsuccess path to stageid: {next_stage_id}")

    #                     traverse(next_stage_id, key)

                   
                    
    #                 if "ontrue" in node:
    #                     if isinstance(node["ontrue"], dict):
    #                         next_stage_id = node["ontrue"]["ontrue"]
    #                     else:
    #                         next_stage_id = node["ontrue"]

    #                     # print(f"Following ontrue path to stageid: {next_stage_id}")
    #                     traverse(next_stage_id, key)

    #                 if "onfalse" in node:
    #                     if isinstance(node["onfalse"], dict):
    #                         next_stage_id = node["onfalse"]["onfalse"]
    #                     else:
    #                         next_stage_id = node["onfalse"]

    #                     # print(f"Following onfalse path to stageid: {next_stage_id}")

    #                     traverse(next_stage_id, key)
                        
    #                 break  

    #     traverse(start_id)
    #     return output


    
    def structure_dict(self,input_data, node_map={}):

        skip_list = ["start"] # Add the elements in lower case that need to be skipped
        output = {}
        visited = {}  # visited nodes
        loop_counter = 1

        def traverse(stage_id, parent_key=None, node_map={}, on_false=False, choices=False):

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
                    choices_port_id = node_map.get("choices_port_id",[])[-1] if choices and node_map.get("choices_port_id",[]) else None
                    node_map = {
                        "p_c_comp_id": [node_map.get("c_comp_id")],
                        "p_c_out_port_id": [node_map.get("c_out_port_id")],
                        "c_comp_id": str(uuid.uuid4()),
                        "c_in_port_id": str(uuid.uuid4()),
                        "c_out_port_id": str(uuid.uuid4()),
                    }
                    if node["type"] == "End":
                        node.update({"node_map": node_map})
                        return
                    if choices:
                        node_map["p_c_out_port_id"] = [choices_port_id]
                    # Process onsuccess (handle nested dictionary or direct string)
                    if node.get("type", "").lower() in skip_list:
                        return
                    
                    if on_false:
                        node_map.update(
                            { "p_c_out_port_id": [condition_id],}
                        )
                    
                    if "onsuccess" in node:
                        if isinstance(node["onsuccess"], dict):
                            next_stage_id = node["onsuccess"]["onsuccess"]
                        else:
                            next_stage_id = node["onsuccess"]
                        # print(f"Following onsuccess path to stageid: {next_stage_id}")

                        # if on_false:
                        #     node_map.update(
                        #         { "p_c_out_port_id": [condition_id],}
                        #     )
                        node.update({"node_map": node_map})

                        traverse(next_stage_id, key, node_map=node_map)

                    if "ontrue" in node and "onfalse" in node:
                        node_map.update(
                            {"c_out_condition_id": str(uuid.uuid4())}
                        )                        
                    
                    if "ontrue" in node:
                        if isinstance(node["ontrue"], dict):
                            next_stage_id = node["ontrue"]["ontrue"]
                        else:
                            next_stage_id = node["ontrue"]

                        node.update({"node_map": node_map})
                        # print(f"Following ontrue path to stageid: {next_stage_id}")
                        traverse(next_stage_id, key, node_map=node_map)

                    if "onfalse" in node:
                        if isinstance(node["onfalse"], dict):
                            next_stage_id = node["onfalse"]["onfalse"]
                        else:
                            next_stage_id = node["onfalse"]

                        node.update({"node_map": node_map})   
                        # print(f"Following onfalse path to stageid: {next_stage_id}")

                        traverse(next_stage_id, key, node_map=node_map, on_false=True)
                    
                    if node["type"] == "ChoiceStart": 
                        node_map.update(
                            {"choices_port_id": list()}
                        )
                        for choice in node["choices"]["choice"]:
                            node_map["choices_port_id"].append(str(uuid.uuid4()))
                            traverse(choice["ontrue"]["ontrue"], key, node_map=node_map, choices=True)
                            # output.update(self.structure_dict_Choice(choice["ontrue"]["ontrue"],input_data))
                            
                        for i,j in input_data.items():
                            if "type" in j and j["type"] == "ChoiceEnd":
                                next_stage_id = j["stageid"]

                        
                        node.update({"node_map": node_map})   

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

    def find_all_calcu_nodes(self,xml_dict):
        data_nodes = []
        for node_key, node_value in xml_dict.items():
            # if node_value.get("type") == "Data" or node_value.get("type") == "Collection" or node_value.get("type") == "Block" or node_key[0:8] == "Argument":
            if node_value.get("type") == "Data" or node_value.get("type") == "Collection" or node_key[0:9] == "Arguments":
                data_nodes.append((node_key, node_value))
        return data_nodes

    def insert_all_calc_nodes(self, struct_dict, xml_dict):
        structured_dict = list(struct_dict.items())
        calc_dict = list(self.find_all_calcu_nodes(xml_dict))
        structured_dict[1:1] = calc_dict
        return dict(structured_dict)

    def start_page(self):
        xml_dict = {}
        key_count = {}
        arg_count = 0
        for child in self.root:
            if child.find("subsheetid") is None:
                self.convert_types(child, xml_dict, key_count,arg_count)
        return self.insert_all_calc_nodes(self.structure_dict(xml_dict, self.node_map), xml_dict)
    
    # def get_all_items_without_conversion(self):
    #     xml_dict = {}
    #     key_count = {}
    #     arg_count = 0
    #     for child in self.root:
    #         if child.find("subsheetid") is None:
    #             self.convert_types(child, xml_dict, key_count,arg_count)
    #     return xml_dict

    def get_subsheet_name(self, sheet):
        for child in self.root:
            if child.find("subsheetid") is not None and child.find("subsheetid").text == sheet:
                if child.get("type") == "SubSheetInfo":
                    sub_name = child.get("name")
        return sub_name 

    def structured_sheet_collection_for_process(self):
        source_data=[]
        Sheet_collections = {}
        Sheet_collections["start_page"] = self.start_page()
        for sheet in self.get_all_sheets():
            xml_dict = {}
            key_count = {}
            arg_count = 0
            for child in self.root:
                if child.find("subsheetid") is not None and child.find("subsheetid").text == sheet:
                    self.convert_types(child, xml_dict, key_count, arg_count)
            
            Sheet_collections[self.get_subsheet_name(sheet) + "_" + sheet] = self.insert_all_calc_nodes(self.structure_dict(xml_dict, self.node_map), xml_dict)
        return Sheet_collections
    
bp = BluePrismToNowRPA(r"C:\Users\donald.j\Downloads\BPA Process - ChoiceStage.bpprocess")

for i, j in bp.structured_sheet_collection_for_process().items():
    print(i)
    for k,l in j.items():
        print(k,l)

# import json
# json_data = json.dumps(bp.structured_sheet_collection_for_process())
# with open(r"C:\Users\donald.j\Downloads\choice.json", 'w') as json_file:
#     json.dump(json_data, json_file, indent=4)


# for i, j in bp.get_all_items_without_conversion().items():
#     print(i,j)
#     # for k,l in j.items():
#     #     print(k,l)

