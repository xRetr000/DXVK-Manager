import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QDialog,
    QTabWidget, QSpinBox, QListWidget
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

            if self.isInterruptionRequested():
                return

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

                if self.isInterruptionRequested():
                    return
                
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
    exe_picker_signal = pyqtSignal(list)  # emitted when multiple .exe files found
    
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

            if self.isInterruptionRequested():
                return

            # Find .exe files (Windows only)
            exe_files = []

            # Search recursively (limited depth)
            for root, dirs, files in os.walk(self.folder):
                if self.isInterruptionRequested():
                    return
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
                self.log_signal.emit("Please select the main game executable from the list.")
                self.exe_picker_signal.emit(exe_files)
                return  # GUI will handle the rest after user picks

            if self.isInterruptionRequested():
                return

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

        # Windows groups taskbar icons by AppUserModelID. Without setting a unique
        # one, Windows falls back to the Python interpreter's icon in the taskbar
        # even though the window icon and .exe icon are set correctly.
        if sys.platform == "win32":
            try:
                import ctypes
                app_id = "xRetr000.DXVKManager.GUI.1"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception:
                pass

        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Use Windows native style for Windows 11 look
        self.app.setStyle('windowsvista')  # Windows 11 compatible native style
        icon = QIcon(self._resource_path("icon.ico"))
        self.app.setWindowIcon(icon)

        self.window = QMainWindow()
        self.window.setWindowTitle("DXVK Manager")
        self.window.setWindowIcon(icon)
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
        self.current_folder = None
    
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
    
    @staticmethod
    def _resource_path(relative_path):
        """Get absolute path to a resource, works for dev and for PyInstaller .exe."""
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def create_left_panel(self):
        """Create the left control panel with tabs."""
        panel = ModernCard()
        outer_layout = QVBoxLayout(panel)
        outer_layout.setSpacing(12)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("DXVK Manager")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 4px;")
        outer_layout.addWidget(title)

        # Tab widget
        self.left_tabs = QTabWidget()
        self.left_tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: #3A3A3A;
                color: #B0B0B0;
                padding: 7px 18px;
                border-radius: 4px;
                margin-right: 4px;
                font-size: 10pt;
                font-weight: 500;
            }
            QTabBar::tab:selected { background: #0078D4; color: #FFFFFF; }
            QTabBar::tab:hover:!selected { background: #4A4A4A; color: #FFFFFF; }
        """)
        outer_layout.addWidget(self.left_tabs)

        install_tab = QWidget()
        install_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(install_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 12, 0, 0)

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

        self.left_tabs.addTab(install_tab, "Install")
        self.left_tabs.addTab(self._create_conf_tab(), "Config Editor")

        return panel

    def _create_conf_tab(self):
        """Build the dxvk.conf editor tab with common optimization options."""
        COMBO_STYLE = """
            QComboBox {
                padding: 6px 8px; border: 1px solid #404040; border-radius: 4px;
                background-color: #1E1E1E; color: #FFFFFF;
            }
            QComboBox:hover { border-color: #00A2FF; }
            QComboBox::drop-down { border: none; background: #2D2D2D; }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D; color: #FFFFFF;
                selection-background-color: #0078D4; border: 1px solid #404040;
            }"""
        SPIN_STYLE = """
            QSpinBox {
                padding: 6px 8px; border: 1px solid #404040; border-radius: 4px;
                background-color: #1E1E1E; color: #FFFFFF;
            }
            QSpinBox:hover { border-color: #00A2FF; }
            QSpinBox::up-button, QSpinBox::down-button { background: #2D2D2D; border: none; }"""
        CHECK_STYLE = """
            QCheckBox { color: #E0E0E0; spacing: 8px; }
            QCheckBox::indicator {
                width: 18px; height: 18px; border: 2px solid #404040;
                border-radius: 3px; background-color: #1E1E1E;
            }
            QCheckBox::indicator:checked { background-color: #00A2FF; border: 2px solid #00A2FF; }
            QCheckBox::indicator:hover { border-color: #00A2FF; }"""
        SEC_STYLE  = "color: #E0E0E0; font-weight: 600; font-size: 10pt; margin-top: 4px;"
        HINT_STYLE = "color: #888888; font-size: 8pt;"

        tab = QWidget()
        tab.setStyleSheet("background: transparent;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(inner)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 4, 12)

        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Status label
        self.conf_status = QLabel("No game folder selected.")
        self.conf_status.setStyleSheet("color: #888888; font-size: 9pt;")
        self.conf_status.setWordWrap(True)
        layout.addWidget(self.conf_status)

        # ── HUD ──────────────────────────────
        layout.addWidget(self._label("HUD Display", SEC_STYLE))
        self.conf_hud = QComboBox()
        self.conf_hud.addItems(["Off", "FPS", "Full", "Custom"])
        self.conf_hud.setStyleSheet(COMBO_STYLE)
        self.conf_hud.currentTextChanged.connect(self._on_hud_changed)
        layout.addWidget(self.conf_hud)
        self.conf_hud_custom = QLineEdit()
        self.conf_hud_custom.setPlaceholderText("e.g. fps,frametimes,gpuload")
        self.conf_hud_custom.setStyleSheet(
            "padding:6px; border:1px solid #404040; border-radius:4px; background:#1E1E1E; color:#FFF;")
        self.conf_hud_custom.setVisible(False)
        layout.addWidget(self.conf_hud_custom)

        # ── Async shader compilation ──────────
        layout.addWidget(self._label("Async Shader Compilation", SEC_STYLE))
        self.conf_async = QCheckBox("Enable async (reduces stuttering)")
        self.conf_async.setStyleSheet(CHECK_STYLE)
        layout.addWidget(self.conf_async)
        hint = QLabel("Compiles shaders in background. May cause brief visual glitches on first play.")
        hint.setStyleSheet(HINT_STYLE)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ── Async compiler threads (separate from sync) ──
        layout.addWidget(self._label("Async Compiler Threads", SEC_STYLE))
        self.conf_async_threads = QSpinBox()
        self.conf_async_threads.setRange(0, 32)
        self.conf_async_threads.setSpecialValueText("Auto")
        self.conf_async_threads.setStyleSheet(SPIN_STYLE)
        layout.addWidget(self.conf_async_threads)
        hint_at = QLabel("Threads dedicated to async shader compilation. 0 = auto.")
        hint_at.setStyleSheet(HINT_STYLE)
        layout.addWidget(hint_at)

        # ── Frame rate cap ────────────────────
        layout.addWidget(self._label("Frame Rate Cap", SEC_STYLE))
        self.conf_fps = QSpinBox()
        self.conf_fps.setRange(0, 999)
        self.conf_fps.setSpecialValueText("Unlimited")
        self.conf_fps.setSuffix(" fps")
        self.conf_fps.setStyleSheet(SPIN_STYLE)
        layout.addWidget(self.conf_fps)
        hint2 = QLabel("0 = no cap. Useful for reducing power draw / heat on laptops.")
        hint2.setStyleSheet(HINT_STYLE)
        hint2.setWordWrap(True)
        layout.addWidget(hint2)

        # ── Sync compiler threads ─────────────
        layout.addWidget(self._label("Sync Compiler Threads", SEC_STYLE))
        self.conf_threads = QSpinBox()
        self.conf_threads.setRange(0, 32)
        self.conf_threads.setSpecialValueText("Auto")
        self.conf_threads.setStyleSheet(SPIN_STYLE)
        layout.addWidget(self.conf_threads)
        hint3 = QLabel("Threads used to compile shaders synchronously. 0 = based on CPU cores.")
        hint3.setStyleSheet(HINT_STYLE)
        hint3.setWordWrap(True)
        layout.addWidget(hint3)

        # ── Max device memory (VRAM budget) ───
        layout.addWidget(self._label("Max Device Memory (VRAM)", SEC_STYLE))
        self.conf_vram = QSpinBox()
        self.conf_vram.setRange(0, 65536)
        self.conf_vram.setSingleStep(512)
        self.conf_vram.setSpecialValueText("Unlimited")
        self.conf_vram.setSuffix(" MB")
        self.conf_vram.setStyleSheet(SPIN_STYLE)
        layout.addWidget(self.conf_vram)
        hint_v = QLabel("Caps VRAM DXVK reports to the game. Helps on GPUs with limited VRAM. 0 = unlimited.")
        hint_v.setStyleSheet(HINT_STYLE)
        hint_v.setWordWrap(True)
        layout.addWidget(hint_v)

        # ── Tear-free / VSync ──────────────────
        layout.addWidget(self._label("Tear-Free (VSync)", SEC_STYLE))
        self.conf_tearfree = QComboBox()
        self.conf_tearfree.addItems(["Auto", "On", "Off"])
        self.conf_tearfree.setStyleSheet(COMBO_STYLE)
        layout.addWidget(self.conf_tearfree)

        # ── Shader cache ───────────────────────
        layout.addWidget(self._label("On-Disk Shader Cache", SEC_STYLE))
        self.conf_shadercache = QCheckBox("Enable shader cache (faster reloads)")
        self.conf_shadercache.setChecked(True)
        self.conf_shadercache.setStyleSheet(CHECK_STYLE)
        layout.addWidget(self.conf_shadercache)

        # ── Log level ─────────────────────────
        layout.addWidget(self._label("Log Level", SEC_STYLE))
        self.conf_loglevel = QComboBox()
        self.conf_loglevel.addItems(["none", "error", "warn", "info", "debug"])
        self.conf_loglevel.setStyleSheet(COMBO_STYLE)
        layout.addWidget(self.conf_loglevel)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Config")
        save_btn.setStyleSheet("""
            QPushButton { background:#0078D4; color:white; border:none;
                padding:9px 20px; border-radius:5px; font-weight:600; }
            QPushButton:hover { background:#106EBE; }
            QPushButton:pressed { background:#005A9E; }""")
        save_btn.clicked.connect(self._save_conf)
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setStyleSheet("""
            QPushButton { background:#5A5A5A; color:white; border:none;
                padding:9px 20px; border-radius:5px; font-weight:500; }
            QPushButton:hover { background:#6A6A6A; }""")
        reset_btn.clicked.connect(self._reset_conf_defaults)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return tab

    def _label(self, text, style):
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        return lbl

    def _on_hud_changed(self, value):
        self.conf_hud_custom.setVisible(value == "Custom")

    def _load_conf(self, folder):
        """Parse dxvk.conf from the game folder and update UI controls."""
        conf_path = os.path.join(folder, "dxvk.conf")
        defaults = {
            "dxvk.hud": "0",
            "dxvk.enableAsync": "False",
            "dxvk.numAsyncThreads": "0",
            "dxvk.maxFrameRate": "0",
            "dxvk.numCompilerThreads": "0",
            "dxvk.maxDeviceMemory": "0",
            "dxvk.tearFree": "Auto",
            "dxvk.shaderCache": "True",
            "dxvk.logLevel": "none",
        }
        values = dict(defaults)

        if os.path.exists(conf_path):
            try:
                with open(conf_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, _, v = line.partition("=")
                            k, v = k.strip(), v.strip()
                            if k in values:
                                values[k] = v
                self.conf_status.setText(f"Loaded: {conf_path}")
                self.conf_status.setStyleSheet("color: #4CAF50; font-size: 9pt;")
            except Exception as e:
                self.conf_status.setText(f"Error reading config: {e}")
                self.conf_status.setStyleSheet("color: #E81123; font-size: 9pt;")
        else:
            self.conf_status.setText("No dxvk.conf found — will create one on save.")
            self.conf_status.setStyleSheet("color: #FFB900; font-size: 9pt;")

        # Apply to UI
        hud_val = values["dxvk.hud"]
        if hud_val in ("0", ""):
            self.conf_hud.setCurrentText("Off")
        elif hud_val == "1":
            self.conf_hud.setCurrentText("FPS")
        elif hud_val == "full":
            self.conf_hud.setCurrentText("Full")
        else:
            self.conf_hud.setCurrentText("Custom")
            self.conf_hud_custom.setText(hud_val)

        self.conf_async.setChecked(values["dxvk.enableAsync"].lower() == "true")

        for spin, key in [
            (self.conf_async_threads, "dxvk.numAsyncThreads"),
            (self.conf_fps, "dxvk.maxFrameRate"),
            (self.conf_threads, "dxvk.numCompilerThreads"),
            (self.conf_vram, "dxvk.maxDeviceMemory"),
        ]:
            try:
                spin.setValue(int(values[key]))
            except ValueError:
                spin.setValue(0)

        tear_val = values["dxvk.tearFree"].capitalize()
        idx = self.conf_tearfree.findText(tear_val if tear_val in ("On", "Off") else "Auto")
        self.conf_tearfree.setCurrentIndex(idx if idx >= 0 else 0)

        self.conf_shadercache.setChecked(values["dxvk.shaderCache"].lower() != "false")

        log = values["dxvk.logLevel"]
        idx = self.conf_loglevel.findText(log)
        self.conf_loglevel.setCurrentIndex(idx if idx >= 0 else 0)

    def _save_conf(self):
        """Write dxvk.conf to the current game folder."""
        folder = self.folder_input.text()
        if not folder:
            DarkMessageBox.warning(self.window, "No Folder", "Select a game folder in the Install tab first.")
            return

        hud_choice = self.conf_hud.currentText()
        if hud_choice == "Off":
            hud_val = "0"
        elif hud_choice == "FPS":
            hud_val = "1"
        elif hud_choice == "Full":
            hud_val = "full"
        else:
            hud_val = self.conf_hud_custom.text().strip() or "0"

        lines = [
            "# dxvk.conf - generated by DXVK Manager",
            "",
            f"dxvk.hud = {hud_val}",
            f"dxvk.enableAsync = {'True' if self.conf_async.isChecked() else 'False'}",
            f"dxvk.numAsyncThreads = {self.conf_async_threads.value()}",
            f"dxvk.maxFrameRate = {self.conf_fps.value()}",
            f"dxvk.numCompilerThreads = {self.conf_threads.value()}",
            f"dxvk.maxDeviceMemory = {self.conf_vram.value()}",
            f"dxvk.tearFree = {self.conf_tearfree.currentText()}",
            f"dxvk.shaderCache = {'True' if self.conf_shadercache.isChecked() else 'False'}",
            f"dxvk.logLevel = {self.conf_loglevel.currentText()}",
        ]

        conf_path = os.path.join(folder, "dxvk.conf")
        try:
            with open(conf_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            self.conf_status.setText(f"Saved: {conf_path}")
            self.conf_status.setStyleSheet("color: #4CAF50; font-size: 9pt;")
            self.log_message(f"dxvk.conf saved to {folder}")
            DarkMessageBox.information(self.window, "Saved", "dxvk.conf saved successfully!")
        except Exception as e:
            DarkMessageBox.critical(self.window, "Error", f"Could not save config:\n{e}")

    def _reset_conf_defaults(self):
        """Reset all conf fields to DXVK defaults."""
        self.conf_hud.setCurrentText("Off")
        self.conf_hud_custom.setText("")
        self.conf_async.setChecked(False)
        self.conf_async_threads.setValue(0)
        self.conf_fps.setValue(0)
        self.conf_threads.setValue(0)
        self.conf_vram.setValue(0)
        self.conf_tearfree.setCurrentText("Auto")
        self.conf_shadercache.setChecked(True)
        self.conf_loglevel.setCurrentText("none")

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
        self.current_folder = folder  # Store for use after exe picker
        self._load_conf(folder)  # Refresh the Config Editor tab for this folder

        # Reset detection
        self.architecture_label.setText("Analyzing...")
        self.directx_label.setText("Analyzing...")
        
        # Stop previous detection thread if running
        if self.detect_thread and self.detect_thread.isRunning():
            self.detect_thread.requestInterruption()
            self.detect_thread.wait()
        
        # Start new detection thread
        self.detect_thread = DetectionThread(folder)
        self.detect_thread.detected_signal.connect(self.on_detection_complete)
        self.detect_thread.log_signal.connect(self.log_message)
        self.detect_thread.exe_picker_signal.connect(self.show_exe_picker)
        self.detect_thread.start()
    
    def on_detection_complete(self, architecture, directx):
        """Handle detection results."""
        self.architecture_label.setText(architecture)
        self.directx_label.setText(directx)

    def show_exe_picker(self, exe_files):
        """Show a dialog to let the user pick the correct .exe when multiple are found."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout

        dialog = QDialog(self.window)
        dialog.setWindowTitle("Select Game Executable")
        dialog.setModal(True)
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet("""
            QDialog { background-color: #202020; color: #FFFFFF; }
            QLabel { color: #E0E0E0; }
            QListWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
            QListWidget::item:selected { background-color: #0078D4; }
            QListWidget::item:hover { background-color: #2A2A2A; }
            QPushButton {
                background-color: #0078D4; color: white;
                border: none; padding: 8px 20px;
                border-radius: 4px; font-weight: 600;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton#secondary {
                background-color: #5A5A5A;
            }
            QPushButton#secondary:hover { background-color: #6A6A6A; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info_label = QLabel("Multiple .exe files found.\nSelect the main game executable:")
        info_label.setStyleSheet("font-size: 10pt; color: #E0E0E0;")
        layout.addWidget(info_label)

        list_widget = QListWidget()
        for exe_path in exe_files:
            size_kb = os.path.getsize(exe_path) // 1024
            list_widget.addItem(f"{os.path.basename(exe_path)}  ({size_kb:,} KB)")
        list_widget.setCurrentRow(0)
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        confirm_btn = QPushButton("Use Selected")
        confirm_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_index = list_widget.currentRow()
            chosen_exe = exe_files[selected_index]
            self.log_message(f"Selected: {os.path.basename(chosen_exe)}")
            self.run_detection_with_exe(chosen_exe)
        else:
            self.architecture_label.setText("Not detected")
            self.directx_label.setText("Not detected")
            self.log_message("Exe selection cancelled.")

    def run_detection_with_exe(self, exe_path):
        """Run architecture detection on a specific exe the user picked."""
        try:
            from exe_analyzer import get_exe_architecture, detect_directx_version
            arch = get_exe_architecture(exe_path)
            self.log_message(f"Architecture detected: {arch}")

            folder = os.path.dirname(exe_path)
            dx_versions = detect_directx_version(folder)
            if dx_versions and dx_versions[0] != "Unknown":
                dx_text = ", ".join(dx_versions)
            else:
                dx_text = "Not detected"
            self.log_message(f"DirectX versions detected: {dx_text}")

            self.on_detection_complete(arch, dx_text)
        except Exception as e:
            self.log_message(f"Error during analysis: {str(e)}")
            self.architecture_label.setText("Error")
            self.directx_label.setText("Error")

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
            self.install_thread.requestInterruption()
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