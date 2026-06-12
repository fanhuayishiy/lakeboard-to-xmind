# lakeboard-to-xmind

[![CI](https://github.com/fanhuayishiy/lakeboard-to-xmind/actions/workflows/ci.yml/badge.svg)](https://github.com/fanhuayishiy/lakeboard-to-xmind/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

将语雀导出的 Lakeboard 思维导图文件（`.lakeboard`）与 XMind 文件（`.xmind`）互相转换。

> 当前仅支持语雀 Lakeboard 的“思维导图”格式与 XMind 思维导图之间的互转。其他 Lakeboard 白板元素、流程图、自由画布、表格、便签等格式暂不支持。

## 功能特性

- 将语雀 Lakeboard 思维导图节点转换为 XMind 主题。\n- 支持将 XMind 思维导图反向转换为语雀 Lakeboard 思维导图 JSON。
- 保留标题层级、子节点顺序，以及左右分支布局。
- 尽量保留常见样式，包括节点填充色、分支线颜色、线宽、圆角主题、优先级/旗帜标记、概要和外框边界。
- 清理标题中的 HTML 标签、`<br>`、零宽字符、不间断空格和 HTML 实体。
- 支持使用已有 `.xmind` 文件作为模板，以提高特定 XMind 版本的兼容性。
- 输出标准 XMind 压缩包条目：`content.json`、`metadata.json`、`manifest.json`、`content.xml`、`Thumbnails/thumbnail.png`。
- 运行时只依赖 Python 标准库。

## 安装

从源码目录安装：

```bash
python -m pip install .
```

开发模式安装：

```bash
python -m pip install -e .
```

## 使用方法

转换语雀 Lakeboard 思维导图文件为 XMind：\n\n```bash\nlakeboard-to-xmind to-xmind input.lakeboard -o output.xmind\n```\n\n旧版简写仍然可用：\n\n```bash\nlakeboard-to-xmind input.lakeboard -o output.xmind\n```\n\n反向转换 XMind 为语雀 Lakeboard 思维导图：\n\n```bash\nlakeboard-to-xmind to-lakeboard input.xmind -o output.lakeboard\n```

使用已有 XMind 文件作为兼容性和样式模板：

```bash
lakeboard-to-xmind to-xmind input.lakeboard -o output.xmind --template template.xmind
```

如果某些 XMind 版本提示生成文件格式不正确，建议使用 `--template` 传入一个该版本能正常打开的 `.xmind` 文件。转换器会复用模板中的工作表、主题、兼容 XML、manifest 和缩略图信息，再替换实际思维导图内容。

只转换层级结构，不复制样式：

```bash
lakeboard-to-xmind to-xmind input.lakeboard -o output.xmind --no-style\nlakeboard-to-xmind to-lakeboard input.xmind -o output.lakeboard --no-style
```

## Python API

```python
from lakeboard_to_xmind import convert_lakeboard_to_xmind, convert_xmind_to_lakeboard

result = convert_lakeboard_to_xmind(
    "input.lakeboard",
    "output.xmind",
    template="template.xmind",
)
print(result.topic_count)\n\nreverse = convert_xmind_to_lakeboard("output.xmind", "roundtrip.lakeboard")\nprint(reverse.topic_count)\n```

## 转换逻辑

1. 以 UTF-8 JSON 读取 `.lakeboard` 文件。
2. 在 `diagramData.body` 中查找第一个 `type == "mindmap"` 的对象。
3. 递归转换节点的 `html`、`children`、`layout`、`border`、`treeEdge`、`icons` 等字段。
4. 为 XMind 生成新的主题 ID，并把语雀常见样式字段映射到 XMind topic style。
5. 正向转换时将结果打包为 `.xmind` ZIP 文件；反向转换时输出语雀 Lakeboard JSON。

## 开发

运行测试：

```bash
python -m unittest discover -s tests -v
```

构建包：

```bash
python -m pip install build
python -m build
```

## 兼容性说明

本项目目前只面向语雀 Lakeboard 导出的思维导图数据结构。一个 `.lakeboard` 文件中可能包含多个画布元素，本工具只转换第一个 `mindmap` 根节点。

已支持的常见思维导图能力：

- 普通主题和多级子主题
- 左右分支
- 节点背景色和分支线颜色
- 优先级与旗帜标记
- 语雀 `abstract` 概要节点到 XMind summary
- 简单分组外框备注到 XMind boundary

暂不支持：

- 非思维导图 Lakeboard 元素
- 流程图、自由画布、便签、表格等格式
- 所有语雀画布级装饰的像素级还原
- 多个思维导图根节点自动拆成多个 XMind 工作表\n- XMind 到 Lakeboard 的像素级布局坐标还原

XMind 文件本质是 ZIP 包。较新的 XMind 版本主要读取 `content.json`；部分较旧或更严格的版本还会依赖 `content.xml`、缩略图等兼容条目。遇到兼容性问题时，请优先使用 `--template`。

## 路线图

- 收集更多脱敏后的语雀思维导图样例。
- 改进更多语雀样式到 XMind 样式的映射。
- 支持多个 mindmap 根节点转换为多个 XMind 工作表。

## 参与贡献

欢迎提交 Issue 和 Pull Request。报告转换问题时，请尽量附带一个已脱敏的 `.lakeboard` 示例文件。

## 开源协议

MIT，详见 [LICENSE](LICENSE)。

## 商标说明

语雀、Lakeboard、XMind 均为其各自所有者的商标。本项目是独立开源项目，与语雀或 XMind 官方无从属、授权或背书关系。

