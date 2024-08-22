#Straight flow

import xml.etree.ElementTree as ET
import pandas as pd

tree = ET.parse(r"C:\Users\donald.j\Downloads\straight flow.xml")
root = tree.getroot()

stages = root.findall("stage")

extract_dict = {}
for stage in stages:
    type = stage.get("type")
    print(type)
    print(f"id : {stage.get("stageid")}")
    print(f"subsheet id : {stage.find("subsheetid").text}")
    if stage.find("ontrue") is not None:
        print(f"ontrue : {stage.find("ontrue").text}")
        print(f"onfalse : {stage.find("onfalse").text}")

    if stage.find("onsuccess") is not None:
        print(f"onsuccess : {stage.find("onsuccess").text}")
    
    new_dict = {stage.get("stageid") : {"type" : type,
                                        "subsheet id" : stage.find("subsheetid").text}}
                
    if stage.find("onsuccess") is not None:
        new_dict[stage.get("stageid")].update({"onsuccess" : stage.find("onsuccess").text})
    if stage.find("ontrue") is not None:
        new_dict[stage.get("stageid")].update({"ontrue" : stage.find("ontrue").text})
        new_dict[stage.get("stageid")].update({"onfalse" : stage.find("onfalse").text})

    extract_dict.update(new_dict)
for i in extract_dict.items():
    print(i)

# print(dict)

# onsuccess >> subsheet id
# ontrue >> subsheet id and onfalse >> subsheet id

print("second")

order_dict = {}
num = 0
sheet_id = ""
onsuccess = ""


for i,j in extract_dict.items():
    print(i,j)
    
    if j["type"] == "Start":
        order_dict[num] = {i:j}
        num+=1
        sheet_id = j["subsheet id"]
        onsuccess = j["onsuccess"]
        print(num, sheet_id)
        
        

    if j["type"] == "End":
        order_dict[len(extract_dict)-1] = {i:j}
        end_id = j["subsheet id"]
        print(len(extract_dict), sheet_id)
    
# removing the start and end from main dict
for i,j in order_dict.items():
    print(extract_dict.pop(list(j.keys())[0]))

print("od")
for i in order_dict.items():
    print(i)

print("main_dict")
for i,j in extract_dict.items():
    print(i,j)


## checking all the elements from the extract_dict and appending in order_dict in a sequence
while extract_dict:
    for id,elements in extract_dict.items():
        print(id,elements)
        if id == onsuccess:
            items = list(order_dict.items()) 

            items.insert(num , (num ,{id:elements}))
            print(items)
            order_dict = dict(items)

            num+=1
            if "onsuccess" in elements:
                onsuccess = elements["onsuccess"]
                print(f"onsuccess : {num}, {sheet_id}")
                print(extract_dict.pop(id))
                
                break

print("dict")
for i in extract_dict.items():
    print(i)

print("ordered_dict")
for i,j in order_dict.items():
    print(i,j)


    
