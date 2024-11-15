import os
import asyncio
import aiofiles
from PIL import Image
import io
from concurrent.futures import ProcessPoolExecutor


async def compress_image(image_path, output_dir, max_size_kb=500, initial_quality=90):
    async with aiofiles.open(image_path, 'rb') as f:
        img_data = await f.read()

    img = Image.open(io.BytesIO(img_data))

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    quality = initial_quality
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        size_kb = buffer.getbuffer().nbytes / 1024

        if size_kb <= max_size_kb:
            break

        if quality <= 10:
            print(f"警告: 无法将 {image_path} 压缩到 {max_size_kb}KB 以下")
            return

        quality -= 5

    base_name = os.path.basename(image_path)
    name, _ = os.path.splitext(base_name)
    compressed_name = f"{name}_compressed.jpg"
    output_path = os.path.join(output_dir, compressed_name)

    buffer.seek(0)
    async with aiofiles.open(output_path, 'wb') as f:
        await f.write(buffer.getvalue())

    print(f"已压缩 {image_path} 到 {size_kb:.2f}KB，保存为 {output_path}")


async def process_file(file_path, output_dir):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        await compress_image(file_path, output_dir)


async def process_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tasks = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            tasks.append(process_file(file_path, output_dir))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("使用方法: python script.py <输入图片目录路径> <输出目录路径>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]

    if not os.path.isdir(input_directory):
        print("错误: 提供的输入路径不是一个有效的目录")
        sys.exit(1)

    asyncio.run(process_directory(input_directory, output_directory))
    print("所有图片处理完成")