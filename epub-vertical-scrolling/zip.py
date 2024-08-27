import os
import zipfile
from typing import List


def create_epub(output_filename: str, mimetype_path: str, folders: List[str]) -> None:
    """
    将指定的文件夹打包成 .epub 文件，并确保 mimetype 文件正确放置

    :param output_filename: 输出的 .epub 文件名
    :param mimetype_path: mimetype 文件的路径
    :param folders: 需要打包的文件夹列表
    """
    with zipfile.ZipFile(output_filename, 'w') as epub_zip:
        # 添加 mimetype 文件，且不压缩
        epub_zip.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)

        for folder in folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(folder))
                    # 确保 mimetype 文件不被重复添加
                    if arcname != 'mimetype':
                        epub_zip.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)


# 使用示例
mimetype_file = './mimetype'
folders_to_zip = ['./EPUB', './META-INF']
create_epub('设计模式.epub', mimetype_file, folders_to_zip)