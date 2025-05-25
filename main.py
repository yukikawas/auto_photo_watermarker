import sys
import os
import datetime
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog,
                             QComboBox, QSpinBox, QDateTimeEdit, QGroupBox,
                             QScrollArea, QMessageBox, QTextEdit)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QDateTime

from PIL import Image, ImageDraw, ImageFont

# --- Core Watermarking Function with New Modern Style ---
def apply_modern_watermark(
        image_path,
        output_path,
        title_text, # New: Custom title
        location_text,
        timestamp_dt,
        anchor="bottom_right",
        padding=(10, 10),
        font_path="arial.ttf",
        base_font_size=20, # Base size for time/location
        log_callback=print
):
    try:
        img = Image.open(image_path).convert("RGBA")
        img_width, img_height = img.size

        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # --- Style Colors ---
        COLOR_BLUE_BAR_BG = (20, 120, 220, 255)  # Opaque Blue
        COLOR_TITLE_TEXT = (255, 255, 255, 255) # White
        COLOR_TIME_TEXT = (240, 240, 240, 255)  # Slightly off-white
        COLOR_WHITE_BAR_BG = (255, 255, 255, 128) # 50% Transparent White
        COLOR_LOCATION_TEXT = (0, 0, 0, 255)    # Black

        # --- Fonts ---
        try:
            base_font = ImageFont.truetype(font_path, base_font_size)
            title_font_size = int(base_font_size * 1.4) # Title font is larger
            title_font = ImageFont.truetype(font_path, title_font_size)
        except IOError:
            log_callback(f"警告: 字体 '{font_path}' 未找到, 使用默认字体。")
            base_font = ImageFont.load_default()
            title_font = ImageFont.load_default() # Fallback for title too

        # --- Text Content ---
        time_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

        # --- Helper to get text dimensions ---
        def get_text_size(text, font_obj, context_draw=draw):
            if not text: return 0,0 # Handle empty strings
            if hasattr(context_draw, 'textbbox'):
                try: # Pillow 9.0.0+ textbbox takes xy, older versions don't
                    bbox = context_draw.textbbox((0,0), text, font=font_obj)
                except TypeError: # Older Pillow, try without xy
                    bbox = context_draw.textbbox(text, font=font_obj)

                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:
                return context_draw.textsize(text, font=font_obj)

        # --- Calculate Text Dimensions ---
        title_w, title_h = get_text_size(title_text, title_font)
        time_w, time_h = get_text_size(time_str, base_font)
        location_w, location_h = get_text_size(location_text, base_font)

        # --- Define Internal Paddings & Spacings (relative to base_font_size for scalability) ---
        h_padding_inside_bars = int(base_font_size * 0.6)
        v_padding_bar_ends = int(base_font_size * 0.3) # Top of title bar, bottom of location bar
        v_padding_title_time = int(base_font_size * 0.15) # Between title and time

        # --- Calculate Dimensions of Each Bar ---
        # Blue (Top) Bar
        blue_bar_content_h = title_h + (v_padding_title_time if title_text and time_str else 0) + time_h
        blue_bar_total_h = (v_padding_bar_ends * 2) + blue_bar_content_h + 10
        blue_bar_width = max(title_w, time_w) + (h_padding_inside_bars * 2)

        # White (Bottom) Bar
        white_bar_content_h = location_h
        white_bar_total_h = (v_padding_bar_ends * 10) + white_bar_content_h
        white_bar_width = location_w + (h_padding_inside_bars * 2)

        # Overall Watermark Block Dimensions
        watermark_block_width = max(blue_bar_width, white_bar_width)
        watermark_block_height = blue_bar_total_h + white_bar_total_h # Bars are stacked directly

        # --- Calculate Overall (final_x, final_y) for the top-left of the watermark block ---
        # This uses the anchor and padding parameters for the entire block
        pad_x_abs, pad_y_abs = padding

        if anchor == "top_left": final_x, final_y = pad_x_abs, pad_y_abs
        elif anchor == "top_center": final_x, final_y = (img_width - watermark_block_width) // 2, pad_y_abs
        elif anchor == "top_right": final_x, final_y = img_width - watermark_block_width - pad_x_abs, pad_y_abs
        elif anchor == "middle_left": final_x, final_y = pad_x_abs, (img_height - watermark_block_height) // 2
        elif anchor == "middle_center": final_x, final_y = (img_width - watermark_block_width) // 2, (img_height - watermark_block_height) // 2
        elif anchor == "middle_right": final_x, final_y = img_width - watermark_block_width - pad_x_abs, (img_height - watermark_block_height) // 2
        elif anchor == "bottom_left": final_x, final_y = pad_x_abs, img_height - watermark_block_height - pad_y_abs
        elif anchor == "bottom_center": final_x, final_y = (img_width - watermark_block_width) // 2, img_height - watermark_block_height - pad_y_abs
        else:  # Default bottom_right
            anchor = "bottom_right"
            final_x, final_y = img_width - watermark_block_width - pad_x_abs, img_height - watermark_block_height - pad_y_abs

        final_x = max(0, int(final_x))
        final_y = max(0, int(final_y))

        # --- Draw Elements ---
        current_y_offset = final_y

        # 1. Blue Bar (Top)
        draw.rectangle(
            [final_x, current_y_offset, final_x + watermark_block_width, current_y_offset + blue_bar_total_h],
            fill=COLOR_BLUE_BAR_BG
        )
        # Title Text
        if title_text:
            draw.text(
                (final_x + h_padding_inside_bars, current_y_offset + v_padding_bar_ends),
                title_text, font=title_font, fill=COLOR_TITLE_TEXT
            )
        # Timestamp Text (below title)
        if time_str:
            time_y_pos = current_y_offset + v_padding_bar_ends + (title_h + v_padding_title_time if title_text else 0)
            draw.text(
                (final_x + h_padding_inside_bars, time_y_pos),
                time_str, font=base_font, fill=COLOR_TIME_TEXT
            )
        current_y_offset += blue_bar_total_h

        # 2. White Transparent Bar (Bottom)
        draw.rectangle(
            [final_x, current_y_offset, final_x + watermark_block_width, current_y_offset + white_bar_total_h],
            fill=COLOR_WHITE_BAR_BG
        )
        # Location Text
        if location_text:
            draw.text(
                (final_x + h_padding_inside_bars, current_y_offset + v_padding_bar_ends),
                location_text, font=base_font, fill=COLOR_LOCATION_TEXT
            )

        # --- Composite and Save ---
        watermarked_img = Image.alpha_composite(img, txt_layer)
        if img.mode != 'RGBA' or output_path.lower().endswith(('.jpg', '.jpeg')):
            watermarked_img = watermarked_img.convert("RGB")
        watermarked_img.save(output_path)
        log_callback(f"现代样式水印已添加到: {output_path} (锚点: {anchor}, 坐标: ({final_x},{final_y}))")
        return True

    except Exception as e:
        import traceback
        log_callback(f"处理图片 {image_path} 时出错: {e}\n{traceback.format_exc()}")
        return False

