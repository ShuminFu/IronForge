# -*- coding: utf-8 -*-
# Copyright (c) 2024 Manuel Schneider

"""
Translates text using the python package translators. See https://pypi.org/project/translators/
"""

from locale import getdefaultlocale
from pathlib import Path
from time import sleep
import requests
from albert import *
import translators as ts

md_iid = '2.3'
md_version = "1.8"
md_name = "Translator"
md_description = "Translate sentences using 'translators' package"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/python/tree/main/translators"
md_authors = "@manuelschneid3r"
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
        stripped = query.string.strip()
        if stripped:
            for _ in range(50):
                sleep(0.01)
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
                response = requests.post(self.api_url, json=payload)
                response.raise_for_status()
                result = response.json()

                translation = result['translatedText']
                detected_lang = result['detectedLanguage']['language']
                alternatives = result.get('alternatives', [])
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
                    subtext=f"{detected_lang.upper()} > {target.upper()}",
                    iconUrls=self.iconUrls,
                    actions=actions
                ))

                # 添加替代翻译结果
                for i, alt in enumerate(alternatives, 1):
                    query.add(StandardItem(
                    id=f"{self.id}_alt_{i}",
                    text=alt,
                    subtext=f"{detected_lang.upper()} > {target.upper()})",
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