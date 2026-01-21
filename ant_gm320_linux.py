#!/usr/bin/env python3
"""
Ant Esports GM320 (Instant A825) – Linux Utility
------------------------------------------------
Features:
- RGB Lighting Control (Static, Breathing, Neon, Wave, etc.)
- DPI Configuration (200 - 12800 DPI)
- Polling Rate Selection
- Auto-generation of udev rules for permissions

Dependencies:
    pip install hidapi PySide6
"""

import sys
import os
import hid
from enum import IntEnum
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QColorDialog, QMessageBox, QFrame,
    QGroupBox, QSlider
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

# ===================== PROTOCOL DEFINITIONS =====================

class Reg(IntEnum):
    """Register addresses for Instant A825 Chipset"""
    PROFILE   = 0x0000
    POLLING   = 0x0009
    DPI_INDEX = 0x0012  # Current DPI step index
    RGB_MODE  = 0x0014
    RGB_SPEED = 0x0016  # Lighting speed
    RGB_COLOR = 0x0015  # Static color (R, G, B)
    APPLY     = 0x0010  # Apply flag
    SAVE      = 0x0011  # Save to memory flag

class RGBMode(IntEnum):
    """Lighting Modes supported by GM320 firmware"""
    OFF              = 0x00
    COLORFUL_STREAMING = 0x01 # Flowing rainbow
    STEADY           = 0x02   # Static Color
    BREATHING        = 0x03   # Single Color Breath
    COLORFUL_TAIL    = 0x04   # Snake/Tail effect
    NEON             = 0x05   # Color cycle
    COLORFUL_STEADY  = 0x06   # Multi-color static
    FLICKER          = 0x07   # Flashing
    STARS_TWINKLE    = 0x08   # Random pixels
    WAVE             = 0x09   # Wave effect

# ===================== HARDWARE INTERFACE =====================

class GM320Device:
    # Common Vendor IDs for Instant Micro mice
    VENDOR_IDS = [0x30FA, 0x1D57]
    
    # Common Product Names reported by this mouse
    NAME_KEYS = ["INSTANT", "GAMING MOUSE", "GM320", "USB OPTICAL MOUSE"]

    REPORT_ID   = 0x07
    CMD_WRITE   = 0x18
    REPORT_SIZE = 65

    # Interpolated DPI steps for A825 (GM320 spec)
    DPI_TABLE = [
        200, 400, 600, 800, 1000, 1200, 1400, 1600,
        1800, 2000, 2400, 3200, 4000, 4800, 5600,
        6400, 7200, 8000, 8800, 9600, 10400,
        11200, 12800
    ]

    POLLING_MAP = {125: 1, 250: 2, 500: 3, 1000: 4}

    def __init__(self):
        self.dev = None
        self.connected_info = ""
        self._connect()

    def _connect(self):
        """Attempts to find and open the device."""
        for d in hid.enumerate():
            if d["vendor_id"] in self.VENDOR_IDS:
                name = (d.get("product_string") or "").upper()
                if any(k in name for k in self.NAME_KEYS):
                    try:
                        self.dev = hid.Device(path=d["path"])
                        self.connected_info = f"{name} (VID: {hex(d['vendor_id'])})"
                        print(f"[Success] Connected to {self.connected_info}")
                        return
                    except Exception as e:
                        print(f"[Error] Found device but failed to open: {e}")
                        continue
        
        if self.dev is None:
            raise RuntimeError("Mouse not found! Ensure it is plugged in.\n"
                               "If on Linux, you may need udev rules (see Setup tab).")

    def _send_packet(self, payload):
        """Sends a feature report padded to the correct size."""
        # Feature report format: [ReportID, 0x00, ...] or just payload depending on backend
        # For hidapi/linux, we usually send bytes starting with Report ID if it's a feature report
        
        # Construct packet: [ReportID, Command, RegLow, RegHigh, Data...]
        # But hidapi.send_feature_report expects the Report ID as the first byte
        full_pkt = [self.REPORT_ID] + list(payload)
        
        # Pad to 65 bytes (Report ID + 64 bytes data)
        full_pkt += [0x00] * (self.REPORT_SIZE - len(full_pkt))
        
        try:
            self.dev.send_feature_report(bytes(full_pkt))
        except Exception as e:
            print(f"[Warning] Write failed: {e}")

    def write_reg(self, reg, data):
        """Writes data to a specific register."""
        # Protocol: [CMD_WRITE, RegLow, RegHigh, Data...]
        payload = [
            self.CMD_WRITE,
            reg & 0xFF,
            (reg >> 8) & 0xFF
        ] + list(data)
        self._send_packet(payload)

    def apply_settings(self, cfg):
        """Sends all settings to the mouse."""
        print(f"Applying: {cfg}")
        
        # 1. DPI
        if cfg["dpi"] in self.DPI_TABLE:
            idx = self.DPI_TABLE.index(cfg["dpi"])
            self.write_reg(Reg.DPI_INDEX, [idx])
        
        # 2. Polling Rate
        self.write_reg(Reg.POLLING, [self.POLLING_MAP[cfg["polling"]]])
        
        # 3. RGB Mode
        self.write_reg(Reg.RGB_MODE, [cfg["rgb_mode"]])
        
        # 4. RGB Color (Only used in Static/Breathing modes)
        r, g, b = cfg["rgb_color"]
        self.write_reg(Reg.RGB_COLOR, [r, g, b])
        
        # 5. Apply and Save
        self.write_reg(Reg.APPLY, [0x01])
        self.write_reg(Reg.SAVE, [0x01])

