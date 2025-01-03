import gradio as gr
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
import html
import re


def process_json_line(line: str, indent_level: int = 0) -> tuple[str, bool]:
    """处理单行JSON，返回处理后的行和是否需要折叠按钮"""
    stripped = line.strip()
    needs_fold = stripped.endswith('{') or stripped.endswith('[')
    indent = ' ' * (indent_level * 2)

    # 生成缩进辅助线的HTML
    indent_guides = ''
    for i in range(indent_level):
        indent_guides += f'<span class="indent-guide" style="left: {i * 20 + 10}px"></span>'

    if needs_fold:
        fold_button = '<span class="fold-button">▼</span>'
        return f'{indent_guides}{indent}{fold_button}{line}', True
    return f'{indent_guides}{indent}{line}', False


def add_fold_buttons(json_str: str) -> str:
    """为JSON字符串添加折叠按钮"""
    # 移除多余的空行和空格
    lines = [line for line in json_str.split('\n') if line.strip()]
    processed_lines = []
    indent_level = 0

    for line in lines:
        stripped = line.strip()

        # 处理缩进级别
        if stripped.startswith('}') or stripped.startswith(']'):
            indent_level = max(0, indent_level - 1)

        processed_line, needs_fold = process_json_line(stripped, indent_level)
        if needs_fold:
            processed_lines.append(f'<div class="line foldable" data-indent="{indent_level}">{processed_line}</div>')
            indent_level += 1
        else:
            processed_lines.append(f'<div class="line" data-indent="{indent_level}">{processed_line}</div>')

    return ''.join(processed_lines)


def create_tree_view(json_data, level=0) -> str:
    """创建JSON的树形视图HTML"""

    def get_value_type(value):
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, str):
            return "string"
        else:
            return type(value).__name__

    if isinstance(json_data, dict):
        items = []
        for key, value in json_data.items():
            if isinstance(value, (dict, list)):
                items.append(f'''
                    <div class="tree-item" style="margin-left: {level * 20}px">
                        <div class="tree-line"></div>
                        <div class="tree-toggle" onclick="this.classList.toggle('collapsed'); this.nextElementSibling.nextElementSibling.classList.toggle('collapsed')">▼</div>
                        <span class="tree-key">{html.escape(str(key))}</span>
                        <div class="tree-content">
                            {create_tree_view(value, level + 1)}
                        </div>
                    </div>
                ''')
            else:
                value_type = get_value_type(value)
                items.append(f'''
                    <div class="tree-item leaf" style="margin-left: {level * 20}px">
                        <div class="tree-line"></div>
                        <span class="tree-key">{html.escape(str(key))}</span>:
                        <span class="tree-value copyable" data-type="{value_type}" onclick="copyToClipboard(this)" title="点击复制">{html.escape(str(value))}</span>
                    </div>
                ''')
        return ''.join(items)
    elif isinstance(json_data, list):
        items = []
        for i, value in enumerate(json_data):
            if isinstance(value, (dict, list)):
                items.append(f'''
                    <div class="tree-item" style="margin-left: {level * 20}px">
                        <div class="tree-line"></div>
                        <div class="tree-toggle" onclick="this.classList.toggle('collapsed'); this.nextElementSibling.nextElementSibling.classList.toggle('collapsed')">▼</div>
                        <span class="tree-key">[{i}]</span>
                        <div class="tree-content">
                            {create_tree_view(value, level + 1)}
                        </div>
                    </div>
                ''')
            else:
                value_type = get_value_type(value)
                items.append(f'''
                    <div class="tree-item leaf" style="margin-left: {level * 20}px">
                        <div class="tree-line"></div>
                        <span class="tree-key">[{i}]</span>:
                        <span class="tree-value copyable" data-type="{value_type}" onclick="copyToClipboard(this)" title="点击复制">{html.escape(str(value))}</span>
                    </div>
                ''')
        return ''.join(items)
    else:
        value_type = get_value_type(json_data)
        return f'<span class="tree-value copyable" data-type="{value_type}" onclick="copyToClipboard(this)" title="点击复制">{html.escape(str(json_data))}</span>'


