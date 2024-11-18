from ultralytics.data.augment import Albumentations
from ultralytics.utils import LOGGER, colorstr
from ultralytics import YOLO

def __init__(self, p=1.0):
    """初始化用于YOLO边界框格式参数的变换对象."""
    self.p = p
    self.transform = None
    prefix = colorstr("albumentations: ")
    try:
        import albumentations as A

        # 插入所需的转换
        T = [
            #A.LongestMaxSize(max_size=640, p=1.0),  # 等比例缩放
            A.RandomBrightnessContrast(p=0.5),
        ]

        self.transform = A.Compose(T, bbox_params=A.BboxParams(format="yolo", label_fields=["class_labels"]))

        LOGGER.info(prefix + ", ".join(f"{x}".replace("always_apply=False, ", "") for x in T if x.p))
    except ImportError:  # 包未安装，跳过
        pass
    except Exception as e:
        LOGGER.info(f"{prefix}{e}")


Albumentations.__init__ = __init__
"""
For multi-GPU training, ensure you're modifying the actual source file instead of using monkey patching, as DDP processes may not apply those changes.
"""
model = YOLO('yolo11n.pt')

# results = model.train(data='dataset.yaml', epochs=300, imgsz=[1920,1080], augment=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default='dataset.yaml', help='数据集配置文件路径')
    parser.add_argument('--model', type=str, default='yolo11n.pt', help='模型路径')
    parser.add_argument('--epochs', type=int, default=300, help='训练轮数')
    parser.add_argument('--imgsz', nargs='+', type=int, default=640,
                        help='图像尺寸. 可以是单个数字(如 640)或者 [width height]')
    parser.add_argument('--device', nargs='+', type=int, default=[7, 6], help='GPU设备ID')
    args = parser.parse_args()

    # # 处理imgsz参数
    # if len(args.imgsz) == 1:
    #     args.imgsz = [args.imgsz[0], args.imgsz[0]]  # 如果只输入一个数字，转换为正方形

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        device=args.device,
        augment=True
    )