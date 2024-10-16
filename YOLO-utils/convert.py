import os
import glob
import argparse


def yolo_to_polygon(cls, x_center, y_center, width, height):
    """
    将YOLO格式转换为polygon格式
    """
    x1 = x_center - width / 2
    y1 = y_center - height / 2
    x2 = x_center + width / 2
    y2 = y_center + height / 2
    return f"{cls} {x1} {y1} {x2} {y1} {x2} {y2} {x1} {y2}"


def process_file(file_path):
    """
    处理单个文件,将YOLO格式转换为polygon格式
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 5:  # YOLO格式
            cls, x_center, y_center, width, height = map(float, parts)
            new_line = yolo_to_polygon(int(cls), x_center, y_center, width, height)
        else:  # 假设其他格式为polygon,保持不变
            new_line = line.strip()
        new_lines.append(new_line)

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))


def main(labels_dir):
    for txt_file in glob.glob(os.path.join(labels_dir, '*.txt')):
        process_file(txt_file)
    print(f"所有文件处理完成，共处理 {len(glob.glob(os.path.join(labels_dir, '*.txt')))} 个文件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='将YOLO格式转换为polygon格式')
    parser.add_argument('labels_dir', type=str, help='标注文件所在的目录路径', nargs='+')
    args = parser.parse_args()

    # 将所有参数合并为一个路径
    labels_dir = ' '.join(args.labels_dir)
    main(labels_dir)