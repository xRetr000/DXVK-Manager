import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor

class InstallationThread(QThread):
    """Thread for running DXVK installation without blocking UI."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, manager, game_folder, architecture, directx_version, backup_enabled):
        super().__init__()
        self.manager = manager
        self.game_folder = game_folder
        self.architecture = architecture
        self.directx_version = directx_version
        self.backup_enabled = backup_enabled
    
    def run(self):
        """Run the installation in the background thread."""
        try:
            self.log_signal.emit("Starting DXVK installation...")
            self.log_signal.emit(f"Game folder: {self.game_folder}")
            self.log_signal.emit(f"Architecture: {self.architecture}")
            self.log_signal.emit(f"DirectX version: {self.directx_version}")
            self.log_signal.emit(f"Backup enabled: {self.backup_enabled}")
            self.log_signal.emit("")  # Empty line for readability
            
            # Capture print statements and errors
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    success = self.manager.install_dxvk(
                        self.game_folder, 
                        self.architecture, 
                        self.directx_version, 
                        self.backup_enabled
                    )
                
                # Emit captured stdout
                stdout_output = stdout_capture.getvalue()
                if stdout_output:
                    for line in stdout_output.strip().split('\n'):
                        if line.strip():
                            self.log_signal.emit(line)
                
                # Emit captured stderr
                stderr_output = stderr_capture.getvalue()
                if stderr_output:
                    self.log_signal.emit("")
                    self.log_signal.emit("Errors/Warnings:")
                    for line in stderr_output.strip().split('\n'):
                        if line.strip():
                            self.log_signal.emit(f"  {line}")
                
                if success:
                    self.log_signal.emit("")
                    self.log_signal.emit("✓ DXVK installation completed successfully!")
                    self.finished_signal.emit(True, "DXVK installation completed successfully!")
                else:
                    self.log_signal.emit("")
                    self.log_signal.emit("✗ DXVK installation failed.")
                    error_details = stdout_output + stderr_output
                    if error_details.strip():
                        error_msg = "DXVK installation failed. Check the log above for details."
                    else:
                        error_msg = "DXVK installation failed. No error details available."
                    self.finished_signal.emit(False, error_msg)
                    
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                self.log_signal.emit("")
                self.log_signal.emit("✗ Installation error occurred:")
                self.log_signal.emit(f"  {str(e)}")
                self.log_signal.emit("")
                self.log_signal.emit("Full error traceback:")
                for line in error_trace.split('\n'):
                    if line.strip():
                        self.log_signal.emit(f"  {line}")
                
                self.finished_signal.emit(False, f"Installation error: {str(e)}")
                
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            self.log_signal.emit(f"✗ Critical error: {error_msg}")
            self.log_signal.emit("")
            self.log_signal.emit("Error traceback:")
            for line in error_trace.split('\n'):
                if line.strip():
                    self.log_signal.emit(f"  {line}")
            self.finished_signal.emit(False, f"Critical error: {error_msg}")

class DetectionThread(QThread):
    """Thread for analyzing game folder without blocking UI."""
    detected_signal = pyqtSignal(str, str)  # architecture, directx
    log_signal = pyqtSignal(str)
    
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
    
    def run(self):
        """Analyze the game folder."""
        self.log_signal.emit(f"Analyzing folder: {self.folder}")
        
        try:
            if not os.path.exists(self.folder):
                self.log_signal.emit("Error: Folder does not exist.")
                self.detected_signal.emit("Error", "Error")
                return
            
            # Find .exe files
            exe_files = []
            for root, dirs, files in os.walk(self.folder):
                depth = root[len(self.folder):].count(os.sep)
                if depth > 1:
                    dirs[:] = []
                
                for f in files:
                    if f.lower().endswith('.exe'):
                        exe_files.append(os.path.join(root, f))
            
            if not exe_files:
                exe_files = [os.path.join(self.folder, f) 
                            for f in os.listdir(self.folder) 
                            if f.lower().endswith('.exe')]
            
            if not exe_files:
                self.log_signal.emit("No .exe files found in the selected folder.")
                self.detected_signal.emit("Not found", "Not found")
                return
            
            if len(exe_files) > 1:
                self.log_signal.emit(f"Multiple .exe files found: {len(exe_files)} files")
                self.log_signal.emit(f"Using {os.path.basename(exe_files[0])} for analysis.")
            
            exe_path = exe_files[0]
            
            # Analyze architecture and DirectX
            try:
                from exe_analyzer import get_exe_architecture, detect_directx_version
                arch = get_exe_architecture(exe_path)
                self.log_signal.emit(f"Architecture detected: {arch}")
                
                dx_versions = detect_directx_version(self.folder)
                if dx_versions and dx_versions[0] != "Unknown":
                    dx_text = ", ".join(dx_versions)
                else:
                    dx_text = "Not detected"
                self.log_signal.emit(f"DirectX versions detected: {dx_text}")
                
                self.detected_signal.emit(arch, dx_text)
                
            except Exception as e:
                self.log_signal.emit(f"Error during analysis: {str(e)}")
                self.detected_signal.emit("Error", "Error")
                
        except Exception as e:
            self.log_signal.emit(f"Error accessing folder: {str(e)}")
            self.detected_signal.emit("Error", "Error")

class ModernCard(QFrame):
    """A modern card widget with rounded corners and shadow effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)

