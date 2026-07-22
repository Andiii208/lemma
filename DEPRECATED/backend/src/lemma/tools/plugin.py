"""插件系统 — 自动发现和加载工具插件

插件格式:
    plugins/
      my_tool/
        plugin.yaml    # 元数据（name, description, version）
        tool.py        # 工具实现（必须有 create_tool(work_dir) -> Tool）
"""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import Tool
from .registry import ToolRegistry

logger = logging.getLogger("ultramath.plugin")


@dataclass
class PluginInfo:
    """插件元数据"""

    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    path: str = ""


def discover_plugins(plugin_dir: str) -> list[PluginInfo]:
    """发现目录下的所有插件"""
    plugins: list[PluginInfo] = []
    plugin_path = Path(plugin_dir)
    if not plugin_path.exists():
        return plugins

    for sub in plugin_path.iterdir():
        if not sub.is_dir():
            continue
        yaml_file = sub / "plugin.yaml"
        tool_file = sub / "tool.py"

        if not yaml_file.exists() or not tool_file.exists():
            continue

        try:
            import yaml

            meta = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            plugins.append(PluginInfo(
                name=meta.get("name", sub.name),
                description=meta.get("description", ""),
                version=meta.get("version", "1.0.0"),
                author=meta.get("author", ""),
                path=str(sub),
            ))
        except Exception as e:
            logger.warning(f"Failed to load plugin metadata from {sub}: {e}")

    return plugins


def load_plugin(plugin_info: PluginInfo, work_dir: str) -> Tool | None:
    """加载单个插件工具"""
    tool_file = Path(plugin_info.path) / "tool.py"
    if not tool_file.exists():
        return None

    try:
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_info.name}", str(tool_file)
        )
        if spec is None or spec.loader is None:
            logger.error(f"无法加载插件规范: {plugin_info.name}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "create_tool"):
            tool = module.create_tool(work_dir)
            if isinstance(tool, Tool):
                return tool
            else:
                logger.warning(f"Plugin {plugin_info.name} create_tool() did not return Tool")
        else:
            logger.warning(f"Plugin {plugin_info.name} missing create_tool() function")

    except Exception as e:
        logger.error(f"Failed to load plugin {plugin_info.name}: {e}")

    return None


def load_plugins_to_registry(
    plugin_dir: str, registry: ToolRegistry, work_dir: str
) -> int:
    """发现并加载所有插件到工具注册表"""
    plugins = discover_plugins(plugin_dir)
    loaded = 0

    for info in plugins:
        tool = load_plugin(info, work_dir)
        if tool:
            registry.register(tool)
            loaded += 1
            logger.info(f"Loaded plugin: {info.name} v{info.version}")

    return loaded
