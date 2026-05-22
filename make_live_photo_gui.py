#!/usr/bin/env python3
import os
import struct
import io
import threading
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image

# ==========================================
# 核心合并逻辑
# ==========================================
XMP_IDENTIFIER = b'http://ns.adobe.com/xap/1.0/\x00'


def find_jpeg_end(data: bytes) -> int:
    if data[:2] != b'\xff\xd8':
        raise ValueError("不是有效的 JPEG 文件")
    eoi_positions = []
    pos = 0
    while True:
        pos = data.find(b'\xff\xd9', pos)
        if pos == -1: break
        eoi_positions.append(pos)
        pos += 2
    if not eoi_positions:
        raise ValueError("未找到 JPEG EOI 标记")
    for eoi in reversed(eoi_positions):
        try:
            img = Image.open(io.BytesIO(data[:eoi + 2]))
            img.verify()
            return eoi + 2
        except Exception:
            continue
    return eoi_positions[-1] + 2


def strip_existing_xmp(jpeg_data: bytes) -> bytes:
    if jpeg_data[:2] != b'\xff\xd8':
        raise ValueError("不是有效的 JPEG 文件")
    result = bytearray(jpeg_data[:2])
    pos = 2
    while pos < len(jpeg_data):
        if jpeg_data[pos] != 0xFF:
            result += jpeg_data[pos:]
            break
        marker = jpeg_data[pos:pos + 2]
        if len(marker) < 2:
            result += jpeg_data[pos:]
            break
        marker_code = struct.unpack('>H', marker)[0]
        if marker_code in (0xFFD8, 0xFFD9):
            result += marker
            pos += 2
            continue
        if marker_code == 0xFFDA:
            result += jpeg_data[pos:]
            break
        seg_len = struct.unpack('>H', jpeg_data[pos + 2:pos + 4])[0]
        seg_data = jpeg_data[pos + 4:pos + 2 + seg_len]
        if marker_code == 0xFFE1 and seg_data.startswith(XMP_IDENTIFIER):
            pos += 2 + seg_len
            continue
        result += marker + jpeg_data[pos + 2:pos + 2 + seg_len]
        pos += 2 + seg_len
    return bytes(result)


def build_xmp_app1(mp4_size: int) -> bytes:
    xmp_content = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.1.0-jc003">\n'
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '    <rdf:Description rdf:about=""\n'
        '        xmlns:GCamera="http://ns.google.com/photos/1.0/camera/"\n'
        '        xmlns:Container="http://ns.google.com/photos/1.0/container/"\n'
        '        xmlns:Item="http://ns.google.com/photos/1.0/container/item/"\n'
        '      GCamera:MotionPhoto="1"\n'
        '      GCamera:MotionPhotoVersion="1"\n'
        '      GCamera:MotionPhotoPresentationTimestampUs="-1">\n'
        '      <Container:Directory>\n'
        '        <rdf:Seq>\n'
        '          <rdf:li rdf:parseType="Resource">\n'
        '            <Container:Item\n'
        '              Item:Mime="image/jpeg"\n'
        '              Item:Semantic="Primary"\n'
        '              Item:Length="0"\n'
        '              Item:Padding="0"/>\n'
        '          </rdf:li>\n'
        '          <rdf:li rdf:parseType="Resource">\n'
        '            <Container:Item\n'
        '              Item:Mime="video/mp4"\n'
        '              Item:Semantic="MotionPhoto"\n'
        f'              Item:Length="{mp4_size}"\n'
        '              Item:Padding="0"/>\n'
        '          </rdf:li>\n'
        '        </rdf:Seq>\n'
        '      </Container:Directory>\n'
        '    </rdf:Description>\n'
        '  </rdf:RDF>\n'
        '</x:xmpmeta>'
    )
    payload = XMP_IDENTIFIER + xmp_content.encode('utf-8')
    length = len(payload) + 2
    return b'\xff\xe1' + struct.pack('>H', length) + payload


def make_live_photo(jpg_path: str, mp4_path: str, output_path: str):
    with open(jpg_path, 'rb') as f: jpg_data = f.read()
    with open(mp4_path, 'rb') as f: mp4_data = f.read()

    jpeg_end = find_jpeg_end(jpg_data)
    clean_jpeg = jpg_data[:jpeg_end]
    stripped_jpeg = strip_existing_xmp(clean_jpeg)

    mp4_size = len(mp4_data)
    xmp_segment = build_xmp_app1(mp4_size)

    result = bytearray()
    result += stripped_jpeg[:2]
    result += xmp_segment
    result += stripped_jpeg[2:]
    result += mp4_data

    with open(output_path, 'wb') as f:
        f.write(bytes(result))


