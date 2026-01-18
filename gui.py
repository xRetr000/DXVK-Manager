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
            
            # Find executable files (.exe on Windows)
            exe_files = []
            
            # Windows-only: look for .exe files
            for root, dirs, files in os.walk(self.folder):
                depth = root[len(self.folder):].count(os.sep)
                if depth > 1:
                    dirs[:] = []
                
                for f in files:
                    if f.lower().endswith('.exe'):
                        exe_files.append(os.path.join(root, f))
            
            if not exe_files:
                # Check root folder directly
                try:
                    exe_files = [os.path.join(self.folder, f) 
                                for f in os.listdir(self.folder) 
                                if f.lower().endswith('.exe')]
                except PermissionError:
                    pass
            
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
    """A Windows 11 Fluent Design card widget with rounded corners."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E1E1E1;
            }
        """)

class DXVKManagerGUI:
    def __init__(self, manager):
        self.manager = manager
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        # Apply Windows 11 native style
        # Try Windows 11 native style first, fallback to Fusion
        try:
            self.app.setStyle('windows11')
        except:
            try:
                self.app.setStyle('windowsvista')
            except:
                self.app.setStyle('Fusion')
        
        self.window = QMainWindow()
        self.window.setWindowTitle("DXVK Manager")
        self.window.setMinimumSize(900, 650)
        self.window.resize(1000, 700)
        
        self.apply_windows11_theme()
        
        # Central widget
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        
        # Main layout (horizontal split) - Windows 11 spacing
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
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
        """Apply Windows 11 native Fluent Design theme with system colors."""
        # Use system colors for light/dark mode support
        palette = QPalette()
        
        # Windows 11 Fluent Design colors (adapts to system theme)
        # Light mode base colors
        palette.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(249, 249, 249))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))  # Windows accent color
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 215))
        
        self.app.setPalette(palette)
        
        # Windows 11 Fluent Design styling with rounded corners and proper spacing
        self.window.setStyleSheet("""
            QMainWindow {
                background-color: #F3F3F3;
            }
            QWidget {
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                font-size: 9pt;
            }
        """)
    
    def create_left_panel(self):
        """Create the left control panel."""
        panel = ModernCard()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title - Windows 11 typography
        title = QLabel("DXVK Manager")
        title_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #202020; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Game folder selection
        folder_label = QLabel("Game Folder:")
        folder_label.setStyleSheet("font-weight: 600; color: #323130; font-size: 9pt; margin-top: 8px;")
        layout.addWidget(folder_label)
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setPlaceholderText("Click Browse to select game folder...")
        self.folder_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #D2D0CE;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #323130;
                font-size: 9pt;
            }
            QLineEdit:focus {
                border: 2px solid #0078D4;
                padding: 9px 11px;
            }
            QLineEdit:hover {
                border-color: #8A8886;
            }
        """)
        folder_layout.addWidget(self.folder_input, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 9pt;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #E1E1E1;
                color: #8A8886;
            }
        """)
        browse_btn.clicked.connect(self.browse_game_folder)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)
        
        # Detection results card - Windows 11 info card
        detection_card = ModernCard()
        detection_layout = QVBoxLayout(detection_card)
        detection_layout.setSpacing(12)
        detection_layout.setContentsMargins(16, 16, 16, 16)
        
        detection_title = QLabel("Detection Results")
        detection_title_font = QFont("Segoe UI", 11, QFont.Weight.SemiBold)
        detection_title.setFont(detection_title_font)
        detection_title.setStyleSheet("color: #323130; margin-bottom: 4px;")
        detection_layout.addWidget(detection_title)
        
        # Architecture
        arch_layout = QHBoxLayout()
        arch_layout.setSpacing(8)
        arch_label = QLabel("Architecture:")
        arch_label.setStyleSheet("color: #605E5C; font-size: 9pt;")
        arch_layout.addWidget(arch_label)
        self.architecture_label = QLabel("Not detected")
        self.architecture_label.setStyleSheet("""
            QLabel {
                color: #0078D4;
                font-weight: 600;
                padding: 6px 12px;
                background-color: #E8F4F8;
                border-radius: 4px;
                font-size: 9pt;
            }
        """)
        arch_layout.addWidget(self.architecture_label)
        arch_layout.addStretch()
        detection_layout.addLayout(arch_layout)
        
        # DirectX version
        dx_layout = QHBoxLayout()
        dx_layout.setSpacing(8)
        dx_label = QLabel("DirectX Version:")
        dx_label.setStyleSheet("color: #605E5C; font-size: 9pt;")
        dx_layout.addWidget(dx_label)
        self.directx_label = QLabel("Not detected")
        self.directx_label.setStyleSheet("""
            QLabel {
                color: #0078D4;
                font-weight: 600;
                padding: 6px 12px;
                background-color: #E8F4F8;
                border-radius: 4px;
                font-size: 9pt;
            }
        """)
        dx_layout.addWidget(self.directx_label)
        dx_layout.addStretch()
        detection_layout.addLayout(dx_layout)
        
        layout.addWidget(detection_card)
        
        # DirectX override
        override_label = QLabel("Override DirectX Version:")
        override_label.setStyleSheet("font-weight: 600; color: #323130; font-size: 9pt; margin-top: 8px;")
        layout.addWidget(override_label)
        
        self.directx_combo = QComboBox()
        self.directx_combo.addItems(["Auto-detect", "Direct3D 9", "Direct3D 10", "Direct3D 11"])
        self.directx_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #D2D0CE;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #323130;
                font-size: 9pt;
            }
            QComboBox:hover {
                border-color: #8A8886;
            }
            QComboBox:focus {
                border: 2px solid #0078D4;
                padding: 9px 11px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #323130;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #323130;
                selection-background-color: #E8F4F8;
                selection-color: #0078D4;
                border: 1px solid #D2D0CE;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.directx_combo)
        
        # Backup option
        self.backup_checkbox = QCheckBox("Create backup of existing DLLs (recommended)")
        self.backup_checkbox.setChecked(True)
        self.backup_checkbox.setToolTip("Backs up original DirectX DLLs before installing DXVK")
        self.backup_checkbox.setStyleSheet("""
            QCheckBox {
                color: #323130;
                spacing: 8px;
                font-size: 9pt;
                margin-top: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #8A8886;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #0078D4;
                border: 2px solid #0078D4;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNEw2IDEyTDIuNjY2NjcgOC42NjY2NyIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            QCheckBox::indicator:hover {
                border-color: #0078D4;
            }
        """)
        layout.addWidget(self.backup_checkbox)
        
        # Action buttons - Windows 11 primary/secondary button style
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 16, 0, 0)
        
        self.install_btn = QPushButton("Install DXVK")
        self.install_btn.setToolTip("Install DXVK DLLs to the selected game folder")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10pt;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #E1E1E1;
                color: #8A8886;
            }
        """)
        self.install_btn.clicked.connect(self.install_dxvk)
        button_layout.addWidget(self.install_btn)
        
        self.uninstall_btn = QPushButton("Uninstall DXVK")
        self.uninstall_btn.setToolTip("Restore original DLLs from backup")
        self.uninstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #323130;
                border: 1px solid #D2D0CE;
                padding: 12px 24px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10pt;
                min-height: 36px;
            }
            QPushButton:hover {
                background-color: #F3F2F1;
                border-color: #8A8886;
            }
            QPushButton:pressed {
                background-color: #EDEBE9;
            }
            QPushButton:disabled {
                background-color: #F3F2F1;
                color: #8A8886;
                border-color: #E1E1E1;
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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        log_title = QLabel("Activity Log")
        log_title_font = QFont("Segoe UI", 11, QFont.Weight.SemiBold)
        log_title.setFont(log_title_font)
        log_title.setStyleSheet("color: #323130; margin-bottom: 4px;")
        layout.addWidget(log_title)
        
        # Log text area - Windows 11 text box style
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Activity log will appear here...")
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                color: #323130;
                border: 1px solid #D2D0CE;
                border-radius: 4px;
                padding: 12px;
                font-family: 'Consolas', 'Cascadia Code', 'Courier New', monospace;
                font-size: 9pt;
                selection-background-color: #E8F4F8;
                selection-color: #0078D4;
            }
            QTextEdit:focus {
                border: 2px solid #0078D4;
                padding: 11px;
            }
            QScrollBar:vertical {
                background-color: #F3F2F1;
                width: 12px;
                border: none;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #C1BEB9;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8A8886;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Show welcome message
        self.log_message("Welcome to DXVK Manager!")
        self.log_message("")
        self.log_message("To get started:")
        self.log_message("1. Click 'Browse...' to select your game folder")
        self.log_message("2. Wait for automatic detection of architecture and DirectX version")
        self.log_message("3. Click 'Install DXVK' to install")
        self.log_message("")
        self.log_message("Ready to begin...")
        
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
        """Start DXVK installation with user-friendly confirmation."""
        folder = self.folder_input.text()
        if not folder:
            QMessageBox.warning(
                self.window, 
                "No Folder Selected",
                "Please select a game folder first.\n\n"
                "Click 'Browse...' to choose the folder containing your game's .exe file."
            )
            return
        
        architecture = self.architecture_label.text()
        if architecture in ["Not detected", "Unknown", "Error", "Analyzing..."]:
            reply = QMessageBox.warning(
                self.window, 
                "Architecture Not Detected", 
                "Could not detect the game's architecture (32-bit or 64-bit).\n\n"
                "Installation may fail or install the wrong DLLs.\n\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Show confirmation dialog before installing
        directx_text = self.directx_label.text()
        backup_text = "Yes (recommended)" if self.backup_checkbox.isChecked() else "No"
        
        reply = QMessageBox.question(
            self.window,
            "Confirm Installation",
            f"Install DXVK to:\n{folder}\n\n"
            f"Architecture: {architecture}\n"
            f"DirectX Version: {directx_text}\n"
            f"Create Backup: {backup_text}\n\n"
            "This will replace DirectX DLL files in the game folder.\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
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
        """Handle installation completion with user-friendly messages."""
        self.install_btn.setEnabled(True)
        self.uninstall_btn.setEnabled(True)
            
            if success:
            QMessageBox.information(
                self.window, 
                "Installation Complete", 
                f"{message}\n\n"
                "You can now launch your game. DXVK will automatically handle DirectX calls."
            )
            else:
            # Show detailed error dialog
            QMessageBox.critical(
                self.window, 
                "Installation Failed", 
                f"{message}\n\n"
                "Please check:\n"
                "- Internet connection\n"
                "- Game folder permissions\n"
                "- Antivirus settings\n"
                "- Activity log for details"
            )

    def uninstall_dxvk(self):
        """Uninstall DXVK with user-friendly confirmation."""
        folder = self.folder_input.text()
        if not folder:
            QMessageBox.warning(
                self.window, 
                "No Folder Selected",
                "Please select a game folder first.\n\n"
                "Click 'Browse...' to choose the folder where DXVK was installed."
            )
            return
        
        reply = QMessageBox.question(
            self.window,
            "Confirm Uninstall",
            f"Uninstall DXVK from:\n{folder}\n\n"
            "This will restore the original DirectX DLL files from backup.\n"
            "If no backup exists, the DXVK DLLs will remain.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
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
                        "Uninstall Complete", 
                        "DXVK has been uninstalled successfully!\n\n"
                        "Original DirectX DLL files have been restored from backup."
                    )
                else:
                    self.log_message("")
                    self.log_message("✗ DXVK uninstallation failed or no backup found.")
                    QMessageBox.warning(
                        self.window,
                        "Uninstall Failed",
                        "Could not uninstall DXVK.\n\n"
                        "Possible reasons:\n"
                        "- No backup folder found (DXVK may not have been installed)\n"
                        "- Backup folder was deleted\n"
                        "- Insufficient permissions\n"
                        "- Files are locked by another program\n\n"
                        "Check the activity log for details."
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
