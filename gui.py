import sys
import os
import io
import webbrowser
import urllib.parse
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
    
    def __init__(self, manager, game_folder, architecture, directx_version, backup_enabled,
                 source='official', version=None):
        super().__init__()
        self.manager = manager
        self.game_folder = game_folder
        self.architecture = architecture
        self.directx_version = directx_version
        self.backup_enabled = backup_enabled
        self.source = source
        self.version = version
    
    def run(self):
        """Run the installation in the background thread."""
        try:
            self.log_signal.emit("Starting DXVK installation...")
            self.log_signal.emit(f"Game folder: {self.game_folder}")
            self.log_signal.emit(f"Architecture: {self.architecture}")
            self.log_signal.emit(f"DirectX version: {self.directx_version}")
            self.log_signal.emit(f"Source: {self.source}")
            self.log_signal.emit(f"Version: {self.version or 'Latest'}")
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
                        self.backup_enabled,
                        source=self.source,
                        version=self.version
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

class ReleaseFetchThread(QThread):
    """Fetches the recent release list for a DXVK source without blocking the UI."""
    releases_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, source_key, limit=10):
        super().__init__()
        self.source_key = source_key
        self.limit = limit

    def run(self):
        try:
            from github_downloader import get_downloader
            downloader = get_downloader(self.source_key)
            releases = downloader.get_releases(limit=self.limit)
            if self.isInterruptionRequested():
                return
            self.releases_signal.emit(releases)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error_signal.emit(str(e))


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

        install_outer = QWidget()
        install_outer.setStyleSheet("background: transparent;")
        install_outer_layout = QVBoxLayout(install_outer)
        install_outer_layout.setContentsMargins(0, 0, 0, 0)
        install_outer_layout.setSpacing(0)

        install_scroll = QScrollArea()
        install_scroll.setWidgetResizable(True)
        install_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        install_scroll.setFrameShape(QFrame.Shape.NoFrame)
        install_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1A1A1A; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #3A3A3A; border-radius: 5px; min-height: 24px; }
            QScrollBar::handle:vertical:hover { background: #4A4A4A; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        install_tab = QWidget()
        install_tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(install_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 12, 6, 12)

        install_scroll.setWidget(install_tab)
        install_outer_layout.addWidget(install_scroll)

        # Use the shared card/row helpers so Install matches Config Editor's look
        make_group = self._make_group
        row = self._add_row
        COMBO_STYLE = self._COMBO_STYLE
        CHECK_STYLE = self._CHECK_STYLE

        layout.setSpacing(10)

        # ── Game folder card ─────────────────────────────────
        card_folder, g_folder = make_group("GAME FOLDER")

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("Click Browse to select your game folder...")
        self.folder_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px; border: 1px solid #3A3A3A; border-radius: 5px;
                background-color: #1A1A1A; color: #FFFFFF; min-height: 22px;
            }
            QLineEdit:focus { border: 1px solid #00A2FF; }
        """)
        folder_row.addWidget(self.folder_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Select the folder where your game is installed")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white; border: none;
                padding: 7px 18px; border-radius: 5px; font-weight: 600; font-size: 9.5pt;
                min-height: 22px;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:pressed { background-color: #005A9E; }
        """)
        browse_btn.clicked.connect(self.browse_game_folder)
        folder_row.addWidget(browse_btn, 0)
        g_folder.addLayout(folder_row)

        # PCGamingWiki button — made prominent with brand-ish teal accent + icon
        wiki_btn = QPushButton("🌐  View on PCGamingWiki")
        wiki_btn.setToolTip("Search PCGamingWiki for this game's compatibility info, fixes, and tweaks")
        wiki_btn.setEnabled(False)
        wiki_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wiki_btn.setStyleSheet("""
            QPushButton {
                background-color: #144D3A;
                color: #4DE8B0;
                border: 1px solid #1E8A5F;
                padding: 8px 14px;
                border-radius: 5px;
                font-weight: 700;
                font-size: 9.5pt;
                text-align: left;
            }
            QPushButton:hover:enabled {
                background-color: #1B6B4D;
                color: #6DFFCB;
                border: 1px solid #2FE49A;
            }
            QPushButton:pressed:enabled {
                background-color: #0F3A2B;
            }
            QPushButton:disabled {
                background-color: #1E1E1E;
                color: #4A4A4A;
                border: 1px solid #2E2E2E;
            }
        """)
        wiki_btn.clicked.connect(self._open_pcgamingwiki)
        self.wiki_btn = wiki_btn
        g_folder.addWidget(wiki_btn)
        layout.addWidget(card_folder)

        # ── Detection card ────────────────────────────────────
        card_detect, g_detect = make_group("DETECTION")

        self.architecture_label = QLabel("Not detected")
        self.architecture_label.setStyleSheet("""
            QLabel {
                color: #00A2FF; font-weight: 600; padding: 4px 10px;
                background-color: #1A3A4D; border-radius: 5px; min-height: 18px;
            }
        """)
        row(g_detect, "Architecture", self.architecture_label)

        self.directx_label = QLabel("Not detected")
        self.directx_label.setStyleSheet("""
            QLabel {
                color: #00A2FF; font-weight: 600; padding: 4px 10px;
                background-color: #1A3A4D; border-radius: 5px; min-height: 18px;
            }
        """)
        row(g_detect, "DirectX Version", self.directx_label)

        self.directx_combo = QComboBox()
        self.directx_combo.addItems(["Auto-detect", "Direct3D 9", "Direct3D 10", "Direct3D 11"])
        self.directx_combo.setToolTip("Manually select DirectX version if auto-detection fails")
        self.directx_combo.setStyleSheet(COMBO_STYLE)
        row(g_detect, "Override", self.directx_combo, "Use if auto-detection picks the wrong version.")
        layout.addWidget(card_detect)

        # ── DXVK Source card ────────────────────────────────────
        card_source, g_source = make_group("DXVK SOURCE")

        self.source_combo = QComboBox()
        self.source_combo.addItem("Official (doitsujin/dxvk)", "official")
        self.source_combo.addItem("GPLAsync (Ph42oN)", "gplasync")
        self.source_combo.setToolTip("Choose which DXVK build to install")
        self.source_combo.setStyleSheet(COMBO_STYLE)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        row(g_source, "Source", self.source_combo)

        self.version_combo = QComboBox()
        self.version_combo.addItem("Latest", None)
        self.version_combo.setToolTip("Choose a specific version, or Latest for the newest release")
        self.version_combo.setStyleSheet(COMBO_STYLE)
        row(g_source, "Version", self.version_combo, "Loading available versions...")
        layout.addWidget(card_source)

        self._release_fetch_thread = None
        self._fetch_releases_for_source("official")

        # ── Safety card ───────────────────────────────────────
        card_safety, g_safety = make_group("SAFETY")
        backup_row = QHBoxLayout()
        backup_row.setSpacing(6)
        self.backup_checkbox = QCheckBox("Create backup before installing")
        self.backup_checkbox.setChecked(True)
        self.backup_checkbox.setEnabled(False)  # Locked on — always backs up for safety
        self.backup_checkbox.setStyleSheet(CHECK_STYLE)
        backup_row.addWidget(self.backup_checkbox)
        lock_lbl = QLabel("🔒 Always on")
        lock_lbl.setStyleSheet("color: #6E9E7E; font-size: 8pt; font-weight: 600;")
        lock_lbl.setToolTip("Backup can't be disabled — this keeps your original DLLs safe to restore anytime.")
        backup_row.addWidget(lock_lbl)
        backup_row.addStretch()
        g_safety.addLayout(backup_row)
        layout.addWidget(card_safety)

        # ── Action buttons ────────────────────────────────────
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)

        self.install_btn = QPushButton("Install DXVK")
        self.install_btn.setToolTip("Downloads and installs DXVK DLLs to your game folder")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white; border: none;
                padding: 12px; border-radius: 6px; font-weight: 600; font-size: 11pt;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:pressed { background-color: #005A9E; }
            QPushButton:disabled { background-color: #404040; color: #808080; }
        """)
        self.install_btn.clicked.connect(self.install_dxvk)
        button_layout.addWidget(self.install_btn)

        self.uninstall_btn = QPushButton("Restore Original DLLs")
        self.uninstall_btn.setToolTip("Restores the original DirectX DLLs from backup")
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D; color: #C8C8C8; border: 1px solid #3A3A3A;
                padding: 9px; border-radius: 6px; font-weight: 500; font-size: 9.5pt;
            }
            QPushButton:hover { background-color: #3A3A3A; color: #FFF; }
            QPushButton:pressed { background-color: #262626; }
            QPushButton:disabled { background-color: #202020; color: #5A5A5A; }
        """)
        self.uninstall_btn.clicked.connect(self.uninstall_dxvk)
        button_layout.addWidget(self.uninstall_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        self.left_tabs.addTab(install_outer, "Install")
        self.left_tabs.addTab(self._create_conf_tab(), "Config Editor")

        return panel

    # ── Shared modern card/row styling (used by Install and Config Editor tabs) ──
    _COMBO_STYLE = """
        QComboBox {
            padding: 5px 8px; border: 1px solid #3A3A3A; border-radius: 5px;
            background-color: #1A1A1A; color: #FFFFFF; min-height: 22px;
        }
        QComboBox:hover { border-color: #00A2FF; }
        QComboBox::drop-down { border: none; background: transparent; width: 22px; }
        QComboBox QAbstractItemView {
            background-color: #242424; color: #FFFFFF;
            selection-background-color: #0078D4; border: 1px solid #3A3A3A;
            border-radius: 4px;
        }"""
    _SPIN_STYLE = """
        QSpinBox {
            padding: 5px 8px; border: 1px solid #3A3A3A; border-radius: 5px;
            background-color: #1A1A1A; color: #FFFFFF; min-height: 22px;
        }
        QSpinBox:hover { border-color: #00A2FF; }
        QSpinBox::up-button, QSpinBox::down-button { background: transparent; border: none; width: 16px; }"""
    _CHECK_STYLE = """
        QCheckBox { color: #E0E0E0; spacing: 8px; font-size: 9.5pt; min-height: 20px; }
        QCheckBox::indicator {
            width: 16px; height: 16px; border: 2px solid #3A3A3A;
            border-radius: 4px; background-color: #1A1A1A;
        }
        QCheckBox::indicator:checked { background-color: #00A2FF; border: 2px solid #00A2FF; }
        QCheckBox::indicator:hover { border-color: #00A2FF; }
        QCheckBox::indicator:disabled { background-color: #2A2A2A; border: 2px solid #2E2E2E; }"""
    _ROW_LABEL_STYLE = "color: #C8C8C8; font-size: 9.5pt; font-weight: 500;"
    _GROUP_TITLE_STYLE = "color: #00A2FF; font-size: 8.5pt; font-weight: 700; letter-spacing: 0.5px;"

    def _make_group(self, title):
        """A flat card-style section container with a small header. Returns (card, inner_layout)."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background-color: #1E1E1E; border: 1px solid #2E2E2E; border-radius: 8px; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)
        header = QLabel(title)
        header.setStyleSheet(self._GROUP_TITLE_STYLE)
        card_layout.addWidget(header)
        grid = QVBoxLayout()
        grid.setSpacing(10)
        card_layout.addLayout(grid)
        return card, grid

    def _add_row(self, grid, label_text, widget, hint_text=None):
        """A single compact label+control row, optional one-line hint."""
        r = QHBoxLayout()
        r.setSpacing(8)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(self._ROW_LABEL_STYLE)
        lbl.setMinimumWidth(108)
        lbl.setWordWrap(True)
        r.addWidget(lbl, 0)
        r.addWidget(widget, 1)
        widget.setMinimumHeight(26)
        grid.addLayout(r)
        if hint_text:
            hint = QLabel(hint_text)
            hint.setStyleSheet("color: #6E6E6E; font-size: 7.5pt;")
            hint.setWordWrap(True)
            grid.addWidget(hint)

    def _create_conf_tab(self):
        """Build the dxvk.conf editor tab — compact modern grid, scrollable."""
        COMBO_STYLE = self._COMBO_STYLE
        SPIN_STYLE = self._SPIN_STYLE
        CHECK_STYLE = self._CHECK_STYLE

        outer_tab = QWidget()
        outer_tab.setStyleSheet("background: transparent;")
        outer_layout = QVBoxLayout(outer_tab)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1A1A1A; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #3A3A3A; border-radius: 5px; min-height: 24px; }
            QScrollBar::handle:vertical:hover { background: #4A4A4A; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 10, 6, 10)

        scroll.setWidget(tab)
        outer_layout.addWidget(scroll)

        # Status pill
        self.conf_status = QLabel("No game folder selected.")
        self.conf_status.setStyleSheet("""
            color: #888888; font-size: 8.5pt; padding: 6px 10px;
            background-color: #1A1A1A; border-radius: 5px;
        """)
        self.conf_status.setWordWrap(True)
        layout.addWidget(self.conf_status)

        make_group = self._make_group
        row = self._add_row

        # ── Rendering group: HUD + Tear-Free ─────────────────
        card1, g1 = make_group("RENDERING")
        self.conf_hud = QComboBox()
        self.conf_hud.addItems(["Off", "FPS", "Full", "Custom"])
        self.conf_hud.setStyleSheet(COMBO_STYLE)
        self.conf_hud.currentTextChanged.connect(self._on_hud_changed)
        row(g1, "HUD Display", self.conf_hud)
        self.conf_hud_custom = QLineEdit()
        self.conf_hud_custom.setPlaceholderText("e.g. fps,frametimes,gpuload")
        self.conf_hud_custom.setStyleSheet(
            "padding:5px 8px; border:1px solid #3A3A3A; border-radius:5px; background:#1A1A1A; color:#FFF;")
        self.conf_hud_custom.setVisible(False)
        g1.addWidget(self.conf_hud_custom)

        self.conf_tearfree = QComboBox()
        self.conf_tearfree.addItems(["Auto", "On", "Off"])
        self.conf_tearfree.setStyleSheet(COMBO_STYLE)
        row(g1, "Tear-Free (VSync)", self.conf_tearfree)
        layout.addWidget(card1)

        # ── Shader compilation group ───────────────────────────
        card2, g2 = make_group("SHADER COMPILATION")
        self.conf_async = QCheckBox("Enable async shader compilation")
        self.conf_async.setStyleSheet(CHECK_STYLE)
        g2.addWidget(self.conf_async)

        self.conf_async_threads = QSpinBox()
        self.conf_async_threads.setRange(0, 32)
        self.conf_async_threads.setSpecialValueText("Auto")
        self.conf_async_threads.setStyleSheet(SPIN_STYLE)
        row(g2, "Async Threads", self.conf_async_threads)

        self.conf_threads = QSpinBox()
        self.conf_threads.setRange(0, 32)
        self.conf_threads.setSpecialValueText("Auto")
        self.conf_threads.setStyleSheet(SPIN_STYLE)
        row(g2, "Sync Threads", self.conf_threads)

        self.conf_shadercache = QCheckBox("Enable on-disk shader cache")
        self.conf_shadercache.setChecked(True)
        self.conf_shadercache.setStyleSheet(CHECK_STYLE)
        g2.addWidget(self.conf_shadercache)
        layout.addWidget(card2)

        # ── Frame rate group ────────────────────────────────────
        card2b, g2b = make_group("FRAME RATE")
        self.conf_fps = QSpinBox()
        self.conf_fps.setRange(0, 999)
        self.conf_fps.setSpecialValueText("Unlimited")
        self.conf_fps.setSuffix(" fps")
        self.conf_fps.setStyleSheet(SPIN_STYLE)
        row(g2b, "Frame Rate Cap", self.conf_fps)
        layout.addWidget(card2b)

        # ── Memory group ───────────────────────────────────────
        card3, g3 = make_group("MEMORY")
        self.conf_vram = QSpinBox()
        self.conf_vram.setRange(0, 65536)
        self.conf_vram.setSingleStep(512)
        self.conf_vram.setSpecialValueText("Unlimited")
        self.conf_vram.setSuffix(" MB")
        self.conf_vram.setStyleSheet(SPIN_STYLE)
        row(g3, "Max VRAM", self.conf_vram, "Caps reported VRAM — helps GPUs with limited memory.")
        layout.addWidget(card3)

        # ── Debug group ────────────────────────────────────────
        card4, g4 = make_group("DEBUG")
        self.conf_loglevel = QComboBox()
        self.conf_loglevel.addItems(["none", "error", "warn", "info", "debug"])
        self.conf_loglevel.setStyleSheet(COMBO_STYLE)
        row(g4, "Log Level", self.conf_loglevel)
        layout.addWidget(card4)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        save_btn = QPushButton("Save Config")
        save_btn.setStyleSheet("""
            QPushButton { background:#0078D4; color:white; border:none;
                padding:9px 22px; border-radius:6px; font-weight:600; font-size:9.5pt; }
            QPushButton:hover { background:#106EBE; }
            QPushButton:pressed { background:#005A9E; }""")
        save_btn.clicked.connect(self._save_conf)
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("""
            QPushButton { background:#2D2D2D; color:#C8C8C8; border:1px solid #3A3A3A;
                padding:9px 18px; border-radius:6px; font-weight:500; font-size:9.5pt; }
            QPushButton:hover { background:#3A3A3A; color:#FFF; }""")
        reset_btn.clicked.connect(self._reset_conf_defaults)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return outer_tab
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

    def _guess_game_name(self, folder):
        """Turn a folder path into a readable guessed game name."""
        name = os.path.basename(os.path.normpath(folder))
        # Replace separators commonly found in folder names with spaces
        for ch in ["_", "-", "."]:
            name = name.replace(ch, " ")
        # Collapse extra whitespace
        name = " ".join(name.split())
        return name

    def _update_wiki_button(self, folder):
        """Enable the PCGamingWiki button, keeping its label short and fixed."""
        game_name = self._guess_game_name(folder)
        self._wiki_game_name = game_name
        self.wiki_btn.setEnabled(True)
        self.wiki_btn.setText("🌐  Search PCGamingWiki")

    def _open_pcgamingwiki(self):
        """Open PCGamingWiki search for the currently detected game name."""
        game_name = getattr(self, "_wiki_game_name", None)
        if not game_name:
            return
        query = urllib.parse.quote_plus(game_name)
        url = f"https://www.pcgamingwiki.com/w/index.php?search={query}"
        webbrowser.open(url)
        self.log_message(f"Opened PCGamingWiki search for: {game_name}")

    def _on_source_changed(self, index):
        """Re-fetch the version list when the DXVK source is switched."""
        source_key = self.source_combo.currentData()
        self._fetch_releases_for_source(source_key)

    def _fetch_releases_for_source(self, source_key):
        """Kick off a background fetch of recent releases for the given source."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItem("Latest", None)
        self.version_combo.addItem("Loading versions...", None)
        loading_item = self.version_combo.model().item(1)
        if loading_item is not None:
            loading_item.setEnabled(False)
        self.version_combo.blockSignals(False)

        if self._release_fetch_thread and self._release_fetch_thread.isRunning():
            self._release_fetch_thread.requestInterruption()
            self._release_fetch_thread.wait()

        self._release_fetch_thread = ReleaseFetchThread(source_key, limit=10)
        self._release_fetch_thread.releases_signal.connect(self._on_releases_fetched)
        self._release_fetch_thread.error_signal.connect(self._on_releases_fetch_error)
        self._release_fetch_thread.start()

    def _on_releases_fetched(self, releases):
        """Populate the version dropdown once the release list arrives."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItem("Latest", None)
        for r in releases:
            self.version_combo.addItem(r["name"], r["tag_name"])
        self.version_combo.blockSignals(False)
        self.log_message(f"Loaded {len(releases)} available DXVK version(s).")

    def _on_releases_fetch_error(self, error_message):
        """Fall back to just 'Latest' if the version list couldn't be fetched."""
        self.version_combo.blockSignals(True)
        self.version_combo.clear()
        self.version_combo.addItem("Latest", None)
        self.version_combo.blockSignals(False)
        self.log_message(f"Could not load version list ({error_message}). You can still install the latest version.")

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
        self._update_wiki_button(folder)

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
        
        # Determine DXVK source and version
        source_key = self.source_combo.currentData()
        source_label = self.source_combo.currentText()
        version_tag = self.version_combo.currentData()
        version_label = self.version_combo.currentText()

        # Show confirmation dialog with details
        confirm_msg = (
            f"Ready to install DXVK for:\n\n"
            f"Game Folder: {folder}\n"
            f"Architecture: {architecture}\n"
            f"DirectX Version: {directx_version}\n"
            f"Source: {source_label}\n"
            f"Version: {version_label}\n\n"
            f"This will:\n"
            f"• Download DXVK ({version_label}) from {source_label}\n"
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
            self.manager, folder, architecture, directx_version, backup_enabled,
            source=source_key, version=version_tag
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