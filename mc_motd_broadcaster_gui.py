#!/usr/bin/env python3

"""
Minecraft MOTD 广播器 GUI — 基于 PyQt5 与 qfluentwidgets (Fluent Design)
"""

import sys
import json
import re

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QBrush
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, QFrame, QSizePolicy,
)

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    LineEdit, PushButton, SpinBox, DoubleSpinBox,
    CardWidget, BodyLabel, StrongBodyLabel,
    TextEdit, PlainTextEdit,
    setTheme, Theme,
    MessageBox, PrimaryPushButton, ToolButton,
    FlowLayout, PillPushButton,
)

import mc_motd_broadcaster_config as motd_broadcaster

__version__ = "2.1.0"

# ── Minecraft 颜色映射 ──────────────────────────────────────────
COLORS = [
    ("§0", "黑",   "#000000"),
    ("§1", "深蓝", "#0000AA"),
    ("§2", "深绿", "#00AA00"),
    ("§3", "深青", "#00AAAA"),
    ("§4", "深红", "#AA0000"),
    ("§5", "深紫", "#AA00AA"),
    ("§6", "金",   "#FFAA00"),
    ("§7", "灰",   "#AAAAAA"),
    ("§8", "深灰", "#555555"),
    ("§9", "蓝",   "#5555FF"),
    ("§a", "绿",   "#55FF55"),
    ("§b", "青",   "#55FFFF"),
    ("§c", "红",   "#FF5555"),
    ("§d", "粉",   "#FF55FF"),
    ("§e", "黄",   "#FFFF55"),
    ("§f", "白",   "#FFFFFF"),
]

FORMATS = [
    ("§l", "B", "粗体", QFont.Bold),
    ("§o", "I", "斜体", QFont.StyleItalic),
    ("§n", "U", "下划线"),
    ("§m", "S", "删除线"),
    ("§k", "?", "随机"),
    ("§r", "R", "重置"),
]


def motd_to_html(raw: str) -> str:
    """将 Minecraft § 代码转为 HTML 片段。"""
    parts = []
    i = 0
    cur_color = "#FFFFFF"
    bold = italic = underline = strikethrough = False

    def _tag(html):
        parts.append(html)

    while i < len(raw):
        if raw[i] == "§" and i + 1 < len(raw):
            code = raw[i + 1].lower()
            i += 2
            if code == "r":
                cur_color = "#FFFFFF"
                bold = italic = underline = strikethrough = False
                _tag("</span>")
            elif code in "0123456789abcdef":
                if parts and not parts[-1].endswith(">"):
                    _tag("</span>")
                cur_color = next(c[2] for c in COLORS if c[0][1] == code)
            elif code == "l":
                bold = True
            elif code == "o":
                italic = True
            elif code == "n":
                underline = True
            elif code == "m":
                strikethrough = True
            continue

        styles = f"color:{cur_color};"
        if bold:      styles += "font-weight:bold;"
        if italic:    styles += "font-style:italic;"
        if underline: styles += "text-decoration:underline;"
        if strikethrough: styles += "text-decoration:line-through;" if not underline else "text-decoration:underline line-through;"

        # escape HTML
        ch = raw[i]
        if ch == "<": ch = "&lt;"
        elif ch == ">": ch = "&gt;"
        elif ch == "&": ch = "&amp;"
        elif ch == "\n": ch = "<br>"

        _tag(f'<span style="{styles}">{ch}</span>')
        i += 1

    html = "".join(parts)
    return f'<div style="font-family:Minecraft,monospace;font-size:14px;background:#1a1a1a;padding:8px;">{html}</div>'


# ── 页面 ────────────────────────────────────────────────────────