# ==========================================
# GUI 界面逻辑
# ==========================================
class LivePhotoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Photos 动态照片批量合成器 (支持子文件夹层级)")
        self.root.geometry("980x700")
        self.root.minsize(850, 550)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        # 选项变量：分离逻辑
        self.include_subdirs = tk.BooleanVar(value=True)
        self.live_exist_action = tk.StringVar(value="skip")  # 实况图：skip/overwrite
        self.static_exist_action = tk.StringVar(value="skip")  # 静态图：skip/overwrite
        self.copy_static = tk.BooleanVar(value=True)

        self.file_list = []
        self.is_processing = False

        self.create_widgets()

    def create_widgets(self):
        # --- 顶部文件夹选择区 ---
        frame_top = tk.Frame(self.root, padx=10, pady=5)
        frame_top.pack(fill=tk.X)

        tk.Label(frame_top, text="源文件夹 (包含 JPG/MP4):").grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Entry(frame_top, textvariable=self.input_dir, width=70, state='readonly').grid(row=0, column=1, padx=5,
                                                                                          pady=5)
        tk.Button(frame_top, text="浏览...", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(frame_top, text="实况图输出目录 (保存合并后):").grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Entry(frame_top, textvariable=self.output_dir, width=70, state='readonly').grid(row=1, column=1, padx=5,
                                                                                           pady=5)
        tk.Button(frame_top, text="浏览...", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # --- 设置选项区 ---
        frame_settings = tk.LabelFrame(self.root, text="处理规则设置", padx=10, pady=5)
        frame_settings.pack(fill=tk.X, padx=10, pady=5)

        # 1. 目录设置
        row1 = tk.Frame(frame_settings)
        row1.pack(fill=tk.X, pady=2)
        tk.Checkbutton(row1, text="扫描所有子文件夹 (输出时保持原有目录结构)",
                       variable=self.include_subdirs, command=self.scan_files).pack(side=tk.LEFT)

        ttk.Separator(frame_settings, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # 2. 实况图规则
        row2 = tk.Frame(frame_settings)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="【实况图】合并目标文件已存在时:").pack(side=tk.LEFT, padx=(0, 5))
        tk.Radiobutton(row2, text="跳过 (忽略)", variable=self.live_exist_action, value="skip").pack(side=tk.LEFT,
                                                                                                     padx=5)
        tk.Radiobutton(row2, text="覆盖 (替换)", variable=self.live_exist_action, value="overwrite").pack(side=tk.LEFT,
                                                                                                          padx=5)

        # 3. 静态图规则
        row3 = tk.Frame(frame_settings)
        row3.pack(fill=tk.X, pady=4)
        tk.Checkbutton(row3, text="将“纯静态图”分离至输出目录同级的 'Static_Photos' 文件夹",
                       variable=self.copy_static, command=self.toggle_static_options).pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(row3, text="纯静态图已存在时:").pack(side=tk.LEFT, padx=(0, 5))
        self.rb_static_skip = tk.Radiobutton(row3, text="跳过 (忽略)", variable=self.static_exist_action, value="skip")
        self.rb_static_skip.pack(side=tk.LEFT, padx=5)
        self.rb_static_over = tk.Radiobutton(row3, text="覆盖 (替换)", variable=self.static_exist_action,
                                             value="overwrite")
        self.rb_static_over.pack(side=tk.LEFT, padx=5)

        # --- 中间表格展示区 ---
        frame_mid = tk.Frame(self.root, padx=10)
        frame_mid.pack(fill=tk.BOTH, expand=True, pady=5)

        scroll_y = ttk.Scrollbar(frame_mid)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("FilePath", "HasMP4", "Status")
        self.tree = ttk.Treeview(frame_mid, columns=columns, show="headings", yscrollcommand=scroll_y.set)
        self.tree.heading("FilePath", text="图片相对路径 (JPG)")
        self.tree.heading("HasMP4", text="匹配到同名视频")
        self.tree.heading("Status", text="当前状态")

        self.tree.column("FilePath", width=420, anchor=tk.W)
        self.tree.column("HasMP4", width=120, anchor=tk.CENTER)
        self.tree.column("Status", width=250, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree.yview)

        # --- 底部控制与进度区 ---
        frame_bottom = tk.Frame(self.root, padx=10, pady=10)
        frame_bottom.pack(fill=tk.X)

        self.btn_start = tk.Button(frame_bottom, text="开始批量合成", bg="#4CAF50", fg="black",
                                   font=("Arial", 12, "bold"), command=self.start_processing)
        self.btn_start.pack(side=tk.RIGHT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame_bottom, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))

        self.lbl_status = tk.Label(frame_bottom, text="等待导入文件夹...")
        self.lbl_status.pack(side=tk.LEFT)

    def toggle_static_options(self):
        """如果取消分离静态图，则禁用后面的单选框"""
        state = tk.NORMAL if self.copy_static.get() else tk.DISABLED
        self.rb_static_skip.config(state=state)
        self.rb_static_over.config(state=state)

    def browse_input(self):
        folder = filedialog.askdirectory(title="选择包含 JPG 和 MP4 的源文件夹")
        if folder:
            self.input_dir.set(folder)
            self.scan_files()
            # 默认自动设置一个输出文件夹
            default_out = Path(folder) / "LivePhotos_Output"
            self.output_dir.set(str(default_out))

    def browse_output(self):
        folder = filedialog.askdirectory(title="选择实况图输出文件夹")
        if folder:
            self.output_dir.set(folder)

    def scan_files(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_list.clear()

        in_path_str = self.input_dir.get()
        if not in_path_str:
            return

        in_path = Path(in_path_str)
        if not in_path.is_dir():
            return

        is_recursive = self.include_subdirs.get()

        jpg_files_set = set()
        for ext in ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG'):
            if is_recursive:
                jpg_files_set.update(in_path.rglob(ext))
            else:
                jpg_files_set.update(in_path.glob(ext))

        jpg_files = sorted(list(jpg_files_set))

        if not jpg_files:
            messagebox.showinfo("提示", "所选文件夹中未找到 JPG/JPEG 图片。")
            return

        for jpg_path in jpg_files:
            mp4_path = jpg_path.with_suffix('.mp4')
            if not mp4_path.exists():
                mp4_path = jpg_path.with_suffix('.MP4')

            has_mp4 = "✅ 是" if mp4_path.exists() else "❌ 否"
            status = "等待处理"

            try:
                rel_path = jpg_path.relative_to(in_path)
            except ValueError:
                rel_path = jpg_path.name

            item_id = self.tree.insert("", tk.END, values=(str(rel_path), has_mp4, status))
            self.file_list.append({
                "item_id": item_id,
                "jpg_path": jpg_path,
                "mp4_path": mp4_path if mp4_path.exists() else None,
                "rel_path": rel_path
            })

        self.lbl_status.config(text=f"共扫描到 {len(self.file_list)} 张照片，准备就绪。")

    def update_ui_status(self, item_id, status_text, progress_value=None, label_text=None):
        self.tree.set(item_id, "Status", status_text)
        if progress_value is not None:
            self.progress_var.set(progress_value)
        if label_text is not None:
            self.lbl_status.config(text=label_text)
        self.tree.see(item_id)

    def start_processing(self):
        if self.is_processing: return
        if not self.file_list:
            messagebox.showwarning("警告", "列表中没有可处理的文件！")
            return

        in_dir = self.input_dir.get()
        out_dir = self.output_dir.get()

        if not in_dir or not out_dir:
            messagebox.showwarning("警告", "请先选择源文件夹和输出文件夹！")
            return

        if Path(in_dir).resolve() == Path(out_dir).resolve():
            msg = "输入和输出文件夹相同，合成操作将【直接覆盖】原始 JPG 照片！\n\n是否确认覆盖？(建议选否，另建输出文件夹)"
            if not messagebox.askyesno("风险提示", msg):
                return

        self.is_processing = True
        self.btn_start.config(state=tk.DISABLED, text="处理中...")

        thread = threading.Thread(target=self.process_files_thread, args=(in_dir, out_dir))
        thread.daemon = True
        thread.start()

    def process_files_thread(self, in_dir, out_dir):
        in_path = Path(in_dir)
        out_path = Path(out_dir)

        # 静态文件夹放在实况输出文件夹同级
        if out_path.parent == out_path:
            static_out_path = out_path / "Static_Photos"
        else:
            static_out_path = out_path.parent / "Static_Photos"

        if self.copy_static.get():
            static_out_path.mkdir(parents=True, exist_ok=True)

        total = len(self.file_list)
        success_count = 0
        live_exist_skip_count = 0  # 实况图跳过统计
        static_copy_count = 0  # 静态图成功复制统计
        static_exist_skip_count = 0  # 静态图跳过统计
        fail_count = 0

        for i, task in enumerate(self.file_list):
            item_id = task["item_id"]
            jpg_path = task["jpg_path"]
            mp4_path = task["mp4_path"]
            rel_path = task["rel_path"]

            progress_percent = ((i + 1) / total) * 100

            # 【情况 1】没有对应的视频（静态照片）
            if mp4_path is None:
                if self.copy_static.get():
                    try:
                        target_static_file = static_out_path / rel_path
                        target_static_file.parent.mkdir(parents=True, exist_ok=True)

                        # 使用静态图独立的冲突规则
                        if target_static_file.exists():
                            if self.static_exist_action.get() == "skip":
                                static_exist_skip_count += 1
                                self.root.after(0, self.update_ui_status, item_id, "⏭️ 跳过 (静态目录已存在)",
                                                progress_percent, f"进度: {i + 1}/{total}")
                                continue

                        shutil.copy2(jpg_path, target_static_file)
                        static_copy_count += 1
                        self.root.after(0, self.update_ui_status, item_id, "📁 分离成功 (已复制到静态目录)",
                                        progress_percent, f"进度: {i + 1}/{total}")
                    except Exception as e:
                        self.root.after(0, self.update_ui_status, item_id, f"❌ 分离失败: {str(e)[:15]}",
                                        progress_percent)
                else:
                    self.root.after(0, self.update_ui_status, item_id, "⏭️ 跳过 (无视频, 未开启分离)", progress_percent,
                                    f"进度: {i + 1}/{total}")
                continue

            # 【情况 2&3】有对应的视频，处理实况照片
            output_file = out_path / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 使用实况图独立的冲突规则
            if output_file.exists():
                if self.live_exist_action.get() == "skip":
                    live_exist_skip_count += 1
                    self.root.after(0, self.update_ui_status, item_id, "⏭️ 跳过 (实况目录已存在)", progress_percent,
                                    f"进度: {i + 1}/{total}")
                    continue

            # 正常合成
            self.root.after(0, self.update_ui_status, item_id, "⏳ 合并中...", progress_percent, f"正在处理: {rel_path}")

            try:
                make_live_photo(str(jpg_path), str(mp4_path), str(output_file))
                success_count += 1
                self.root.after(0, self.update_ui_status, item_id, "✅ 合成成功", progress_percent)
            except Exception as e:
                fail_count += 1
                self.root.after(0, self.update_ui_status, item_id, f"❌ 失败: {str(e)[:20]}", progress_percent)

        # 结束汇报弹窗
        def finish():
            self.progress_var.set(100)
            self.lbl_status.config(
                text=f"任务完成！实况成功: {success_count} | 实况跳过: {live_exist_skip_count} | 静态分离: {static_copy_count} | 静态跳过: {static_exist_skip_count}")
            self.btn_start.config(state=tk.NORMAL, text="开始批量合成")
            self.is_processing = False

            msg = (
                f"任务结束！数据统计：\n\n"
                f"【实况照片】\n"
                f"✅ 成功合成: {success_count} 个\n"
                f"⏭️ 因已存在而跳过: {live_exist_skip_count} 个\n\n"
            )
            if self.copy_static.get():
                msg += (
                    f"【纯静态照片】\n"
                    f"📁 成功分离复制: {static_copy_count} 个\n"
                    f"⏭️ 因已存在而跳过: {static_exist_skip_count} 个\n\n"
                )

            msg += f"❌ 处理失败: {fail_count} 个\n\n实况图输出至:\n{out_path}"

            messagebox.showinfo("处理完成", msg)

        self.root.after(0, finish)


if __name__ == '__main__':
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview", rowheight=25, font=('Arial', 10))
    style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

    app = LivePhotoGUI(root)
    root.mainloop()