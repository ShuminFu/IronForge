import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Union


class ObjectParser:
    def __init__(self):
        # 用于匹配基本的键值对模式
        self.kv_pattern = re.compile(r'(\w+)=(.+?)(?=,\s*\w+=|$)')
        # 用于匹配datetime对象
        self.datetime_pattern = re.compile(
            r'datetime\.datetime\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2}),\s*(\d{1,2})(?:,\s*(?:\d{1,2})?)?(?:,\s*tzinfo=datetime\.timezone\.utc)?\)'
        )
        # 用于匹配枚举值
        self.enum_pattern = re.compile(r'<\w+\.(\w+):\s*\'(\w+)\'>')

    def parse_datetime(self, datetime_str: str) -> str:
        """解析datetime字符串为ISO格式"""
        match = self.datetime_pattern.match(datetime_str.strip())
        if match:
            year, month, day, hour, minute = map(int, match.groups()[:5])
            dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
            return dt.isoformat()
        return datetime_str

    def parse_enum(self, enum_str: str) -> str:
        """解析枚举值为字符串"""
        match = self.enum_pattern.match(enum_str.strip())
        if match:
            return match.group(2)
        return enum_str

    def parse_value(self, value: str) -> Any:
        """解析值的类型"""
        value = value.strip()

        # 处理None
        if value == 'None':
            return None

        # 处理布尔值
        if value in ('True', 'False'):
            return value == 'True'

        # 处理数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # 处理datetime
        if 'datetime.datetime' in value:
            return self.parse_datetime(value)

        # 处理枚举
        if value.startswith('<') and value.endswith('>'):
            return self.parse_enum(value)

        # 处理字符串形式的列表
        if (value.startswith('"[') and value.endswith(']"')) or \
           (value.startswith("'[") and value.endswith("]'")):
            # 移除外层引号
            inner_value = value[1:-1]
            return self.parse_object(inner_value)

        # 处理字符串（移除引号）
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return value[1:-1]

        # 处理列表
        if value.startswith('[') and value.endswith(']'):
            return self.parse_object(value)

        # 处理字典
        if value.startswith('{') and value.endswith('}'):
            return self._parse_dict(value[1:-1])

        # 处理命名对象
        if '(' in value and value.endswith(')'):
            obj_content = value[value.index('(')+1:-1]
            return self._parse_dict(obj_content)

        return value

    def _split_items(self, items_str: str) -> List[str]:
        """分割列表或字典中的项"""
        if not items_str.strip():
            return []

        items = []
        current_item = ''
        bracket_count = 0
        quote_char = None
        in_datetime = False

        i = 0
        while i < len(items_str):
            char = items_str[i]

            # 检测datetime开始
            if items_str[i:].startswith('datetime.datetime'):
                in_datetime = True

            # 处理引号
            if char in '"\'':
                if quote_char is None:
                    quote_char = char
                elif char == quote_char and items_str[i-1] != '\\':
                    quote_char = None

            # 如果在引号内，直接添加字符
            if quote_char is not None:
                current_item += char
                i += 1
                continue

            # 如果在datetime内部，需要特殊处理
            if in_datetime:
                current_item += char
                if char == ')':
                    in_datetime = False
                i += 1
                continue

            # 处理逗号分隔
            if char == ',' and bracket_count == 0:
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ''
                i += 1
                while i < len(items_str) and items_str[i].isspace():
                    i += 1
                continue

            current_item += char

            if char in '[{(':
                bracket_count += 1
            elif char in ']})':
                bracket_count -= 1

            i += 1

        if current_item.strip():
            items.append(current_item.strip())

        return items

    def _parse_dict(self, dict_str: str) -> Dict:
        """解析字典内容"""
        if not dict_str.strip():
            return {}

        result = {}
        current_key = None
        current_value = ''
        bracket_count = 0
        quote_char = None
        in_datetime = False

        i = 0
        while i < len(dict_str):
            char = dict_str[i]

            # 检测datetime开始
            if dict_str[i:].startswith('datetime.datetime'):
                in_datetime = True

            # 处理引号
            if char in '"\'':
                if quote_char is None:
                    quote_char = char
                elif char == quote_char and dict_str[i-1] != '\\':
                    quote_char = None

            # 如果在引号内，直接添加字符
            if quote_char is not None:
                if current_key is None:
                    current_value += char
                else:
                    current_value += char
                i += 1
                continue

            # 如果在datetime内部，需要特殊处理
            if in_datetime:
                current_value += char
                if char == ')':
                    in_datetime = False
                i += 1
                continue

            # 处理等号（键值分隔符）
            if char == '=' and bracket_count == 0 and current_key is None:
                current_key = current_value.strip()
                current_value = ''
                i += 1
                continue

            # 处理逗号（键值对分隔符）
            if char == ',' and bracket_count == 0 and current_key is not None:
                if current_value.strip():
                    # 递归解析值
                    parsed_value = self.parse_value(current_value.strip())
                    # 如果解析后仍然是字符串且看起来像是列表或对象，再次尝试解析
                    if isinstance(parsed_value, str):
                        if parsed_value.startswith('[') and parsed_value.endswith(']'):
                            parsed_value = self.parse_object(parsed_value)
                        elif parsed_value.startswith('{') and parsed_value.endswith('}'):
                            parsed_value = self._parse_dict(parsed_value[1:-1])
                        elif '(' in parsed_value and parsed_value.endswith(')'):
                            obj_content = parsed_value[parsed_value.index('(')+1:-1]
                            parsed_value = self._parse_dict(obj_content)
                    result[current_key] = parsed_value
                current_key = None
                current_value = ''
                i += 1
                while i < len(dict_str) and dict_str[i].isspace():
                    i += 1
                continue

            current_value += char

            if char in '[{(':
                bracket_count += 1
            elif char in ']})':
                bracket_count -= 1

            i += 1

        # 处理最后一个键值对
        if current_key is not None and current_value.strip():
            # 递归解析值
            parsed_value = self.parse_value(current_value.strip())
            # 如果解析后仍然是字符串且看起来像是列表或对象，再次尝试解析
            if isinstance(parsed_value, str):
                if parsed_value.startswith('[') and parsed_value.endswith(']'):
                    parsed_value = self.parse_object(parsed_value)
                elif parsed_value.startswith('{') and parsed_value.endswith('}'):
                    parsed_value = self._parse_dict(parsed_value[1:-1])
                elif '(' in parsed_value and parsed_value.endswith(')'):
                    obj_content = parsed_value[parsed_value.index('(')+1:-1]
                    parsed_value = self._parse_dict(obj_content)
            result[current_key] = parsed_value

        return result

    def parse_object(self, obj_str: str) -> Union[Dict, List, Any]:
        """解析对象字符串为字典或列表"""
        if not obj_str:
            return {}

        # 处理最外层的命名对象
        obj_str = obj_str.strip()

        # 处理列表
        if obj_str.startswith('[') and obj_str.endswith(']'):
            items = self._split_items(obj_str[1:-1])
            parsed_items = []
            for item in items:
                item = item.strip()
                # 如果是命名对象，解析为字典
                if '(' in item and item.endswith(')'):
                    # 获取对象名称和内容
                    obj_name = item[:item.index('(')]
                    obj_content = item[item.index('(')+1:-1]
                    parsed_items.append({obj_name: self._parse_dict(obj_content)})
                else:
                    parsed_items.append(self.parse_value(item))
            return parsed_items

        # 处理命名对象
        if '(' in obj_str and obj_str.endswith(')'):
            obj_name = obj_str[:obj_str.index('(')]
            obj_content = obj_str[obj_str.index('(')+1:-1]
            return {obj_name: self._parse_dict(obj_content)}

        return self.parse_value(obj_str)


