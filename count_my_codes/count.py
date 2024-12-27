import os
from pathlib import Path
import argparse


def count_lines(file_path):
    """统计单个文件的代码行数,跳过空行和注释行"""
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if line and not line.startswith('#'):
                count += 1
    return count


def scan_repository(repo_path):
    """扫描整个仓库的.py文件并统计代码行数"""
    total_lines = 0
    file_count = 0
    results = []

    # 遍历所有.py文件
    for py_file in Path(repo_path).rglob('*.py'):
        # 跳过虚拟环境目录
        if 'venv' in str(py_file) or '.env' in str(py_file):
            continue

        try:
            lines = count_lines(py_file)
            relative_path = os.path.relpath(py_file, repo_path)
            results.append((relative_path, lines))
            total_lines += lines
            file_count += 1
        except Exception as e:
            print(f"处理文件 {py_file} 时出错: {e}")

    return total_lines, file_count, results


def scan_repository_without_tests(repo_path):
    """扫描整个仓库的.py文件并统计代码行数，跳过test_开头和_example.py结尾的文件"""
    total_lines = 0
    file_count = 0
    results = []

    # 遍历所有.py文件
    for py_file in Path(repo_path).rglob('*.py'):
        # 跳过虚拟环境目录、测试文件和示例文件
        if ('venv' in str(py_file) or
                '.env' in str(py_file) or
                py_file.name.startswith('test_') or
                py_file.name.endswith('_example.py')):
            continue

        try:
            lines = count_lines(py_file)
            relative_path = os.path.relpath(py_file, repo_path)
            results.append((relative_path, lines))
            total_lines += lines
            file_count += 1
        except Exception as e:
            print(f"处理文件 {py_file} 时出错: {e}")

    return total_lines, file_count, results


def main():
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(
        description='统计Python代码行数工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                     # 统计代码行数(不包含测试和示例文件)
  %(prog)s --include-tests     # 统计所有Python文件的代码行数

说明:
  - 默认会跳过以下文件:
    * test_*.py 开头的测试文件
    * *_example.py 结尾的示例文件
    * venv/ 和 .env/ 目录下的文件
  - 统计时会忽略空行和注释行
  - 结果按代码行数从多到少排序
""")

    parser.add_argument(
        '--include-tests',
        action='store_true',
        help='是否包含测试文件(test_*.py)和示例文件(*_example.py)'
    )
    args = parser.parse_args()

    # 获取当前目录作为仓库路径
    repo_path = os.getcwd()

    # 根据参数选择扫描函数
    if args.include_tests:
        total_lines, file_count, results = scan_repository(repo_path)
    else:
        total_lines, file_count, results = scan_repository_without_tests(repo_path)

    # 按行数从多到少排序
    results.sort(key=lambda x: x[1], reverse=True)

    # 打印统计结果
    print("\n=== Python代码统计结果 ===")
    print(f"仓库路径: {repo_path}")
    print(f"包含测试文件: {'是' if args.include_tests else '否'}")
    print(f"Python文件总数: {file_count}")
    print(f"代码总行数: {total_lines}")
    print("\n前10个最大的Python文件:")
    for path, lines in results[:10]:
        print(f"{path:<50} {lines:>8} 行")


# 使用方法：
# 默认不包含测试文件：python script.py
# 包含测试文件：python script.py --include-tests

if __name__ == '__main__':
    main()
