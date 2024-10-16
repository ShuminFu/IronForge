import os
from PIL import Image
import argparse


def convert_to_webp(input_path, output_path, quality=80):
    """
    将输入图片转换为WebP格式

    :param input_path: 输入图片的路径
    :param output_path: 输出WebP图片的路径
    :param quality: WebP图片的质量，范围0-100，默认80
    """
    try:
        img = Image.open(input_path)

        # 如果图片有透明通道，保留透明度
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img.save(output_path, 'WEBP', quality=quality)
        print(f"成功转换: {input_path} -> {output_path}")
    except Exception as e:
        print(f"转换失败 {input_path}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="将图片转换为WebP格式")
    parser.add_argument("input", help="输入图片或目录的路径")
    parser.add_argument("-o", "--output", help="输出目录路径，默认为当前目录", default=".")
    parser.add_argument("-q", "--quality", type=int, help="WebP质量 (0-100)", default=80)
    args = parser.parse_args()

    if os.path.isfile(args.input):
        # 单个文件转换
        filename = os.path.basename(args.input)
        name, _ = os.path.splitext(filename)
        output_path = os.path.join(args.output, f"{name}.webp")
        convert_to_webp(args.input, output_path, args.quality)
    elif os.path.isdir(args.input):
        # 目录批量转换
        for root, _, files in os.walk(args.input):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                    input_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, args.input)
                    output_dir = os.path.join(args.output, relative_path)
                    os.makedirs(output_dir, exist_ok=True)
                    name, _ = os.path.splitext(file)
                    output_path = os.path.join(output_dir, f"{name}.webp")
                    convert_to_webp(input_path, output_path, args.quality)
    else:
        print("输入路径无效")


if __name__ == "__main__":
    main()