def parse_debug_output(debug_str: str) -> Dict:
    """将调试输出字符串转换为JSON兼容的字典"""
    parser = ObjectParser()
    return parser.parse_object(debug_str)


if __name__ == '__main__':
    import json

    # 测试用例
    debug_str = """ProcessingDialogue(dialogue_id='d123456789', title='客户咨询对话', created_at=datetime.datetime(2024, 3, 15, 8, 30, tzinfo=datetime.timezone.utc), participants=[User(user_id='u001', name='客服小王', role=<UserRole.AGENT: 'agent'>, avatar_url='https://example.com/avatars/agent1.jpg'), User(user_id='u002', name='张三', role=<UserRole.CUSTOMER: 'customer'>, avatar_url='https://example.com/avatars/customer1.jpg')], messages=[Message(message_id='m001', sender_id='u002', content='你好，我想咨询一下产品退换货的问题', type=<MessageType.TEXT: 'text'>, timestamp=datetime.datetime(2024, 3, 15, 8, 30, 15, tzinfo=datetime.timezone.utc), status=<MessageStatus.DELIVERED: 'delivered'>), Message(message_id='m002', sender_id='u001', content='您好！很高兴为您服务。请问是哪个产品需要退换呢？', type=<MessageType.TEXT: 'text'>, timestamp=datetime.datetime(2024, 3, 15, 8, 30, 30, tzinfo=datetime.timezone.utc), status=<MessageStatus.READ: 'read'>), Message(message_id='m003', sender_id='u002', content={'url': 'https://example.com/images/product.jpg', 'mime_type': 'image/jpeg', 'size': 1024567}, type=<MessageType.IMAGE: 'image'>, timestamp=datetime.datetime(2024, 3, 15, 8, 31, tzinfo=datetime.timezone.utc), status=<MessageStatus.DELIVERED: 'delivered'>)], metadata=DialogueMetadata(channel='web', platform='customer_service', tags=['退换货', '产品咨询'], priority='normal', status='active'), statistics=DialogueStatistics(message_count=3, response_time_avg=15, customer_satisfaction=4.5))"""

    # 解析对象
    result = parse_debug_output(debug_str)

    # 打印格式化的JSON输出
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 验证关键字段
    assert result['dialogue_id'] == 'd123456789'
    assert result['title'] == '客户咨询对话'
    assert result['created_at'] == '2024-03-15T08:30:00+00:00'
    assert len(result['participants']) == 2
    assert len(result['messages']) == 3
    assert result['metadata']['channel'] == 'web'
    assert result['statistics']['message_count'] == 3

    print("\n验证通过！数据结构完整性检查成功。")
