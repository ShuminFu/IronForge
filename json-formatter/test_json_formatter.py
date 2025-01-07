import unittest
from json_formatter import parse_debug_output


class TestJsonFormatter(unittest.TestCase):
    def test_parse_vscode_dataview_output(self):
        # 准备测试数据
        test_input = """('parameters', {'file_path': 'src/html/index.html', 'file_type': 'html', 'mime_type': 'text/html', 'description': 'Main page displaying products in a responsive grid layout.', 'references': ['src/css/main.css', 'src/css/product-card.css', 'src/js/main.js', 'src/js/product-modal.js'], 'code_details': {'project_type': 'web', 'project_description': 'A product display webpage with responsive layout and filtering capabilities.', 'requirements': ['Responsive grid layout', 'Product filtering functionality', 'Modal display for product details'], 'frameworks': ['normalize.css', '@popperjs/core'], 'resources': [{'file_path': 'src/html/index.html', 'type': 'html', 'mime_type': 'text/html', 'description': 'Main page displaying products in a responsive grid layout.', 'references': ['src/css/main.css', 'src/css/product-card.css', 'src/js/main.js', 'src/js/product-modal.js']}, {'file_path': 'src/css/main.css', 'type': 'css', 'mime_type': 'text/css', 'description': 'CSS file for overall responsive layout.'}, {'file_path': 'src/css/product-card.css', 'type': 'css', 'mime_type': 'text/css', 'description': 'CSS file for styling product cards.'}, {'file_path': 'src/js/main.js', 'type': 'javascript', 'mime_type': 'text/javascript', 'description': 'JavaScript file for handling product filtering.'}, {'file_path': 'src/js/product-modal.js', 'type': 'javascript', 'mime_type': 'text/javascript', 'description': 'JavaScript file for product detail modal functionality.'}]}, 'dialogue_context': {'text': '请创建一个响应式的产品展示页面，包含以下功能：\n            1. 主页面(index.html)：\n               - 响应式网格布局展示产品\n               - 产品过滤功能\n            2. 样式文件：\n               - 主样式(main.css)：响应式布局\n               - 产品卡片样式(product-card.css)\n            3. JavaScript文件：\n               - 主逻辑(main.js)：实现产品过滤\n               - 模态框(product-modal.js)：产品详情展示\n            4. 依赖：\n               - normalize.css用于样式重置\n               - @popperjs/core用于模态框定位', 'type': 'CODE_RESOURCE', 'tags': 'code_request,code_type_css,code_type_javascript,code_type_html,framework_normalize.css,framework_@popperjs/core', 'intent': {'intent': 'Create a responsive product display webpage with filtering functionality including HTML, CSS, and JavaScript files.', 'confidence': 1.0, 'parameters': {'text': '请创建一个响应式的产品展示页面，包含以下功能：\n            1. 主页面(index.html)：\n               - 响应式网格布局展示产品\n               - 产品过滤功能\n            2. 样式文件：\n               - 主样式(main.css)：响应式布局\n               - 产品卡片样式(product-card.css)\n            3. JavaScript文件：\n               - 主逻辑(main.js)：实现产品过滤\n               - 模态框(product-modal.js)：产品详情展示\n            4. 依赖：\n               - normalize.css用于样式重置\n               - @popperjs/core用于模态框定位', 'type': 'CODE_RESOURCE', 'tags': 'code_request,code_type_css,code_type_javascript,code_type_html,framework_normalize.css,framework_@popperjs/core', 'is_code_request': True, 'code_details': {'project_type': 'web', 'project_description': 'A product display webpage with responsive layout and filtering capabilities.', 'resources': [{'file_path': 'src/html/index.html', 'type': 'html', 'mime_type': 'text/html', 'description': 'Main page displaying products in a responsive grid layout.', 'references': ['src/css/main.css', 'src/css/product-card.css', 'src/js/main.js', 'src/js/product-modal.js']}, {'file_path': 'src/css/main.css', 'type': 'css', 'mime_type': 'text/css', 'description': 'CSS file for overall responsive layout.'}, {'file_path': 'src/css/product-card.css', 'type': 'css', 'mime_type': 'text/css', 'description': 'CSS file for styling product cards.'}, {'file_path': 'src/js/main.js', 'type': 'javascript', 'mime_type': 'text/javascript', 'description': 'JavaScript file for handling product filtering.'}, {'file_path': 'src/js/product-modal.js', 'type': 'javascript', 'mime_type': 'text/javascript', 'description': 'JavaScript file for product detail modal functionality.'}], 'requirements': ['Responsive grid layout', 'Product filtering functionality', 'Modal display for product details'], 'frameworks': ['normalize.css', '@popperjs/core']}}}}, 'opera_id': '96028f82-9f76-4372-976c-f0c5a054db79'})"""

        # 执行解析
        result = parse_debug_output(test_input)

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], 'src/html/index.html')
        self.assertEqual(result['file_type'], 'html')
        self.assertEqual(result['mime_type'], 'text/html')

        # 验证嵌套结构
        self.assertIn('code_details', result)
        code_details = result['code_details']
        self.assertEqual(code_details['project_type'], 'web')

        # 验证列表
        self.assertIn('requirements', code_details)
        self.assertIsInstance(code_details['requirements'], list)
        self.assertEqual(len(code_details['requirements']), 3)

        # 验证复杂嵌套
        self.assertIn('resources', code_details)
        resources = code_details['resources']
        self.assertIsInstance(resources, list)
        self.assertEqual(len(resources), 5)

        # 验证第一个资源
        first_resource = resources[0]
        self.assertEqual(first_resource['file_path'], 'src/html/index.html')
        self.assertEqual(first_resource['type'], 'html')

        # 验证 opera_id
        self.assertEqual(result['opera_id'], '96028f82-9f76-4372-976c-f0c5a054db79')

    def test_simple_vscode_dataview_output(self):
        """测试简单的VSCode DataView输出"""
        test_input = """('parameters', {'key': 'value'})"""
        result = parse_debug_output(test_input)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['key'], 'value')


if __name__ == '__main__':
    unittest.main()
