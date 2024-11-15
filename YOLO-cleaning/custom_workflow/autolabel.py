"""
This is a script for auto labelling images using custom YOLO model.
"""
import argparse
import os
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np


def process_images(input_folder: str, weights_path: str):
    # 加载YOLO模型
    model = YOLO(weights_path)

    # 创建输出文件夹
    output_images = Path('images')
    output_labels = Path('labels')
    output_images.mkdir(exist_ok=True)
    output_labels.mkdir(exist_ok=True)

    # 处理输入文件夹中的每张图片
    for img_file in Path(input_folder).glob('*'):
        if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            # 读取图片
            img = cv2.imread(str(img_file))

            # 进行预测
            results = model(img)

            # 保存图片
            cv2.imwrite(str(output_images / img_file.name), img)

            # 保存标注
            with open(output_labels / f"{img_file.stem}.txt", 'w') as f:
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls, x, y, w, h = box.cls.cpu().numpy()[0], *box.xywhn.cpu().numpy()[0]
                        f.write(f"{int(cls)} {x} {y} {w} {h}\n")

    print(f"处理完成。图片保存在 {output_images} 文件夹，标注保存在 {output_labels} 文件夹。")


def main():
    parser = argparse.ArgumentParser(description='使用YOLO模型处理图片并生成标注')
    parser.add_argument('input_folder', type=str, help='输入图片文件夹路径')
    parser.add_argument('weights_path', type=str, help='YOLO模型权重文件路径')

    args = parser.parse_args()

    process_images(args.input_folder, args.weights_path)


if __name__ == "__main__":
    main()