# Huawei LivePhoto Batch Split Tool

[简体中文](../README.md) | English

This project batch-splits Huawei camera LivePhoto files into standalone static photos and motion videos. The split `JPG + MP4` files can later be merged into the Motion Photo standard for playback in Windows Photos, Google Photos, and similar gallery applications.

The GUI is built with `PyQt6` and `PyQt6-Fluent-Widgets`, following a Windows 11 style and staying visually consistent with `merge_live_photo_gui.py` in this repository.

## Features

- **Batch scanning**: Scan the selected folder or all subfolders.
- **Automatic detection**: Detect embedded LivePhoto files, Huawei Cloud downloaded JPG/MP4 pairs, and ordinary static photos.
- **Batch splitting**: Split embedded LivePhoto JPG files into matching `.jpg` and `.mp4` files.
- **Pair organization**: Copy Huawei Cloud downloaded JPG/MP4 pairs into one output folder while preserving folder structure.
- **Conflict handling**: Choose skip or overwrite separately for existing photo and video targets.
- **Chinese / English UI**: GUI strings are separated into `split_huawei_live_photo_translations.py`.
- **Persistent settings**: Language, input/output folders, scan mode, and conflict rules are saved locally.

## Tested Devices

| Platform | Device | Code name | System version | Source |
| --- | --- | --- | --- | --- |
| HarmonyOS | HUAWEI Mate 20 | HMA-AL00 | HarmonyOS 4.0.0.121 | Native LivePhoto JPG file |
| HarmonyOS | HUAWEI nova 5z | SPN-AL00 | HarmonyOS 2.0.0.165 | Native LivePhoto JPG file |
| HarmonyOS NEXT | HUAWEI nova 14 Ultra | MRT-AL10 | HarmonyOS 5 / 6 | Standalone JPG/MP4 files exported by Huawei Cloud or system APIs |

> Standalone photo and video files downloaded from Huawei Cloud for HarmonyOS 5 / 6 captures are supported when they follow the matching JPG/MP4 filename rule.

## Quick Start

### Windows Portable Build

Download the release package, extract it, and run:

```text
SplitHuaweiLivePhotoTool.exe
```

The portable package includes:

- Windows x64 GUI application
- Bundled ExifTool
- SHA256 checksum file

### Run from Source

```powershell
python -m venv .venv
.\.venv\Scripts\activate

pip install PyQt6 PyQt6-Fluent-Widgets PyQt6-Frameless-Window Pillow pyinstaller

python split_huawei_live_photo_gui.py
```

Split a single file or a folder from the command line:

```powershell
python split_huawei_live_photo.py .\sample\HarmonyOS4\Source\IMG_20260515_230101.jpg .\sample\HarmonyOS4\SplitOutput
python split_huawei_live_photo.py .\sample\HarmonyOS4\Source .\sample\HarmonyOS4\SplitOutput
```

## Usage

1. Start `SplitHuaweiLivePhotoTool.exe` or run `python split_huawei_live_photo_gui.py`.
2. Choose the source folder. It can contain embedded Huawei LivePhoto JPG files or Huawei Cloud downloaded JPG/MP4 pairs.
3. Confirm the output folder and choose whether to scan subfolders.
4. Set conflict rules for existing target files.
5. Click **Start batch split**.

Output files are written into the output folder while preserving the source folder structure. Ordinary static photos are marked as skipped and are not copied.

## Build

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

Build output:

```text
dist\SplitHuaweiLivePhotoTool.exe
```

## Project Structure

- `split_huawei_live_photo.py`: command-line and core splitting logic.
- `split_huawei_live_photo_gui.py`: PyQt6 / Fluent GUI.
- `split_huawei_live_photo_translations.py`: Chinese and English GUI strings.
- `merge_live_photo_gui.py`: merge-tool GUI used as the visual reference.
- `merge_live_photo_translations.py`: merge-tool GUI strings.
- `sample/`: test samples.

Local settings path:

```text
%APPDATA%\SplitHuaweiLivePhotoGUI\settings.json
```

## Release Information

Recommended Chinese project name:

```text
华为LivePhoto批量分离工具
```

Recommended English project name:

```text
Huawei LivePhoto Batch Split Tool
```

Recommended project description:

```text
Batch split Huawei and HarmonyOS LivePhoto files, with support for embedded JPG LivePhoto files and Huawei Cloud downloaded JPG/MP4 pairs.
```

Recommended release title:

```text
Huawei LivePhoto Batch Split Tool v1.0.0
```

Recommended release notes:

```markdown
First public release.

Changes:

    Add PyQt6 Fluent GUI for Huawei LivePhoto splitting
    Support Chinese and English UI switching
    Refactor UI translations into a separate module
    Split embedded Huawei / HarmonyOS LivePhoto JPG files
    Organize Huawei Cloud downloaded JPG/MP4 pairs

Assets:

    Windows x64 portable build
    Bundled ExifTool
    SHA256 checksum file included
```

## Push and Release

```powershell
git remote add origin https://github.com/<owner>/huawei-livephoto-batch-split-tool.git
git push -u origin main
git push origin v1.0.0
```

On GitHub Releases, select the `v1.0.0` tag, use the release title and notes above, and upload:

```text
SplitHuaweiLivePhotoTool-1.0.0-20260523-windows-x64-portable.zip
SplitHuaweiLivePhotoTool-1.0.0-20260523-windows-x64-portable.sha256.txt
```

## License

This project is released under the license in `LICENSE`.