# ===================== GUI APPLICATION =====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ant Esports GM320 Manager")
        self.resize(600, 500)
        self.apply_stylesheet()

        self.device = None
        self.pending_config = {
            "dpi": 1600,
            "polling": 1000,
            "rgb_mode": RGBMode.COLORFUL_STREAMING,
            "rgb_color": (255, 0, 0)
        }

        # Initialize UI
        self.init_ui()
        
        # Try connecting
        try:
            self.device = GM320Device()
            self.status_label.setText(f"Connected: {self.device.connected_info}")
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        except RuntimeError as e:
            self.status_label.setText("Device Disconnected / Permission Error")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            QMessageBox.warning(self, "Connection Error", str(e))

    def apply_stylesheet(self):
        # Dark Theme Look
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: #ffffff; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #3c3c3c; color: #aaa; padding: 10px; }
            QTabBar::tab:selected { background: #505050; color: #fff; }
            QLabel { color: #ffffff; font-size: 14px; }
            QPushButton { 
                background-color: #0078d7; color: white; border: none; padding: 8px; 
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #198ce6; }
            QComboBox { padding: 5px; background: #444; color: white; border: 1px solid #555; }
            QGroupBox { border: 1px solid #555; margin-top: 20px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)

    def init_ui(self):
        root = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("GM320 Control Center")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_performance_tab(), "Performance")
        tabs.addTab(self.create_rgb_tab(), "Lighting")
        tabs.addTab(self.create_setup_tab(), "Setup / Help")
        layout.addWidget(tabs)

        # Footer Actions
        btn_layout = QHBoxLayout()
        
        apply_btn = QPushButton("APPLY SETTINGS")
        apply_btn.setMinimumHeight(40)
        apply_btn.clicked.connect(self.apply_to_device)
        
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)

        root.setLayout(layout)
        self.setCentralWidget(root)

    def create_performance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # DPI Group
        dpi_group = QGroupBox("Sensitivity (DPI)")
        dpi_layout = QVBoxLayout()
        
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems([str(x) for x in GM320Device.DPI_TABLE])
        self.dpi_combo.setCurrentText("1600")
        self.dpi_combo.currentTextChanged.connect(self.update_config)
        
        dpi_layout.addWidget(QLabel("Select DPI Level:"))
        dpi_layout.addWidget(self.dpi_combo)
        dpi_group.setLayout(dpi_layout)
        layout.addWidget(dpi_group)

        # Polling Rate Group
        poll_group = QGroupBox("Response Rate (Hz)")
        poll_layout = QVBoxLayout()
        
        self.poll_combo = QComboBox()
        self.poll_combo.addItems(["125", "250", "500", "1000"])
        self.poll_combo.setCurrentText("1000")
        self.poll_combo.currentTextChanged.connect(self.update_config)

        poll_layout.addWidget(QLabel("Polling Rate:"))
        poll_layout.addWidget(self.poll_combo)
        poll_group.setLayout(poll_layout)
        layout.addWidget(poll_group)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_rgb_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Mode Selection
        mode_group = QGroupBox("Lighting Effect")
        mode_layout = QVBoxLayout()
        
        self.rgb_mode_combo = QComboBox()
        for mode in RGBMode:
            self.rgb_mode_combo.addItem(mode.name.replace("_", " ").title(), mode)
        
        self.rgb_mode_combo.setCurrentText("Colorful Streaming")
        self.rgb_mode_combo.currentIndexChanged.connect(self.update_config)
        
        mode_layout.addWidget(self.rgb_mode_combo)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Color Selection
        color_group = QGroupBox("Static Color")
        color_layout = QHBoxLayout()
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(50, 30)
        self.color_preview.setStyleSheet("background-color: red; border: 1px solid white;")
        
        self.color_btn = QPushButton("Pick Color")
        self.color_btn.clicked.connect(self.pick_color)
        
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_setup_tab(self):
        """Tab to help user set up udev rules."""
        tab = QWidget()
        layout = QVBoxLayout()

        info = QLabel(
            "Linux requires permission to access USB HID devices.\n"
            "If the application cannot find the mouse, install the udev rule below."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        install_btn = QPushButton("Generate udev rule file")
        install_btn.clicked.connect(self.generate_udev_rule)
        layout.addWidget(install_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    # ===================== LOGIC =====================

    def pick_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.pending_config["rgb_color"] = (c.red(), c.green(), c.blue())
            self.color_preview.setStyleSheet(f"background-color: {c.name()}; border: 1px solid white;")

    def update_config(self):
        # Update pending config dict from UI state
        self.pending_config["dpi"] = int(self.dpi_combo.currentText())
        self.pending_config["polling"] = int(self.poll_combo.currentText())
        
        # Get RGB Mode enum from user data in combo
        idx = self.rgb_mode_combo.currentIndex()
        self.pending_config["rgb_mode"] = self.rgb_mode_combo.itemData(idx)

    def apply_to_device(self):
        if not self.device:
            QMessageBox.critical(self, "Error", "No device connected.")
            return
        
        try:
            self.device.apply_settings(self.pending_config)
            QMessageBox.information(self, "Success", "Settings applied successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings:\n{e}")

    def generate_udev_rule(self):
        rule_content = (
            '# Ant Esports GM320 / Instant A825 Mouse\n'
            'SUBSYSTEM=="usb", ATTRS{idVendor}=="30fa", MODE="0666"\n'
            'SUBSYSTEM=="usb", ATTRS{idVendor}=="1d57", MODE="0666"\n'
            'KERNEL=="hidraw*", ATTRS{idVendor}=="30fa", MODE="0666"\n'
            'KERNEL=="hidraw*", ATTRS{idVendor}=="1d57", MODE="0666"\n'
        )
        
        fname = "99-gm320-mouse.rules"
        try:
            with open(fname, "w") as f:
                f.write(rule_content)
            
            QMessageBox.information(
                self, "File Created",
                f"Created '{fname}' in the current folder.\n\n"
                "Run the following command in terminal to install:\n"
                f"sudo mv {fname} /etc/udev/rules.d/ && sudo udevadm control --reload-rules && sudo udevadm trigger"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check for PySide6 or PyQt installation
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Critical Error: {e}")