class DXVKManagerGUI:
    def __init__(self, manager):
        self.manager = manager
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Apply modern Windows 11 style
        self.app.setStyle('Fusion')
        
        self.window = QMainWindow()
        self.window.setWindowTitle("DXVK Manager Tool")
        self.window.setMinimumSize(900, 650)
        self.window.resize(1000, 700)
        
        self.apply_modern_theme()
        
        # Central widget
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        # Main layout (horizontal split)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Left panel - Controls
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 0)
        
        # Right panel - Logs
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)
        
        # Threads
        self.install_thread = None
        self.detect_thread = None
    
    def apply_modern_theme(self):
        """Apply a modern dark theme."""
        palette = QPalette()
        
        # Dark theme colors
        palette.setColor(QPalette.ColorRole.Window, QColor(24, 24, 24))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 162, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 162, 255))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.app.setPalette(palette)
        
        # Set window background
        self.window.setStyleSheet("""
            QMainWindow {
                background-color: #181818;
            }
        """)
    
    def create_left_panel(self):
        """Create the left control panel."""
        panel = ModernCard()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("DXVK Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Game folder selection
        folder_label = QLabel("Game Folder:")
        folder_label.setStyleSheet("font-weight: 600; color: #E0E0E0;")
        layout.addWidget(folder_label)
        
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("Select game folder...")
        self.folder_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #00A2FF;
            }
        """)
        folder_layout.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #00A2FF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0090E6;
            }
            QPushButton:pressed {
                background-color: #0078CC;
            }
        """)
        browse_btn.clicked.connect(self.browse_game_folder)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)
        
        # Detection results card
        detection_card = ModernCard()
        detection_layout = QVBoxLayout(detection_card)
        detection_layout.setSpacing(10)
        detection_layout.setContentsMargins(15, 15, 15, 15)
        
        detection_title = QLabel("Detection Results")
        detection_title.setStyleSheet("font-weight: 600; color: #E0E0E0; font-size: 12pt;")
        detection_layout.addWidget(detection_title)
        
        # Architecture
        arch_layout = QHBoxLayout()
        arch_label = QLabel("Architecture:")
        arch_label.setStyleSheet("color: #B0B0B0;")
        arch_layout.addWidget(arch_label)
        self.architecture_label = QLabel("Not detected")
        self.architecture_label.setStyleSheet("""
            QLabel {
                color: #00A2FF;
                font-weight: 600;
                padding: 4px 8px;
                background-color: #1A3A4D;
                border-radius: 4px;
            }
        """)
        arch_layout.addWidget(self.architecture_label)
        arch_layout.addStretch()
        detection_layout.addLayout(arch_layout)
        
        # DirectX version
        dx_layout = QHBoxLayout()
        dx_label = QLabel("DirectX Version:")
        dx_label.setStyleSheet("color: #B0B0B0;")
        dx_layout.addWidget(dx_label)
        self.directx_label = QLabel("Not detected")
        self.directx_label.setStyleSheet("""
            QLabel {
                color: #00A2FF;
                font-weight: 600;
                padding: 4px 8px;
                background-color: #1A3A4D;
                border-radius: 4px;
            }
        """)
        dx_layout.addWidget(self.directx_label)
        dx_layout.addStretch()
        detection_layout.addLayout(dx_layout)
        
        layout.addWidget(detection_card)
        
        # DirectX override
        override_label = QLabel("Override DirectX:")
        override_label.setStyleSheet("font-weight: 600; color: #E0E0E0;")
        layout.addWidget(override_label)
        
        self.directx_combo = QComboBox()
        self.directx_combo.addItems(["Auto-detect", "Direct3D 9", "Direct3D 10", "Direct3D 11"])
        self.directx_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QComboBox:hover {
                border-color: #00A2FF;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #2D2D2D;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #FFFFFF;
                selection-background-color: #00A2FF;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.directx_combo)
        
        # Backup option
        self.backup_checkbox = QCheckBox("Backup existing DLLs")
        self.backup_checkbox.setChecked(True)
        self.backup_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E0E0E0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #404040;
                border-radius: 3px;
                background-color: #1E1E1E;
            }
            QCheckBox::indicator:checked {
                background-color: #00A2FF;
                border: 2px solid #00A2FF;
            }
            QCheckBox::indicator:hover {
                border-color: #00A2FF;
            }
        """)
        layout.addWidget(self.backup_checkbox)
        
        # Action buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.install_btn = QPushButton("Install DXVK")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #00A2FF;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #0090E6;
            }
            QPushButton:pressed {
                background-color: #0078CC;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.install_btn.clicked.connect(self.install_dxvk)
        button_layout.addWidget(self.install_btn)
        
        self.uninstall_btn = QPushButton("Uninstall DXVK")
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A5A5A;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #6A6A6A;
            }
            QPushButton:pressed {
                background-color: #4A4A4A;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.uninstall_btn.clicked.connect(self.uninstall_dxvk)
        button_layout.addWidget(self.uninstall_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """Create the right log panel."""
        panel = ModernCard()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Title
        log_title = QLabel("Activity Log")
        log_title_font = QFont()
        log_title_font.setPointSize(14)
        log_title_font.setBold(True)
        log_title.setFont(log_title_font)
        log_title.setStyleSheet("color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(log_title)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.log_text)
        
        return panel
    
    def browse_game_folder(self):
        """Open folder dialog to select game folder."""
        folder = QFileDialog.getExistingDirectory(
            self.window, 
            "Select Game Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)
            self.analyze_game_folder(folder)
    
    def analyze_game_folder(self, folder):
        """Analyze the selected game folder."""
        # Reset detection
        self.architecture_label.setText("Analyzing...")
        self.directx_label.setText("Analyzing...")
        
        # Stop previous detection thread if running
        if self.detect_thread and self.detect_thread.isRunning():
            self.detect_thread.terminate()
            self.detect_thread.wait()
        
        # Start new detection thread
        self.detect_thread = DetectionThread(folder)
        self.detect_thread.detected_signal.connect(self.on_detection_complete)
        self.detect_thread.log_signal.connect(self.log_message)
        self.detect_thread.start()
    
    def on_detection_complete(self, architecture, directx):
        """Handle detection results."""
        self.architecture_label.setText(architecture)
        self.directx_label.setText(directx)
    
    def install_dxvk(self):
        """Start DXVK installation."""
        folder = self.folder_input.text()
        if not folder:
            QMessageBox.critical(self.window, "Error", "Please select a game folder first.")
            return
        
        architecture = self.architecture_label.text()
        if architecture in ["Not detected", "Unknown", "Error", "Analyzing..."]:
            reply = QMessageBox.warning(
                self.window, 
                "Warning", 
                "Architecture not detected. Installation may fail. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Determine DirectX version
        if self.directx_combo.currentText() != "Auto-detect":
            directx_version = self.directx_combo.currentText()
        else:
            directx_text = self.directx_label.text()
            if directx_text != "Not detected" and directx_text != "Analyzing...":
                directx_version = directx_text.split(", ")[0]
            else:
                directx_version = "Unknown"
        
        backup_enabled = self.backup_checkbox.isChecked()
        
        # Disable buttons
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)
        
        # Stop previous thread if running
        if self.install_thread and self.install_thread.isRunning():
            self.install_thread.terminate()
            self.install_thread.wait()
        
        # Start installation thread
        self.install_thread = InstallationThread(
            self.manager, folder, architecture, directx_version, backup_enabled
        )
        self.install_thread.log_signal.connect(self.log_message)
        self.install_thread.finished_signal.connect(self.on_installation_finished)
        self.install_thread.start()
    
    def on_installation_finished(self, success, message):
        """Handle installation completion."""
        self.install_btn.setEnabled(True)
        self.uninstall_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self.window, "Success", message)
        else:
            QMessageBox.critical(self.window, "Error", message)
    
    def uninstall_dxvk(self):
        """Uninstall DXVK."""
        folder = self.folder_input.text()
        if not folder:
            QMessageBox.critical(self.window, "Error", "Please select a game folder first.")
            return
        
        reply = QMessageBox.question(
            self.window,
            "Confirm Uninstall",
            "Are you sure you want to uninstall DXVK and restore backups?\n\n"
            "This will restore the original DirectX DLL files from backup.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_message(f"Starting uninstallation for: {folder}")
            self.log_message("")
            
            # Capture print statements and errors
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    success = self.manager.uninstall_dxvk(folder)
                
                # Emit captured stdout
                stdout_output = stdout_capture.getvalue()
                if stdout_output:
                    for line in stdout_output.strip().split('\n'):
                        if line.strip():
                            self.log_message(line)
                
                # Emit captured stderr
                stderr_output = stderr_capture.getvalue()
                if stderr_output:
                    self.log_message("")
                    self.log_message("Errors/Warnings:")
                    for line in stderr_output.strip().split('\n'):
                        if line.strip():
                            self.log_message(f"  {line}")
                
                if success:
                    self.log_message("")
                    self.log_message("✓ DXVK uninstalled successfully!")
                    QMessageBox.information(
                        self.window, 
                        "Success", 
                        "DXVK uninstalled successfully!\nOriginal DLL files have been restored."
                    )
                else:
                    self.log_message("")
                    self.log_message("✗ DXVK uninstallation failed or no backup found.")
                    QMessageBox.warning(
                        self.window,
                        "Warning",
                        "Uninstallation failed or no backup found.\n\n"
                        "The backup folder may not exist, or there may have been an error during restoration."
                    )
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                self.log_message("")
                self.log_message(f"✗ Error during uninstallation: {error_msg}")
                self.log_message("")
                self.log_message("Full error traceback:")
                for line in error_trace.split('\n'):
                    if line.strip():
                        self.log_message(f"  {line}")
                QMessageBox.critical(self.window, "Error", f"Uninstallation error:\n{error_msg}")
    
    def log_message(self, message):
        """Add a message to the log."""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def run(self):
        """Start the GUI application."""
        self.window.show()
        return self.app.exec()