def format_json(input_json: str, view_type: str = "normal") -> str | dict:
    """格式化JSON字符串并添加语法高亮"""
    try:
        if not input_json.strip():
            return "请输入JSON数据" if view_type != "gradio" else {}

        # 解析JSON
        parsed = json.loads(input_json)

        # Gradio内置JSON视图
        if view_type == "gradio":
            return parsed

        if view_type == "tree":
            tree_html = create_tree_view(parsed)
            return f"""
            <div class="tree-view">
                {tree_html}
            </div>
            <style>
                .tree-view {{
                    background: #1e1e1e;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                    font-family: 'Monaco', 'Consolas', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    color: #f8f8f2;
                    overflow: auto;
                    position: relative;
                }}

                .tree-item {{
                    padding: 2px 0;
                    white-space: nowrap;
                    position: relative;
                }}

                .tree-line {{
                    position: absolute;
                    left: -12px;
                    top: 0;
                    bottom: 0;
                    width: 1px;
                    background-color: #444;
                }}

                .tree-item:before {{
                    content: '';
                    position: absolute;
                    left: -12px;
                    top: 50%;
                    width: 12px;
                    height: 1px;
                    background-color: #444;
                }}

                .tree-item.leaf:before {{
                    width: 8px;
                }}

                .tree-toggle {{
                    cursor: pointer;
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    line-height: 20px;
                    text-align: center;
                    color: #888;
                    user-select: none;
                    transition: transform 0.2s;
                    transform-origin: center center;
                }}

                .tree-toggle.collapsed {{
                    transform: rotate(-90deg);
                }}

                .tree-key {{
                    color: #f92672 !important;
                    font-weight: bold;
                    margin-right: 4px;
                }}

                .tree-value {{
                    color: #a6e22e;
                }}

                .tree-value.copyable {{
                    cursor: pointer;
                    padding: 2px 4px;
                    border-radius: 3px;
                    transition: background-color 0.2s;
                }}

                .tree-value.copyable:hover {{
                    background-color: rgba(255, 255, 255, 0.1);
                }}

                .tree-value[data-type="string"] {{
                    color: #e6db74 !important;
                }}
                .tree-value[data-type="number"] {{
                    color: #ae81ff !important;
                }}
                .tree-value[data-type="boolean"] {{
                    color: #fd971f !important;
                }}
                .tree-value[data-type="null"] {{
                    color: #888 !important;
                }}

                .tree-content {{
                    display: block;
                    position: relative;
                    margin-left: 20px;
                }}

                .tree-content.collapsed {{
                    display: none;
                }}

                /* 复制成功的动画效果 */
                @keyframes copySuccess {{
                    0% {{ background-color: rgba(255, 255, 255, 0.1); }}
                    50% {{ background-color: rgba(0, 255, 0, 0.2); }}
                    100% {{ background-color: rgba(255, 255, 255, 0.1); }}
                }}

                .copy-success {{
                    animation: copySuccess 0.5s ease-in-out;
                }}
            </style>
            <script>
                function copyToClipboard(element) {{
                    const text = element.textContent;
                    navigator.clipboard.writeText(text).then(() => {{
                        element.classList.add('copy-success');
                        setTimeout(() => {{
                            element.classList.remove('copy-success');
                        }}, 500);
                    }});
                }}
            </script>
            """

        # 普通视图的处理逻辑
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=True)
        formatter = HtmlFormatter(style='monokai', cssclass='highlight', nowrap=True)
        highlighted = highlight(formatted, JsonLexer(), formatter)
        highlighted_with_buttons = add_fold_buttons(highlighted)

        return f"""
        <style>
            .json-viewer {{
                background: #1e1e1e;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                min-height: 100px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 14px;
                line-height: 1.5;
                overflow: auto;
            }}

            .line {{
                padding: 2px 0 2px 10px;
                white-space: pre;
                display: block;
                position: relative;
                min-height: 20px;
            }}

            .line:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}

            .indent-guide {{
                position: absolute;
                top: 0;
                bottom: 0;
                width: 1px;
                background-color: #444;
                pointer-events: none;
            }}

            .fold-button {{
                cursor: pointer;
                display: inline-block;
                width: 20px;
                text-align: center;
                color: #888;
                user-select: none;
                transition: transform 0.2s;
                position: relative;
                z-index: 1;
            }}

            .fold-button:hover {{
                color: #fff;
            }}

            .fold-button.folded {{
                transform: rotate(-90deg);
            }}

            .foldable-content {{
                position: relative;
            }}

            .foldable-content.folded {{
                display: none;
            }}

            /* Pygments Monokai 主题 - 优化高亮样式 */
            .highlight {{ background: transparent !important; color: #f8f8f2 !important; }}
            .highlight .p {{ color: #f8f8f2 !important; }}
            .highlight .s2, .highlight .s1 {{ color: #a6e22e !important; }}
            .highlight .mi, .highlight .mf {{ color: #ae81ff !important; }}
            .highlight .kc {{ color: #fd971f !important; }}
            .highlight .nt {{ color: #f92672 !important; }}
        </style>
        <script>
            function toggleFoldButton(event) {{
                const button = event.target;
                if (!button.classList.contains('fold-button')) return;

                button.classList.toggle('folded');
                const line = button.closest('.line');
                if (!line) return;

                let content = line.nextElementSibling;
                while (content && !content.classList.contains('line')) {{
                    if (content.classList.contains('foldable-content')) {{
                        content.classList.toggle('folded');
                        break;
                    }}
                    content = content.nextElementSibling;
                }}
                event.stopPropagation();
            }}

            function initFoldButtons() {{
                const buttons = document.querySelectorAll('.fold-button');
                buttons.forEach(button => {{
                    button.removeEventListener('click', toggleFoldButton);
                    button.addEventListener('click', toggleFoldButton);
                }});

                document.querySelectorAll('.foldable').forEach(line => {{
                    const nextLines = [];
                    let next = line.nextElementSibling;
                    let depth = 1;

                    while (next && depth > 0) {{
                        const content = next.textContent.trim();
                        if (content.endsWith('{{') || content.endsWith('[')) {{
                            depth++;
                        }} else if (content === '}}' || content === ']') {{
                            depth--;
                        }}
                        if (depth > 0) {{
                            nextLines.push(next);
                        }}
                        next = next.nextElementSibling;
                    }}

                    if (nextLines.length > 0) {{
                        const wrapper = document.createElement('div');
                        wrapper.className = 'foldable-content';
                        line.parentNode.insertBefore(wrapper, line.nextSibling);
                        nextLines.forEach(node => wrapper.appendChild(node));
                    }}
                }});
            }}

            // 使用 MutationObserver 监听DOM变化
            if (typeof foldButtonsObserver === 'undefined') {{
                window.foldButtonsObserver = new MutationObserver((mutations) => {{
                    mutations.forEach((mutation) => {{
                        if (mutation.addedNodes.length) {{
                            setTimeout(initFoldButtons, 0);
                        }}
                    }});
                }});

                foldButtonsObserver.observe(document.body, {{
                    childList: true,
                    subtree: true
                }});
            }}

            // 初始化
            document.addEventListener('DOMContentLoaded', initFoldButtons);
            setTimeout(initFoldButtons, 100);
        </script>
        <div class="json-viewer">
            <div class="highlight">
                {highlighted_with_buttons}
            </div>
        </div>
        """

    except json.JSONDecodeError as e:
        return f"JSON解析错误: {str(e)}" if view_type != "gradio" else {}
    except Exception as e:
        return f"发生错误: {str(e)}" if view_type != "gradio" else {}