class BroadcastPage(CardWidget):
    """广播配置与控制页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.broadcasters = []
        self.config_path = "mc_motd_config.json"
        self.config = {}
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_status)
        self._setup_ui()
        self.load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = StrongBodyLabel("广播配置")
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        layout.addWidget(title)

        layout.addWidget(BodyLabel("MOTD 名称"))
        self.motd_input = LineEdit(self)
        self.motd_input.setPlaceholderText("A Minecraft Server")
        layout.addWidget(self.motd_input)

        row1 = QHBoxLayout()
        row1.addWidget(BodyLabel("服务器数量"))
        self.count_spin = SpinBox(self)
        self.count_spin.setRange(1, 20)
        self.count_spin.setValue(1)
        row1.addWidget(self.count_spin)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(BodyLabel("基础端口"))
        self.port_spin = SpinBox(self)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(25565)
        row2.addWidget(self.port_spin)
        row2.addStretch()
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(BodyLabel("广播间隔 (秒)"))
        self.interval_spin = DoubleSpinBox(self)
        self.interval_spin.setRange(0.5, 30.0)
        self.interval_spin.setSingleStep(0.5)
        self.interval_spin.setValue(3.0)
        row3.addWidget(self.interval_spin)
        row3.addStretch()
        layout.addLayout(row3)

        btn_row = QHBoxLayout()
        self.start_btn = PrimaryPushButton("▶  开始广播", self)
        self.start_btn.clicked.connect(self.toggle_broadcasting)
        btn_row.addWidget(self.start_btn)
        self.save_btn = PushButton("保存配置", self)
        self.save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        layout.addWidget(StrongBodyLabel("输出信息"))
        self.log = TextEdit(self)
        self.log.setReadOnly(True)
        layout.addWidget(self.log, stretch=1)

    # ── 配置 ──

    def load_config(self, silent=False):
        self.config = motd_broadcaster.load_config(self.config_path)
        if "motd" in self.config:
            self.motd_input.setText(self.config["motd"])
        if "motd_count" in self.config:
            self.count_spin.setValue(self.config["motd_count"])
        if "base_port" in self.config:
            self.port_spin.setValue(self.config["base_port"])
        if "interval" in self.config:
            self.interval_spin.setValue(self.config["interval"])
        if not silent:
            self._info(f"已加载配置文件: {self.config_path}")

    def save_config(self):
        self.config["motd"] = self.motd_input.text().strip()
        self.config["motd_count"] = self.count_spin.value()
        self.config["base_port"] = self.port_spin.value()
        self.config["interval"] = self.interval_spin.value()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self._info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            self._warn(f"保存配置失败: {e}")

    # ── 广播 ──

    def toggle_broadcasting(self):
        if self.broadcasters:
            self.stop_broadcasting()
        else:
            self.start_broadcasting()

    def start_broadcasting(self):
        self.save_config()
        self.config = motd_broadcaster.load_config(self.config_path)
        self.broadcasters = []
        try:
            for server in self.config["servers"]:
                bc = motd_broadcaster.MinecraftMOTDBroadcaster(
                    server["motd"], server["port"]
                )
                bc.BROADCAST_INTERVAL = server["interval"]
                bc.start()
                self.broadcasters.append(bc)
            self.start_btn.setText("■  停止广播")
            self._info(f"已开始广播 {len(self.broadcasters)} 个服务器")
            self._timer.start(2000)
        except Exception as e:
            self._warn(f"启动广播失败: {e}")

    def stop_broadcasting(self):
        for bc in self.broadcasters:
            bc._stop_event.set()
        self.broadcasters = []
        self.start_btn.setText("▶  开始广播")
        self._timer.stop()
        self._info("已停止所有广播")

    def _update_status(self):
        count = len([b for b in self.broadcasters if b.is_running()])
        self.start_btn.setText(f"■  停止广播 ({count} 运行中)")

    def _info(self, text):
        self.log.append(f"[INFO] {text}")

    def _warn(self, text):
        self.log.append(f"[WARN] {text}")

    def cleanup(self):
        self._timer.stop()
        for bc in self.broadcasters:
            bc._stop_event.set()

    def set_motd(self, text):
        """从 MOTD 编辑器接收编辑后的文本。"""
        self.motd_input.setText(text)


class MotdEditorPage(CardWidget):
    """MOTD 编辑页 — 类似 motd.gg 的实时编辑器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._motd_page = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = StrongBodyLabel("MOTD 编辑器")
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        layout.addWidget(title)

        # ── 颜色按钮 (2×8 网格) ──
        layout.addWidget(BodyLabel("颜色"))
        color_grid = QGridLayout()
        color_grid.setSpacing(3)
        for idx, (code, name, hex_color) in enumerate(COLORS):
            btn = PushButton(name, self)
            btn.setFixedSize(52, 30)
            btn.setStyleSheet(f"""
                PushButton {{
                    background-color: {hex_color};
                    color: #fff;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                PushButton:hover {{
                    border: 2px solid #fff;
                }}
            """)
            btn.clicked.connect(lambda _, c=code: self._insert_code(c))
            color_grid.addWidget(btn, idx // 8, idx % 8)
        layout.addLayout(color_grid)

        # ── 格式按钮 ──
        layout.addWidget(BodyLabel("格式"))
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(4)
        for code, label, tip, *_ in FORMATS:
            btn = PushButton(label, self)
            btn.setFixedSize(48, 30)
            btn.setToolTip(tip)
            btn.setStyleSheet("""
                PushButton {
                    background-color: #444;
                    color: #fff;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                }
                PushButton:hover { border: 2px solid #fff; }
            """)
            btn.clicked.connect(lambda _, c=code: self._insert_code(c))
            fmt_row.addWidget(btn)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)

        # ── 编辑区 + 预览 ──
        splitter = QSplitter(Qt.Horizontal, self)

        # 左侧：原始文本
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(BodyLabel("原始文本 (§ 代码)"))
        self.raw_edit = PlainTextEdit(self)
        self.raw_edit.setPlaceholderText("在此输入 MOTD，支持 § 颜色代码…")
        self.raw_edit.setFont(QFont("Consolas", 12))
        self.raw_edit.textChanged.connect(self._update_preview)
        left_layout.addWidget(self.raw_edit)
        splitter.addWidget(left_pane)

        # 右侧：预览
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(BodyLabel("游戏内预览"))
        self.preview = TextEdit(self)
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("background-color: #1a1a1a; border: none;")
        right_layout.addWidget(self.preview)
        splitter.addWidget(right_pane)

        splitter.setSizes([280, 280])
        layout.addWidget(splitter, stretch=1)

        # ── 底部按钮 ──
        bottom = QHBoxLayout()

        self.apply_btn = PrimaryPushButton("✔  应用到广播", self)
        self.apply_btn.clicked.connect(self._apply_motd)
        bottom.addWidget(self.apply_btn)

        self.copy_btn = PushButton("📋  复制 MOTD", self)
        self.copy_btn.clicked.connect(self._copy_motd)
        bottom.addWidget(self.copy_btn)

        clear_btn = PushButton("清空", self)
        clear_btn.clicked.connect(lambda: self.raw_edit.clear())
        bottom.addWidget(clear_btn)

        layout.addLayout(bottom)

    def _insert_code(self, code):
        """在光标处插入 § 代码。"""
        cursor = self.raw_edit.textCursor()
        cursor.insertText(code)
        self.raw_edit.setTextCursor(cursor)
        self.raw_edit.setFocus()

    def _update_preview(self):
        html = motd_to_html(self.raw_edit.toPlainText())
        self.preview.setHtml(html)

    def _apply_motd(self):
        text = self.raw_edit.toPlainText().strip()
        if not text:
            return
        if self._motd_page:
            self._motd_page.set_motd(text)
            self._motd_page.save_config()
            # 切换导航到广播页
            w = self.window()
            if hasattr(w, 'switchTo'):
                w.switchTo(w.broadcast_page)

    def _copy_motd(self):
        text = self.raw_edit.toPlainText().strip()
        if not text:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def link_motd_page(self, page):
        """关联广播页，用于应用 MOTD。"""
        self._motd_page = page

    def set_motd(self, text):
        """从外部设置 MOTD（如从广播页反向编辑）。"""
        self.raw_edit.setPlainText(text)


