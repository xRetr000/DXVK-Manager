import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

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
            
            # Find .exe files (Windows only)
            exe_files = []
            
            # Search recursively (limited depth)
            for root, dirs, files in os.walk(self.folder):
                depth = root[len(self.folder):].count(os.sep)
                if depth > 1:  # Only go 1 level deep
                    dirs[:] = []
                
                for f in files:
                    if f.lower().endswith('.exe'):
                        exe_files.append(os.path.join(root, f))
            
            # Also check root folder
            if not exe_files:
                try:
                    exe_files = [os.path.join(self.folder, f) 
                                for f in os.listdir(self.folder) 
                                if f.lower().endswith('.exe')]
                except PermissionError:
                    self.log_signal.emit("Error: Cannot access folder. You may need administrator privileges.")
                    self.detected_signal.emit("Error", "Error")
                    return
            
            if not exe_files:
                self.log_signal.emit("No .exe files found in the selected folder.")
                self.log_signal.emit("Tip: Make sure you selected the folder containing the game's main executable.")
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

class DarkMessageBox(QDialog):
    """Custom dark-themed message box to match the application's dark mode."""
    def __init__(self, parent=None, title="", message="", icon_type="question"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)
        self.setModal(True)
        self.result_button = None
        
        # Dark theme styling - Windows 11 dark mode
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                color: #FFFFFF;
            }
            QLabel {
                color: #E0E0E0;
                background-color: transparent;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton#secondary {
                background-color: #5A5A5A;
                color: white;
            }
            QPushButton#secondary:hover {
                background-color: #6A6A6A;
            }
            QPushButton#secondary:pressed {
                background-color: #4A4A4A;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Icon and message layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Icon label with circular background
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        if icon_type == "question":
            icon_label.setText("?")
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 36pt;
                    color: #0078D4;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                    background-color: #1A3A4D;
                    border-radius: 25px;
                    padding: 0px;
                }
            """)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif icon_type == "warning":
            icon_label.setText("!")
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 36pt;
                    color: #FFB900;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                    background-color: #4A3A1A;
                    border-radius: 25px;
                    padding: 0px;
                }
            """)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif icon_type == "critical":
            icon_label.setText("✗")
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 36pt;
                    color: #E81123;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                    background-color: #4A1A1A;
                    border-radius: 25px;
                    padding: 0px;
                }
            """)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif icon_type == "information":
            icon_label.setText("i")
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 36pt;
                    color: #0078D4;
                    font-weight: bold;
                    min-width: 50px;
                    max-width: 50px;
                    min-height: 50px;
                    max-height: 50px;
                    background-color: #1A3A4D;
                    border-radius: 25px;
                    padding: 0px;
                }
            """)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            icon_label.setMinimumWidth(0)
            icon_label.setMaximumWidth(0)
            icon_label.setMinimumHeight(0)
            icon_label.setMaximumHeight(0)
        
        content_layout.addWidget(icon_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            font-size: 10pt; 
            line-height: 1.5;
            color: #E0E0E0;
        """)
        content_layout.addWidget(message_label, 1)
        
        layout.addLayout(content_layout)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.yes_button = QPushButton("Yes")
        self.yes_button.clicked.connect(lambda: self.accept())
        button_layout.addWidget(self.yes_button)
        
        self.no_button = QPushButton("No")
        self.no_button.setObjectName("secondary")
        self.no_button.clicked.connect(lambda: self.reject())
        button_layout.addWidget(self.no_button)
        
        layout.addLayout(button_layout)
        
        # Set default button and focus
        self.yes_button.setDefault(True)
        self.yes_button.setFocus()
        
        # Set minimum width for better appearance
        self.setMinimumWidth(450)
    
    @staticmethod
    def question(parent, title, message):
        """Show a question dialog (Yes/No)."""
        dialog = DarkMessageBox(parent, title, message, "question")
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
    
    @staticmethod
    def warning(parent, title, message):
        """Show a warning dialog (OK)."""
        dialog = DarkMessageBox(parent, title, message, "warning")
        dialog.no_button.hide()
        dialog.yes_button.setText("OK")
        dialog.exec()
    
    @staticmethod
    def critical(parent, title, message):
        """Show a critical error dialog (OK)."""
        dialog = DarkMessageBox(parent, title, message, "critical")
        dialog.no_button.hide()
        dialog.yes_button.setText("OK")
        dialog.exec()
    
    @staticmethod
    def information(parent, title, message):
        """Show an information dialog (OK)."""
        dialog = DarkMessageBox(parent, title, message, "information")
        dialog.no_button.hide()
        dialog.yes_button.setText("OK")
        dialog.exec()

class DXVKManagerGUI:
    def __init__(self, manager):
        self.manager = manager
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Use Windows native style for Windows 11 look
        self.app.setStyle('windowsvista')  # Windows 11 compatible native style
        
        self.window = QMainWindow()
        self.window.setWindowTitle("DXVK Manager")
        self.window.setMinimumSize(900, 650)
        self.window.resize(1000, 700)
        
        # Enable Windows 11 rounded corners and modern look
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.apply_windows11_theme()
        
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
    
    def apply_windows11_theme(self):
        """Apply Windows 11 native theme with system colors."""
        import winreg
        use_dark = True  # Default to dark mode
        
        try:
            # Detect Windows dark mode preference
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            use_dark = winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 0
            winreg.CloseKey(key)
        except (FileNotFoundError, OSError, ValueError):
            # Registry key doesn't exist (older Windows) or access denied
            # Default to dark mode
            pass
        
        if use_dark:
            # Windows 11 Dark Mode colors
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(32, 32, 32))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(42, 42, 42))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(42, 42, 42))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))  # Windows accent
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            self.app.setPalette(palette)
        
        # Windows 11 Fluent Design styling
        self.window.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
            }
            QFrame {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: none;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3A3A, stop:1 #2D2D2D);
            }
            QLineEdit, QComboBox {
                border-radius: 4px;
                padding: 6px;
                border: 1px solid #404040;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #0078D4;
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
        
        # Game folder selection - Make it the primary action
        folder_label = QLabel("1. Select Game Folder")
        folder_label.setStyleSheet("font-weight: 600; font-size: 11pt; color: #E0E0E0;")
        layout.addWidget(folder_label)
        
        folder_hint = QLabel("Choose the folder containing your game's .exe file")
        folder_hint.setStyleSheet("color: #999999; font-size: 9pt;")
        layout.addWidget(folder_hint)
        
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("Click Browse to select your game folder...")
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
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Select the folder where your game is installed")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
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
        
        detection_title = QLabel("2. Detection Results")
        detection_title.setStyleSheet("font-weight: 600; color: #E0E0E0; font-size: 11pt;")
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
        override_label = QLabel("3. DirectX Version (if auto-detect fails):")
        override_label.setStyleSheet("font-weight: 600; color: #E0E0E0; font-size: 10pt;")
        layout.addWidget(override_label)
        
        self.directx_combo = QComboBox()
        self.directx_combo.addItems(["Auto-detect", "Direct3D 9", "Direct3D 10", "Direct3D 11"])
        self.directx_combo.setToolTip("Manually select DirectX version if auto-detection fails")
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
        
        # Backup option - Always enabled for safety
        self.backup_checkbox = QCheckBox("Create backup before installing (Recommended)")
        self.backup_checkbox.setChecked(True)
        self.backup_checkbox.setToolTip("Always creates a backup so you can restore original files if needed")
        self.backup_checkbox.setEnabled(False)  # Always enabled - can't disable for safety
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
        
        self.install_btn = QPushButton("4. Install DXVK")
        self.install_btn.setToolTip("Downloads and installs DXVK DLLs to your game folder")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.install_btn.clicked.connect(self.install_dxvk)
        button_layout.addWidget(self.install_btn)
        
        self.uninstall_btn = QPushButton("Restore Original DLLs")
        self.uninstall_btn.setToolTip("Restores the original DirectX DLLs from backup")
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #5A5A5A;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 10pt;
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
        """Open folder dialog to select Windows game folder."""
        # Start in common game locations
        common_paths = [
            os.path.expanduser("~\\Documents"),
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Games",
            "D:\\Games",
            "E:\\Games",
        ]
        
        start_path = ""
        for path in common_paths:
            if os.path.exists(path):
                start_path = path
                break
        
        folder = QFileDialog.getExistingDirectory(
            self.window, 
            "Select Game Folder\n(Choose the folder containing your game's .exe file)",
            start_path,
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
        """Start DXVK installation with confirmation."""
        folder = self.folder_input.text()
        if not folder:
            DarkMessageBox.warning(
                self.window, 
                "No Game Selected", 
                "Please select a game folder first.\n\n"
                "Click 'Browse...' to choose the folder containing your game's .exe file."
            )
            return
        
        architecture = self.architecture_label.text()
        if architecture in ["Not detected", "Unknown", "Error", "Analyzing..."]:
            if not DarkMessageBox.question(
                self.window, 
                "Architecture Not Detected", 
                "Could not detect if your game is 32-bit or 64-bit.\n\n"
                "Installation may fail. Do you want to continue anyway?\n\n"
                "Tip: Make sure you selected the folder containing the game's main .exe file."
            ):
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
        
        # Show confirmation dialog with details
        confirm_msg = (
            f"Ready to install DXVK for:\n\n"
            f"Game Folder: {folder}\n"
            f"Architecture: {architecture}\n"
            f"DirectX Version: {directx_version}\n\n"
            f"This will:\n"
            f"• Download the latest DXVK from GitHub\n"
            f"• Create a backup of existing DLLs\n"
            f"• Install DXVK DLLs to your game folder\n\n"
            f"Make sure your game is NOT running.\n\n"
            f"Continue with installation?"
        )
        
        if not DarkMessageBox.question(
            self.window,
            "Confirm Installation",
            confirm_msg
        ):
            return
        
        backup_enabled = True  # Always enabled
        
        # Disable buttons
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)
        self.install_btn.setText("Installing...")
        
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
        self.install_btn.setText("4. Install DXVK")
        
        if success:
            DarkMessageBox.information(
                self.window, 
                "Installation Complete!", 
                f"{message}\n\n"
                f"✓ DXVK has been installed successfully\n"
                f"✓ Original DLLs backed up to 'dxvk_backup' folder\n\n"
                f"You can now launch your game.\n"
                f"DXVK should improve graphics performance!"
            )
        else:
            DarkMessageBox.critical(
                self.window, 
                "Installation Failed", 
                f"{message}\n\n"
                f"Common causes:\n"
                f"• Game folder requires administrator privileges\n"
                f"• Game is currently running (close it first)\n"
                f"• Antivirus blocking the installation\n"
                f"• No internet connection\n\n"
                f"Check the Activity Log below for detailed error information."
            )

    def uninstall_dxvk(self):
        """Uninstall DXVK."""
        folder = self.folder_input.text()
        if not folder:
            DarkMessageBox.critical(self.window, "Error", "Please select a game folder first.")
            return
        
        if not DarkMessageBox.question(
            self.window,
            "Confirm Uninstall",
            "Are you sure you want to uninstall DXVK and restore backups?\n\n"
            "This will restore the original DirectX DLL files from backup."
        ):
            return
        
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
                DarkMessageBox.information(
                    self.window, 
                    "Success", 
                    "DXVK uninstalled successfully!\nOriginal DLL files have been restored."
                )
            else:
                self.log_message("")
                self.log_message("✗ DXVK uninstallation failed or no backup found.")
                DarkMessageBox.warning(
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
            DarkMessageBox.critical(self.window, "Error", f"Uninstallation error:\n{error_msg}")

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
