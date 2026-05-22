# Huawei Live Photo Split Tool

华为 / 鸿蒙 Live Photo 批量分离工具。用于将华为手机拍摄或华为云下载的动态照片整理为独立的静态照片与动态视频文件。

简体中文 | English UI supported

## 项目描述

Huawei Live Photo Split Tool 是一个面向 Windows 的图形化批处理工具，基于 `PyQt6` 与 `PyQt6-Fluent-Widgets` 构建，界面风格与本仓库中的 `merge_live_photo_gui.py` 保持一致。

工具支持两类输入：

- **内嵌式华为 Live Photo**：例如 HarmonyOS 4 机型导出的单个 JPG 文件，文件内部包含 JPEG 数据、MP4 视频数据与 `LIVE_` 尾部元数据。
- **华为云独立文件**：华为云服务下载后已经拆成同名 `JPG + MP4` 的动态照片文件。此类素材会被识别并整理到统一输出目录，因此 HarmonyOS 5 / 6 拍摄、经华为云下载后已经独立保存的照片也支持分离整理。

## 核心特性

- **批量扫描**：支持扫描当前目录或所有子目录。
- **自动识别**：自动区分内嵌 Live Photo、华为云同名 JPG/MP4 独立文件、普通静态照片。
- **批量分离**：内嵌 Live Photo 会被拆分为同名 `.jpg` 与 `.mp4`。
- **独立文件整理**：已分离的华为云 JPG/MP4 会被复制到统一输出目录并保留目录层级。
- **冲突策略**：照片和视频目标已存在时可分别选择跳过或覆盖。
- **中英文切换**：GUI 文案已分离到 `split_huawei_live_photo_translations.py`。
- **配置记忆**：语言、输入输出目录、扫描规则、冲突策略会保存到本地配置。

## 已测试设备

| 平台 | 设备 | 代号 | 系统版本 | 来源 | 结果 |
| --- | --- | --- | --- | --- | --- |
| HarmonyOS | HUAWEI Mate 20 | HMA-AL00 | HarmonyOS 4.0.0.121 | 本机 Live Photo JPG | 支持内嵌分离 |
| HarmonyOS | HUAWEI Mate 20 | HMA-AL00 | HarmonyOS 4.0.0.121 | 华为云服务下载 JPG/MP4 | 支持独立文件整理 |
| HarmonyOS NEXT | 华为机型 | - | HarmonyOS 5 / 6 | 华为云服务下载 JPG/MP4 | 按同名独立文件格式支持 |

## 快速开始

### Windows 便携版

下载 release 中的便携包，解压后运行：

```text
SplitHuaweiLivePhotoTool.exe
```

便携包包含：

- Windows x64 GUI 程序
- `ExifTool` 目录
- SHA256 校验文件

### 源码运行

```powershell
python -m venv .venv
.\.venv\Scripts\activate

pip install PyQt6 PyQt6-Fluent-Widgets PyQt6-Frameless-Window Pillow pyinstaller

python split_huawei_live_photo_gui.py
```

命令行分离单个文件或目录：

```powershell
python split_huawei_live_photo.py .\sample\HarmonyOS4\IMG_20260515_230101.jpg .\sample\HarmonyOS4\Split_Output
python split_huawei_live_photo.py .\sample\HarmonyOS4 .\sample\HarmonyOS4\Split_Output
```

## 使用说明

1. 启动 `SplitHuaweiLivePhotoTool.exe` 或运行 `python split_huawei_live_photo_gui.py`。
2. 选择源文件夹。源文件夹可以包含内嵌华为 Live Photo JPG，也可以包含华为云下载后的同名 JPG/MP4。
3. 确认输出目录，按需选择是否扫描子目录。
4. 设置目标文件已存在时的处理策略。
5. 点击 **开始批量分离**。

输出文件会按源目录层级写入输出目录。普通静态照片只会标记为跳过，不会复制到输出目录。

## 项目结构

- `split_huawei_live_photo.py`：命令行与核心分离逻辑。
- `split_huawei_live_photo_gui.py`：PyQt6 / Fluent GUI。
- `split_huawei_live_photo_translations.py`：拆分工具中英文 UI 文案。
- `merge_live_photo_gui.py`：合成工具 GUI，可作为界面风格参考。
- `merge_live_photo_translations.py`：合成工具中英文 UI 文案。
- `sample/`：测试样例。

本地配置保存位置：

```text
%APPDATA%\SplitHuaweiLivePhotoGUI\settings.json
```

## 打包构建

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name SplitHuaweiLivePhotoTool `
  --collect-all qfluentwidgets `
  --collect-all qframelesswindow `
  --exclude-module PyQt6.QtNetwork `
  --exclude-module PyQt6.QtOpenGL `
  --exclude-module PyQt6.QtQml `
  --exclude-module PyQt6.QtQuick `
  --exclude-module PyQt6.QtSql `
  --exclude-module PyQt6.QtTest `
  --exclude-module PyQt6.QtWebEngineCore `
  --exclude-module PyQt6.QtWebEngineWidgets `
  .\split_huawei_live_photo_gui.py
```

构建产物：

```text
dist\SplitHuaweiLivePhotoTool.exe
```

## Release 命名规范

推荐项目名：

```text
Huawei Live Photo Split Tool
```

推荐仓库名：

```text
huawei-live-photo-split-tool
```

推荐项目简介：

```text
Batch split Huawei and HarmonyOS Live Photos into standalone JPG and MP4 files, with support for Huawei Cloud downloaded JPG/MP4 pairs.
```

推荐标签：

```text
v1.0.0
```

推荐 release 标题：

```text
Huawei Live Photo Split Tool v1.0.0
```

推荐 release 描述：

```markdown
First public release.

Changes:

    Add PyQt6 Fluent GUI for Huawei Live Photo splitting
    Support Chinese and English UI switching
    Refactor UI translations into a separate module
    Split embedded Huawei / HarmonyOS Live Photo JPG files
    Organize Huawei Cloud downloaded JPG/MP4 pairs

Assets:

    Windows x64 portable build
    Bundled ExifTool
    SHA256 checksum file included
```

## Push 与 Release 流程

首次创建远程仓库后：

```powershell
git remote add origin https://github.com/<owner>/huawei-live-photo-split-tool.git
git branch -M main
git push -u origin main
```

创建 release 标签并推送：

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

在 GitHub Release 页面选择 `v1.0.0` 标签，填写上面的 release 标题和描述，并上传：

```text
SplitHuaweiLivePhotoTool-1.0.0-20260523-windows-x64-portable.zip
SplitHuaweiLivePhotoTool-1.0.0-20260523-windows-x64-portable.sha256.txt
```

## 开源协议

本项目基于仓库中的 `LICENSE` 文件发布。
