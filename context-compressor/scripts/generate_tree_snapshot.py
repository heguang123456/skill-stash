#!/usr/bin/env python3
"""
Generate an annotated directory tree snapshot for the vType project.

Instead of verbose line-count statistics, produce a concise tree with
module responsibility annotations — more useful for AI context than raw numbers.

Usage:
    python generate_tree_snapshot.py [--root PROJECT_ROOT] [--output FILE]
"""

import os
import sys
from pathlib import Path
from argparse import ArgumentParser

# Mapping of known files to their responsibilities (one-line annotation)
ANNOTATIONS = {
    "config.py": "全局配置中心：16 项核心参数，环境变量 VTYPE_* 覆盖",
    "main.py": "CLI 入口：Click 框架，vtype start/devices/config 命令",
    "core/audio.py": "音频捕获：sounddevice 流模式，PortAudio 回调线程",
    "core/detector.py": "人声检测：WebRTC VAD 状态机，静音切片 + 防抖缓冲",
    "core/recognizer.py": "ASR 推理：faster-whisper int8 量化，单例模型加载",
    "core/typer.py": "键盘模拟：pynput 输出引擎，剪贴板粘贴兜底",
    "core/manager.py": "核心调度器：3 线程拓扑（detector/recognizer/typer）+ 生命周期状态机",
    "utils/clipboard.py": "剪贴板操作：pyperclip + pynput 快捷键模拟",
    "utils/key_monitor.py": "全局热键监听：push-to-talk 交互，pynput Listener + 组合键支持",
}

# Directories to skip
SKIP_DIRS = {
    "__pycache__", ".git", ".workbuddy", ".pytest_cache",
    "NVIDIA Corporation",
}

# File extensions to include
INCLUDE_EXTS = {".py", ".md", ".txt", ".toml", ".cfg", ".ini", ".yml", ".yaml"}


def is_important_dir(name: str) -> bool:
    """Check if directory should be included."""
    return name not in SKIP_DIRS and not name.startswith(".")


def should_show(path: Path) -> bool:
    """Determine if a file should appear in the tree."""
    # Always show key project files
    key_files = {"README.md", "CHANGELOG.md", "REQUIREMENTS.md"}
    if path.name in key_files:
        return True
    # Show Python source, config files, and markdown in docs/
    if path.suffix in INCLUDE_EXTS:
        return True
    return False


def generate_tree(root: Path) -> str:
    """Generate annotated directory tree."""
    lines = [f"# {root.name} — 项目目录树", ""]

    def walk(path: Path, prefix: str = "", is_last: bool = True):
        """Recursively walk and annotate the tree."""
        name = path.name

        if path.is_dir():
            if not is_important_dir(name):
                return

            # Write directory entry
            connector = "└── " if is_last else "├── "
            dir_ann = _dir_annotation(name)
            lines.append(f"{prefix}{connector}{name}/ {dir_ann}")

            # Get children
            children = sorted(
                [p for p in path.iterdir() if p.is_file() and should_show(p)]
                + [p for p in path.iterdir() if p.is_dir() and is_important_dir(p.name)],
                key=lambda p: (not p.is_dir(), p.name),
            )

            for i, child in enumerate(children):
                child_last = i == len(children) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                walk(child, child_prefix, child_last)

        elif path.is_file():
            connector = "└── " if is_last else "├── "
            ann = _file_annotation(str(path.relative_to(root)))
            lines.append(f"{prefix}{connector}{name} {ann}")

    walk(root)
    return "\n".join(lines)


def _dir_annotation(name: str) -> str:
    """Get annotation for a directory."""
    annotations = {
        "core": "核心模块（音频、检测、识别、打字、调度）",
        "utils": "工具模块（剪贴板、热键监听）",
        "docs": "文档（需求规格 specs、实现文档 impls）",
        "tests": "测试套件（pytest）",
        "assets": "静态资源",
    }
    return annotations.get(name, "")


def _file_annotation(rel_path: str) -> str:
    """Get annotation for a file."""
    # Normalize to forward slashes for cross-platform matching
    normalized = rel_path.replace("\\", "/")
    if normalized in ANNOTATIONS:
        return f"← {ANNOTATIONS[normalized]}"
    return ""


def main():
    parser = ArgumentParser(description="Generate annotated vType directory tree")
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tree_output = generate_tree(root)

    if args.output:
        Path(args.output).write_text(tree_output, encoding="utf-8")
        print(f"Tree snapshot written to {args.output}")
    else:
        print(tree_output)


if __name__ == "__main__":
    main()