# --- PyQt Application ---
class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.current_pil_image = None
        self.preview_pil_image = None
        self.output_folder = None
        self.input_folder = None
        self.log_messages = []

        self.initUI()

    def log_message(self, message):
        print(message)
        self.log_messages.append(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}")
        if hasattr(self, 'log_output_area'):
            self.log_output_area.setPlainText("\n".join(self.log_messages[-100:]))
            self.log_output_area.verticalScrollBar().setValue(self.log_output_area.verticalScrollBar().maximum())

    def initUI(self):
        self.setWindowTitle('照片批量加水印工具 V4')
        self.setGeometry(100, 100, 1100, 850) # Increased height for new field & log

        main_layout = QVBoxLayout()
        top_h_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()

        # --- Left Panel: Controls ---
        # 1. File Selection (Same as before)
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout()
        self.btn_load_single = QPushButton("选择单张图片")
        self.btn_load_single.clicked.connect(self.load_single_image)
        self.lbl_single_file = QLabel("未选择图片")
        self.lbl_single_file.setWordWrap(True)
        file_layout.addWidget(self.btn_load_single); file_layout.addWidget(self.lbl_single_file)
        self.btn_input_folder = QPushButton("选择图片文件夹 (批量)")
        self.btn_input_folder.clicked.connect(self.select_input_folder)
        self.lbl_input_folder = QLabel("未选择输入文件夹")
        self.lbl_input_folder.setWordWrap(True)
        file_layout.addWidget(self.btn_input_folder); file_layout.addWidget(self.lbl_input_folder)
        self.btn_output_folder = QPushButton("选择输出文件夹")
        self.btn_output_folder.clicked.connect(self.select_output_folder)
        self.lbl_output_folder = QLabel("未选择输出文件夹")
        self.lbl_output_folder.setWordWrap(True)
        file_layout.addWidget(self.btn_output_folder); file_layout.addWidget(self.lbl_output_folder)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)

        # 2. Watermark Content (Updated for Title Text)
        content_group = QGroupBox("水印内容")
        content_layout = QVBoxLayout()

        content_layout.addWidget(QLabel("标题文字:"))
        self.edit_title_text = QTextEdit("施工记录") # New field
        content_layout.addWidget(self.edit_title_text)

        content_layout.addWidget(QLabel("拍摄地点:"))
        self.edit_location = QTextEdit("")
        content_layout.addWidget(self.edit_location)

        content_layout.addWidget(QLabel("起始拍摄时间:"))
        self.edit_start_time = QDateTimeEdit(QDateTime.currentDateTime())
        self.edit_start_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        content_layout.addWidget(self.edit_start_time)
        content_group.setLayout(content_layout)
        left_panel.addWidget(content_group)

        # 3. Watermark Style & Relative Position (Font size now 'Base Font Size')
        style_group = QGroupBox("水印样式与相对位置")
        style_layout = QVBoxLayout()
        anchor_layout = QHBoxLayout()
        lbl_anchor = QLabel("水印锚点:")
        self.combo_anchor = QComboBox()
        self.anchor_map_ui_to_code = {
            "右下角": "bottom_right", "左下角": "bottom_left", "中下部": "bottom_center",
            "右上角": "top_right", "左上角": "top_left", "中上部": "top_center",
            "右中部": "middle_right", "左中部": "middle_left", "正中间": "middle_center"
        }
        self.combo_anchor.addItems(self.anchor_map_ui_to_code.keys())
        self.combo_anchor.setCurrentText("左下角")
        anchor_layout.addWidget(lbl_anchor); anchor_layout.addWidget(self.combo_anchor)
        style_layout.addLayout(anchor_layout)

        padding_layout = QHBoxLayout()
        lbl_padding_x = QLabel("整体水平边距(X):")
        self.spin_padding_x = QSpinBox(); self.spin_padding_x.setRange(0, 1000); self.spin_padding_x.setValue(30)
        lbl_padding_y = QLabel("整体垂直边距(Y):")
        self.spin_padding_y = QSpinBox(); self.spin_padding_y.setRange(0, 1000); self.spin_padding_y.setValue(30)
        padding_layout.addWidget(lbl_padding_x); padding_layout.addWidget(self.spin_padding_x)
        padding_layout.addWidget(lbl_padding_y); padding_layout.addWidget(self.spin_padding_y)
        style_layout.addLayout(padding_layout)

        font_size_layout = QHBoxLayout()
        lbl_font_size = QLabel("基础字体大小 (时间/地点):") # Label changed
        self.spin_base_font_size = QSpinBox() # Renamed variable
        self.spin_base_font_size.setRange(8, 128); self.spin_base_font_size.setValue(40)
        font_size_layout.addWidget(lbl_font_size); font_size_layout.addWidget(self.spin_base_font_size)
        style_layout.addLayout(font_size_layout)
        style_group.setLayout(style_layout)
        left_panel.addWidget(style_group)

        # 4. Batch Processing Settings (Same as before)
        batch_group = QGroupBox("批量处理设置")
        batch_layout = QVBoxLayout()
        lbl_time_increment = QLabel("时间递增:")
        self.combo_time_increment = QComboBox()
        self.combo_time_increment.addItems(["递增1分钟", "无递增" , "递增2分钟", "递增5分钟", "递增10分钟", "随机(1-5分钟)"])
        batch_layout.addWidget(lbl_time_increment); batch_layout.addWidget(self.combo_time_increment)
        batch_group.setLayout(batch_layout)
        left_panel.addWidget(batch_group)

        # 5. Actions (Same as before)
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout()
        self.btn_preview = QPushButton("刷新预览")
        self.btn_preview.clicked.connect(self.update_preview)
        action_layout.addWidget(self.btn_preview)
        self.btn_apply_single = QPushButton("应用到单张图片并保存")
        self.btn_apply_single.clicked.connect(self.process_single_image)
        action_layout.addWidget(self.btn_apply_single)
        self.btn_process_batch = QPushButton("开始批量处理")
        self.btn_process_batch.clicked.connect(self.process_batch_images)
        action_layout.addWidget(self.btn_process_batch)
        action_group.setLayout(action_layout)
        left_panel.addWidget(action_group)
        left_panel.addStretch(1)

        # --- Right Panel: Preview (Same as before) ---
        self.lbl_preview = QLabel("图片预览区域")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setMinimumSize(400, 300)
        self.lbl_preview.setStyleSheet("border: 1px solid gray;")
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setWidget(self.lbl_preview)
        right_panel.addWidget(scroll_area)

        top_h_layout.addLayout(left_panel, 1)
        top_h_layout.addLayout(right_panel, 2)
        main_layout.addLayout(top_h_layout)

        # --- Log Output Area (Same as before) ---
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output_area = QTextEdit(); self.log_output_area.setReadOnly(True); self.log_output_area.setFixedHeight(150)
        log_layout.addWidget(self.log_output_area)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        self.setLayout(main_layout)
        self.show()
        self.log_message("应用程序已启动。现代水印样式 V4。")

    def _pil_to_qpixmap(self, pil_image): # Same as before
        if pil_image is None: return QPixmap()
        if pil_image.mode != "RGBA": pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def load_single_image(self): # Same as before
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "选择单张图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)", options=options)
        if filePath:
            self.current_image_path = filePath
            self.lbl_single_file.setText(os.path.basename(filePath))
            try:
                self.current_pil_image = Image.open(filePath)
                self.log_message(f"已加载图片: {filePath}")
                self.update_preview()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法加载图片: {e}")
                self.log_message(f"加载图片失败: {filePath} - {e}")
                self.current_image_path = None; self.current_pil_image = None
                self.lbl_single_file.setText("未选择图片"); self.lbl_preview.clear(); self.lbl_preview.setText("图片加载失败")

    def select_input_folder(self): # Same as before
        folderPath = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folderPath: self.input_folder = folderPath; self.lbl_input_folder.setText(folderPath); self.log_message(f"输入文件夹已选择: {folderPath}")

    def select_output_folder(self): # Same as before
        folderPath = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folderPath: self.output_folder = folderPath; self.lbl_output_folder.setText(folderPath); self.log_message(f"输出文件夹已选择: {folderPath}")

    def _get_font_path(self): # Same as before (using sys._MEIPASS for bundled apps)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        bundled_font_paths = [os.path.join(base_path, "msyh.ttc"), os.path.join(base_path, "arial.ttf")]
        for font_path in bundled_font_paths:
            if os.path.exists(font_path):
                try: ImageFont.truetype(font_path, 10); return font_path
                except IOError: self.log_message(f"捆绑字体 {font_path} 存在但加载失败。")

        if os.name == 'nt':
            system_font_paths = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/arialuni.ttf", "C:/Windows/Fonts/arial.ttf"]
            for font_path in system_font_paths:
                if os.path.exists(font_path):
                    try: ImageFont.truetype(font_path, 10); return font_path
                    except IOError: continue
        # Add more OS-specific font paths if needed for Linux/macOS packaging
        self.log_message("警告: 未找到合适的字体，将回退到Pillow的默认字体。")
        return "arial.ttf" # Default fallback

    def _get_watermark_params_from_ui(self, current_dt_override=None):
        title_text = self.edit_title_text.toPlainText() # New
        location_text = self.edit_location.toPlainText()
        timestamp_dt = current_dt_override if current_dt_override else self.edit_start_time.dateTime().toPyDateTime()

        anchor_ui = self.combo_anchor.currentText()
        anchor = self.anchor_map_ui_to_code.get(anchor_ui, "bottom_right")

        padding = (self.spin_padding_x.value(), self.spin_padding_y.value())
        base_font_size = self.spin_base_font_size.value() # Updated
        font_path = self._get_font_path()

        return title_text, location_text, timestamp_dt, anchor, padding, font_path, base_font_size

    def _apply_watermark_to_pil_image_for_preview(self, pil_img, title_text, location_text, timestamp_dt, anchor, padding, font_path, base_font_size):
        # This function should essentially mirror `apply_modern_watermark` but on a PIL image copy
        # For brevity, the logic is very similar to apply_modern_watermark.
        # Key difference: operates on pil_img directly (a copy) and returns a PIL image.
        if pil_img is None: return None

        img_copy = pil_img.copy().convert("RGBA")
        # The drawing logic from apply_modern_watermark would be replicated here,
        # drawing onto a txt_layer derived from img_copy.size, then compositing.
        # For this response length, assume it's a call to a helper or direct replication:

        # Replicating essential parts of apply_modern_watermark for preview:
        txt_layer = Image.new("RGBA", img_copy.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        COLOR_BLUE_BAR_BG = (20, 120, 220, 255)
        COLOR_TITLE_TEXT = (255, 255, 255, 255)
        COLOR_TIME_TEXT = (240, 240, 240, 255)
        COLOR_WHITE_BAR_BG = (255, 255, 255, 128)
        COLOR_LOCATION_TEXT = (0, 0, 0, 255)

        try:
            base_font = ImageFont.truetype(font_path, base_font_size)
            title_font_size = int(base_font_size * 1.4)
            title_font = ImageFont.truetype(font_path, title_font_size)
        except IOError:
            base_font = ImageFont.load_default(); title_font = ImageFont.load_default()

        time_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

        def get_text_size(text, font_obj, context_draw=draw):
            if not text: return 0,0
            if hasattr(context_draw, 'textbbox'):
                try: bbox = context_draw.textbbox((0,0), text, font=font_obj)
                except TypeError: bbox = context_draw.textbbox(text, font=font_obj)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            else: return context_draw.textsize(text, font=font_obj)

        title_w, title_h = get_text_size(title_text, title_font)
        time_w, time_h = get_text_size(time_str, base_font)
        location_w, location_h = get_text_size(location_text, base_font)

        h_padding_inside_bars = int(base_font_size * 0.6)
        v_padding_bar_ends = int(base_font_size * 0.3)
        v_padding_title_time = int(base_font_size * 0.15)

        blue_bar_content_h = title_h + (v_padding_title_time if title_text and time_str else 0) + time_h
        blue_bar_total_h = (v_padding_bar_ends * 2) + blue_bar_content_h + 11
        blue_bar_width = max(title_w, time_w) + (h_padding_inside_bars * 2)

        white_bar_content_h = location_h
        white_bar_total_h = (v_padding_bar_ends * 10) + white_bar_content_h
        white_bar_width = location_w + (h_padding_inside_bars * 2)

        watermark_block_width = max(blue_bar_width, white_bar_width)
        watermark_block_height = blue_bar_total_h + white_bar_total_h

        pad_x_abs, pad_y_abs = padding
        img_width, img_height = img_copy.size

        if anchor == "top_left": final_x, final_y = pad_x_abs, pad_y_abs
        elif anchor == "top_center": final_x, final_y = (img_width - watermark_block_width) // 2, pad_y_abs
        elif anchor == "top_right": final_x, final_y = img_width - watermark_block_width - pad_x_abs, pad_y_abs
        elif anchor == "middle_left": final_x, final_y = pad_x_abs, (img_height - watermark_block_height) // 2
        elif anchor == "middle_center": final_x, final_y = (img_width - watermark_block_width) // 2, (img_height - watermark_block_height) // 2
        elif anchor == "middle_right": final_x, final_y = img_width - watermark_block_width - pad_x_abs, (img_height - watermark_block_height) // 2
        elif anchor == "bottom_left": final_x, final_y = pad_x_abs, img_height - watermark_block_height - pad_y_abs
        elif anchor == "bottom_center": final_x, final_y = (img_width - watermark_block_width) // 2, img_height - watermark_block_height - pad_y_abs
        else: final_x, final_y = img_width - watermark_block_width - pad_x_abs, img_height - watermark_block_height - pad_y_abs
        final_x = max(0, int(final_x)); final_y = max(0, int(final_y))

        current_y_offset = final_y
        draw.rectangle([final_x, current_y_offset, final_x + watermark_block_width, current_y_offset + blue_bar_total_h], fill=COLOR_BLUE_BAR_BG)
        if title_text: draw.text((final_x + h_padding_inside_bars, current_y_offset + v_padding_bar_ends), title_text, font=title_font, fill=COLOR_TITLE_TEXT)
        if time_str:
            time_y_pos = current_y_offset + v_padding_bar_ends + (title_h + v_padding_title_time if title_text else 0)
            draw.text((final_x + h_padding_inside_bars, time_y_pos), time_str, font=base_font, fill=COLOR_TIME_TEXT)
        current_y_offset += blue_bar_total_h
        draw.rectangle([final_x, current_y_offset, final_x + watermark_block_width, current_y_offset + white_bar_total_h], fill=COLOR_WHITE_BAR_BG)
        if location_text: draw.text((final_x + h_padding_inside_bars, current_y_offset + v_padding_bar_ends), location_text, font=base_font, fill=COLOR_LOCATION_TEXT)

        return Image.alpha_composite(img_copy, txt_layer)


    def update_preview(self): # Updated to pass new params
        if self.current_pil_image is None:
            if self.current_image_path:
                try: self.current_pil_image = Image.open(self.current_image_path)
                except Exception as e: self.log_message(f"预览失败，无法重新加载图片: {e}"); self.lbl_preview.setText("预览失败"); return
            else: self.lbl_preview.setText("请先加载一张图片以预览"); return

        params = self._get_watermark_params_from_ui() # title, location, timestamp, anchor, padding, font_path, base_font_size

        self.preview_pil_image = self._apply_watermark_to_pil_image_for_preview(self.current_pil_image, *params)

        if self.preview_pil_image:
            qpixmap = self._pil_to_qpixmap(self.preview_pil_image)
            self.lbl_preview.setPixmap(qpixmap.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.log_message("预览已更新。")
        else:
            self.lbl_preview.setText("预览生成失败"); self.log_message("预览生成失败。")

    def process_single_image(self): # Updated to use new params
        if not self.current_image_path: QMessageBox.warning(self, "提示", "请先选择一张图片。"); return

        default_filename = os.path.splitext(os.path.basename(self.current_image_path))[0] + "" + os.path.splitext(self.current_image_path)[1]
        default_output_path = os.path.join(self.output_folder or os.path.dirname(self.current_image_path) or ".", default_filename)
        save_path, _ = QFileDialog.getSaveFileName(self, "保存水印图片", default_output_path, "图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if not save_path: self.log_message("单张图片保存操作已取消。"); return

        params = self._get_watermark_params_from_ui()
        success = apply_modern_watermark(self.current_image_path, save_path, *params, log_callback=self.log_message)
        if success: QMessageBox.information(self, "成功", f"水印图片已保存到: {save_path}")
        else: QMessageBox.warning(self, "失败", "添加水印失败，请查看日志输出。")

    def process_batch_images(self): # Updated for new params and time increment logic
        if not self.input_folder: QMessageBox.warning(self, "提示", "请选择输入图片文件夹。"); return
        if not self.output_folder: QMessageBox.warning(self, "提示", "请选择输出文件夹。"); return
        if self.input_folder == self.output_folder: QMessageBox.warning(self, "警告", "输入和输出文件夹不能相同。"); return

        os.makedirs(self.output_folder, exist_ok=True)
        title_text, location_text, base_timestamp_dt, anchor, padding, font_path, base_font_size = self._get_watermark_params_from_ui()
        increment_type = self.combo_time_increment.currentText()

        image_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        if not image_files: QMessageBox.information(self, "提示", "输入文件夹中没有找到支持的图片文件。"); return

        self.log_message(f"开始批量处理 {len(image_files)} 张图片 (现代样式)...")
        processed_count = 0
        current_timestamp_dt = base_timestamp_dt # Start with the UI selected time

        for i, filename in enumerate(image_files):
            input_path = os.path.join(self.input_folder, filename)
            base_name, ext = os.path.splitext(filename)
            output_filename = f"{base_name}{ext}"
            output_path = os.path.join(self.output_folder, output_filename)

            # Apply time increment for images after the first one
            if i > 0:
                if increment_type == "递增1分钟": current_timestamp_dt += datetime.timedelta(seconds=random.randint(61, 89))
                elif increment_type == "递增2分钟": current_timestamp_dt += datetime.timedelta(seconds=random.randint(117, 139))
                elif increment_type == "递增5分钟": current_timestamp_dt += datetime.timedelta(seconds=random.randint(311, 325))
                elif increment_type == "递增10分钟": current_timestamp_dt += datetime.timedelta(seconds=random.randint(607, 611))
                elif increment_type == "随机(1-5分钟)": current_timestamp_dt += datetime.timedelta(seconds=random.randint(60, 300))

            success = apply_modern_watermark(
                input_path, output_path,
                title_text, location_text, current_timestamp_dt, # current_timestamp_dt is key here
                anchor, padding, font_path, base_font_size,
                log_callback=self.log_message
            )
            if success: processed_count += 1
            QApplication.processEvents()

        QMessageBox.information(self, "完成", f"批量处理完成！共处理 {processed_count} / {len(image_files)} 张图片。")
        self.log_message(f"批量处理完成。成功: {processed_count}, 总计: {len(image_files)}.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WatermarkApp()
    sys.exit(app.exec_())