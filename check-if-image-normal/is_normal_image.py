import cv2
import numpy as np


def is_normal_image(image_path: str) -> bool:
    # 读取图片
    image = cv2.imread(image_path)

    # 检查图片是否成功读取
    if image is None:
        print(f"无法读取图片: {image_path}")
        return False

    # 将图片转换为HSV颜色空间
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 计算颜色直方图
    hist = cv2.calcHist([hsv_image], [0, 1], None, [180, 256], [0, 180, 0, 256])

    # 归一化直方图
    hist = cv2.normalize(hist, hist).flatten()

    # 计算颜色分布的熵
    hist_entropy = -np.sum(hist * np.log2(hist + 1e-7))
    print(f"图片的颜色分布熵: {hist_entropy}")

    # 设置一个阈值来判断图片是否正常
    entropy_threshold = 5.0

    # 如果熵值低于阈值，认为图片不正常
    return hist_entropy > entropy_threshold


if __name__ == "__main__":
    import os

    images_dir = '/Users/apple/Desktop/work/IronForge/check-if-image-normal/20240829190353_f789bdf1c3d043c985fe36cf6e5d2818_8'
    # 获取当前目录下的所有文件
    all_files = os.listdir(images_dir)
    print(all_files)

    # 筛选出所有图片文件（假设图片文件的扩展名为 .jpg, .jpeg, .png）
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in image_extensions]

    # 遍历每个图片文件并判断是否正常
    for image_file in image_files:
        image_path = os.path.join(images_dir, image_file)
        if is_normal_image(image_path):
            print(f"{image_file} 是正常的")
        else:
            print(f"{image_file} 不是正常的")
