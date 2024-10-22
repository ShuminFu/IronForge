# Albert Translator Plugin

## Introduction

This is a translation plugin designed for the Albert launcher. It utilizes a self-hosted LibreTranslate API to provide fast and efficient translation services.

## Features

- Supports translation between Chinese and English
- Provides main translation result and multiple alternatives
- Allows direct copying of translation results or pasting to the active window

## Usage

1. In Albert, type the trigger keyword `tr` followed by a space.
2. Enter the text you want to translate. By default, it will translate to Chinese.
3. To translate to English, prefix the text with "en ".

Examples:
- `tr 你好` will translate "你好" to English
- `tr en hello` will translate "hello" to Chinese

## Installation

1. Ensure Python and the `requests` library are installed on your system.
2. Place the plugin files in Albert's plugin directory.
3. Enable the plugin in Albert's settings.

## Dependencies

- Python 3.6+
- requests library

## Configuration

The plugin uses a self-hosted LibreTranslate API. Make sure to set the correct API URL in the `__init__.py` file:
