# -*- coding: utf-8 -*-
# Copyright (c) 2024 Manuel Schneider

"""
Translates text using the python package translators. See https://pypi.org/project/translators/
"""

from locale import getdefaultlocale
from pathlib import Path
from time import sleep, time
import requests
from albert import *
import translators as ts

md_iid = '2.3'
md_version = "1.9"
md_name = "Translator with API"
md_description = "Translate sentences by calling translate API such as local host libretranslate"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/python/tree/main/translators"
md_authors = "@shumin"
md_lib_dependencies = "translators"


class Plugin(PluginInstance, TriggerQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(
            self, self.id, self.name, self.description,
            synopsis="[en] <text>",
            defaultTrigger='tr '
        )
        self.iconUrls = [f"file:{Path(__file__).parent}/google_translate.png"]
        self.api_url = "http://10.1.20.124:5000/translate"
        

    def configWidget(self):
        return [
            {
                'type': 'label',
                'text': __doc__.strip(),
            },
            {
                'type': 'combobox',
                'property': 'translator',
                'label': 'Translator',
                'items': ts.translators_pool
            },
            {
                'type': 'lineedit',
                'property': 'lang',
                'label': 'Default language',
            }
        ]

    def handleTriggerQuery(self, query):
        start_time = time()
        stripped = query.string.strip()
        if stripped:
            for _ in range(10):
                sleep(0.001)
                if not query.isValid:
                    return

            splits = stripped.split(maxsplit=1)
            if len(splits) == 2 and splits[0] == 'en':
                target, text = 'en', splits[1]
            else:
                target, text = 'zh', stripped

            try:
                payload = {
                    "q": text,
                    "source": "auto",
                    "target": target,
                    "format": "text",
                    "alternatives": 3,
                    "api_key": ""
                }
                # 添加重试机制
                max_retries = 3
                for attempt in range(max_retries):
                    response = requests.post(self.api_url, json=payload, allow_redirects=False)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 302:
                        warning(f"请求被重定向，正在重试... (尝试 {attempt + 1}/{max_retries})")
                        sleep(0.05)  # 在重试之前稍作等待
                    else:
                        response.raise_for_status()
                else:
                    raise Exception(f"达到最大重试次数 ({max_retries})，翻译失败")
                result = response.json()

                translation = result['translatedText']
                detected_lang = result['detectedLanguage']['language']
                alternatives = result.get('alternatives', [])
                end_time = time()
                elapsed_time = round(end_time - start_time, 3)
                actions = []
                def create_actions(text):
                    actions = []
                    if havePasteSupport():
                        actions.append(
                            Action(
                                "paste", "复制到剪贴板并粘贴到最前面的窗口",
                                lambda t=text: setClipboardTextAndPaste(t)
                            )
                        )
                    actions.append(
                    Action("copy", "复制到剪贴板",
                           lambda t=text: setClipboardText(t))
                    )
                    return actions
                
                if havePasteSupport():
                    actions.append(
                        Action(
                            "paste", "Copy to clipboard and paste to front-most window",
                            lambda t=translation: setClipboardTextAndPaste(t)
                        )
                    )

                actions.append(
                    Action("copy", "Copy to clipboard",
                           lambda t=translation: setClipboardText(t))
                )

                query.add(StandardItem(
                    id=self.id,
                    text=translation,
                    subtext=f"{detected_lang.upper()} > {target.upper()}, time: {elapsed_time}",
                    iconUrls=self.iconUrls,
                    actions=actions
                ))

                # 添加替代翻译结果
                for i, alt in enumerate(alternatives, 1):
                    query.add(StandardItem(
                    id=f"{self.id}_alt_{i}",
                    text=alt,
                    subtext=f"{detected_lang.upper()} > {target.upper()}",
                    iconUrls=self.iconUrls,
                    actions=create_actions(alt)
                ))

            except Exception as e:

                query.add(StandardItem(
                    id=self.id,
                    text="Error",
                    subtext=str(e),
                    iconUrls=self.iconUrls
                ))

                warning(str(e))