class MainWindow(FluentWindow):
    """Minecraft MOTD 广播器 — 主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft MOTD 广播器")
        self.resize(620, 620)

        self.broadcast_page = BroadcastPage(self)
        self.motd_editor = MotdEditorPage(self)
        self.motd_editor.link_motd_page(self.broadcast_page)

        self.initNavigation()
        self._center()

    def initNavigation(self):
        self.broadcast_page.setObjectName("broadcast_page")
        self.addSubInterface(
            self.broadcast_page, FluentIcon.SEND, "广播",
            NavigationItemPosition.TOP,
        )

        self.motd_editor.setObjectName("motd_editor")
        self.addSubInterface(
            self.motd_editor, FluentIcon.EDIT, "MOTD 编辑器",
            NavigationItemPosition.TOP,
        )

        self.navigationInterface.addItem(
            routeKey="about",
            icon=FluentIcon.INFO,
            text="关于",
            onClick=self._show_about,
            position=NavigationItemPosition.BOTTOM,
        )

    def _show_about(self):
        dlg = MessageBox(
            "关于",
            f'Minecraft MOTD 广播器 GUI {__version__}\n'
            f'核心: {motd_broadcaster.__version__}\n\n'
            f'基于 LANBroadcaster (by minerz029)\n'
            f'使用 GNU GPL v3 许可证',
            self,
        )
        dlg.yesButton.setText("确定")
        dlg.cancelButton.hide()
        dlg.exec()

    def _center(self):
        self.show()
        QApplication.processEvents()
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event):
        self.broadcast_page.cleanup()
        super().closeEvent(event)


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
