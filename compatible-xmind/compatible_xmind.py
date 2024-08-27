import json
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def read_xmind(file_path: str) -> None:
    try:
        # 尝试读取json文件
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'content.json' in zip_ref.namelist():
                content = zip_ref.read('content.json')
                json_data = json.loads(content.decode('utf-8'))
                result = process_json(json_data)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return
    except Exception as e:
        print("Error reading JSON file:", e)

    # 如果没有json文件，则尝试读取xml文件
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            if 'content.xml' in zip_ref.namelist():
                content = zip_ref.read('content.xml')
                root = ET.fromstring(content)
                result = process_xml(root)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return
    except Exception as e:
        print("Error reading XML file:", e)

    print("No valid content found in the XMind file.")


def process_json(json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sheets = []
    for item in json_data:
        sheet_title = item.get("title", "Untitled Sheet")
        root_topic = item.get("rootTopic", {})
        sheets.append({
            "title": sheet_title,
            "rootTopic": process_topic(root_topic)
        })
    return sheets


def process_xml(root: ET.Element) -> List[Dict[str, Any]]:
    ns = {'xmind': 'urn:xmind:xmap:xmlns:content:2.0'}
    sheets = []
    for sheet_elem in root.findall('.//xmind:sheet', ns):
        sheet_title = sheet_elem.get('title', 'Untitled Sheet')
        root_topic_elem = sheet_elem.find('.//xmind:topic', ns)
        if root_topic_elem is not None:
            sheets.append({
                "title": sheet_title,
                "rootTopic": process_topic_xml(root_topic_elem)
            })
    return sheets


def process_topic(topic: Dict[str, Any], indent: int = 0) -> Dict[str, Any]:
    title = topic.get("title", "")
    children = []
    if "children" in topic:
        for child in topic["children"].get("attached", []):
            children.append(process_topic(child, indent + 1))
    return {
        "title": title,
        "children": children
    }


def process_topic_xml(topic_elem: ET.Element, indent: int = 0) -> Dict[str, Any]:
    ns = {'xmind': 'urn:xmind:xmap:xmlns:content:2.0'}
    title_elem = topic_elem.find('xmind:title', ns)
    title = title_elem.text if title_elem is not None else ""
    children = []
    for child_elem in topic_elem.findall('xmind:children/xmind:topics/xmind:topic', ns):
        children.append(process_topic_xml(child_elem, indent + 1))
    return {
        "title": title,
        "children": children
    }


if __name__ == "__main__":
    file_path = "软件设计师上午.xmind"
    read_xmind(file_path)