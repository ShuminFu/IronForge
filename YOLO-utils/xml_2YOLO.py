import os
import shutil
import xml.etree.ElementTree as ET
import random
import uuid

def create_directory_structure(base_path):
    for folder in ['train', 'valid', 'test']:
        for subfolder in ['images', 'labels']:
            os.makedirs(os.path.join(base_path, folder, subfolder), exist_ok=True)

def convert_bbox(size, box):
    dw = 1.0 / size[0]
    dh = 1.0 / size[1]
    x = (box[0] + box[2]) / 2.0
    y = (box[1] + box[3]) / 2.0
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return (x, y, w, h)

def convert_annotation(xml_path, output_path, class_mapping):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    with open(output_path, 'w') as out_file:
        for obj in root.iter('object'):
            cls = obj.find('name').text
            if cls not in class_mapping:
                continue
            cls_id = class_mapping[cls]
            xmlbox = obj.find('bndbox')
            b = (float(xmlbox.find('xmin').text), float(xmlbox.find('ymin').text),
                 float(xmlbox.find('xmax').text), float(xmlbox.find('ymax').text))
            bb = convert_bbox((w, h), b)
            out_file.write(f"{cls_id} {' '.join([str(a) for a in bb])}\n")

def find_image_xml_pairs(root_dir):
    image_xml_pairs = []
    for root, dirs, files in os.walk(root_dir):
        if 'images' in root:
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(root, file)
                    # 构造对应的XML路径
                    xml_dir = root.replace('images', 'annotations/xmls')
                    xml_path = os.path.join(xml_dir, os.path.splitext(file)[0] + '.xml')
                    if os.path.exists(xml_path):
                        image_xml_pairs.append((image_path, xml_path))
    return image_xml_pairs

def process_dataset(source_path, dest_path, class_mapping):
    create_directory_structure(dest_path)
    image_xml_pairs = find_image_xml_pairs(source_path)

    for img_path, xml_path in image_xml_pairs:
        # Determine destination folder (70% train, 30% valid, 0% test)
        if random.random() < 0.7:
            dest_folder = 'train'
        else:
            dest_folder = 'valid'

        # Generate a new filename
        new_filename = f"{os.path.splitext(os.path.basename(img_path))[0]}_jpg.rf.{uuid.uuid4().hex[:20]}"

        # Copy image with new filename
        shutil.copy(img_path, os.path.join(dest_path, dest_folder, 'images', f"{new_filename}.jpg"))

        # Convert and save annotation with new filename
        convert_annotation(xml_path,
                           os.path.join(dest_path, dest_folder, 'labels', f"{new_filename}.txt"),
                           class_mapping)

def create_data_yaml(dest_path, class_names):
    yaml_content = f"""train: ../train/images
val: ../valid/images
test: ../test/images

nc: {len(class_names)}
names: {class_names}
"""
    with open(os.path.join(dest_path, 'data.yaml'), 'w') as f:
        f.write(yaml_content)

if __name__ == '__main__':
    source_path = '/home/shumin/Downloads/'  # 当前目录
    dest_path = '/home/shumin/Downloads/yolo_dataset'
    class_mapping = {'D00': 0, 'D10': 1, 'D20': 2, 'D40': 3}
    class_names = ['Longitudinal Crack', 'Transverse Crack', 'Aligator Crack', 'Pothole']

    process_dataset(source_path, dest_path, class_mapping)
    create_data_yaml(dest_path, class_names)

    print("数据集转换完成！")