# 创建Gradio界面
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# JSON格式化工具")
    gr.Markdown("支持任意格式JSON的美化，包括压缩格式。支持语法高亮和折叠功能。")
    gr.Markdown("* 默认使用树形视图，点击 ▼ 按钮可以折叠/展开JSON对象和数组")
    gr.Markdown("* 支持无限层级的折叠")
    gr.Markdown("* 支持树形视图、普通视图和Gradio内置视图切换")
    gr.Markdown("* 输出窗口支持拖拽调整大小")

    # 添加自定义CSS
    gr.HTML("""
    <style>
        .resizable-box {
            resize: both;
            overflow: auto;
            min-height: 300px;
            min-width: 200px;
            max-height: 800px;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }

        /* 自定义滚动条样式 */
        .resizable-box::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        .resizable-box::-webkit-scrollbar-track {
            background: #1e1e1e;
            border-radius: 4px;
        }

        .resizable-box::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
        }

        .resizable-box::-webkit-scrollbar-thumb:hover {
            background: #666;
        }

        /* 调整JSON组件的样式 */
        .resizable-box > .gradio-container {
            height: 100%;
        }

        .resizable-box > .gradio-container > div:first-child {
            height: 100%;
            margin: 0;
        }

        .resizable-box .json-component {
            height: 100% !important;
            background: transparent;
        }

        .resizable-box .json-component > div {
            height: 100% !important;
            max-height: none !important;
        }

        .resizable-box .json-component > div > pre {
            height: 100% !important;
            max-height: none !important;
        }

        /* 调整HTML视图的样式 */
        .resizable-box .json-viewer {
            margin: 0;
            height: 100%;
        }

        /* 调整树形视图的样式 */
        .resizable-box .tree-view {
            margin: 0;
            height: 100%;
        }

        /* 移除JSON组件的label */
        .resizable-box .gradio-container .label-wrap {
            display: none;
        }
    </style>
    """)

    with gr.Row():
        input_json = gr.Textbox(
            label="输入JSON",
            placeholder="在此粘贴任意格式的JSON...",
            lines=10,
            max_lines=30,
            show_copy_button=True,
            container=True,
            scale=1,
            interactive=True,
        )

    with gr.Row():
        view_type = gr.Radio(
            choices=["tree", "normal", "gradio"],
            value="tree",
            label="视图类型",
            interactive=True
        )
        format_btn = gr.Button("格式化", variant="primary", size="lg")

    with gr.Row():
        with gr.Column(elem_classes="resizable-box", scale=1):
            output_json = gr.JSON(
                label=None,  # 移除label
                container=False,  # 移除container
                visible=True,
                elem_classes="json-component"
            )
            output_html = gr.HTML(
                label="格式化结果",
                container=True,
                visible=False
            )


    def update_view(input_text: str, view_type: str):
        result = format_json(input_text, view_type)
        if view_type == "gradio":
            return {
                output_html: gr.update(visible=False),
                output_json: gr.update(visible=True, value=result)
            }
        else:
            return {
                output_html: gr.update(visible=True, value=result),
                output_json: gr.update(visible=False)
            }


    # 添加示例数据
    examples = gr.Examples(
        examples=[
            [
                '{"name":"张三","age":25,"skills":["Python","JavaScript"],"address":{"city":"北京","street":"朝阳区"},"projects":{"web":{"frontend":true,"backend":false},"mobile":null}}'],
            [
                '{"data":{"users":[{"id":1,"name":"李四","details":{"age":30,"role":"admin"}},{"id":2,"name":"王五","details":{"age":25,"role":"user"}}],"total":2},"status":"success"}']
        ],
        inputs=[input_json],
    )

    # 绑定按钮点击事件
    format_btn.click(
        fn=update_view,
        inputs=[input_json, view_type],
        outputs=[output_html, output_json],
    )

    # 输入框回车时自动格式化
    input_json.submit(
        fn=update_view,
        inputs=[input_json, view_type],
        outputs=[output_html, output_json],
    )

    # 视图类型改变时自动更新
    view_type.change(
        fn=update_view,
        inputs=[input_json, view_type],
        outputs=[output_html, output_json],
    )

if __name__ == "__main__":
    demo.launch()
