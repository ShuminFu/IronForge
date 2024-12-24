import os
from pathlib import Path


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


def main():
    # 获取当前目录作为仓库路径
    repo_path = os.getcwd()
    total_lines, file_count, results = scan_repository(repo_path)

    # 按行数从多到少排序
    results.sort(key=lambda x: x[1], reverse=True)

    # 打印统计结果
    print("\n=== Python代码统计结果 ===")
    print(f"仓库路径: {repo_path}")
    print(f"Python文件总数: {file_count}")
    print(f"代码总行数: {total_lines}")
    print("\n前10个最大的Python文件:")
    for path, lines in results[:10]:
        print(f"{path:<50} {lines:>8} 行")


if __name__ == '__main__':
    main()

