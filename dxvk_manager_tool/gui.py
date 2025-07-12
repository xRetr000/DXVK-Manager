import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os

class DXVKManagerGUI:
    def __init__(self, manager):
        self.manager = manager
        self.root = tk.Tk()
        self.root.title("DXVK Manager Tool")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.game_folder_var = tk.StringVar()
        self.architecture_var = tk.StringVar(value="Not detected")
        self.directx_var = tk.StringVar(value="Not detected")
        self.backup_var = tk.BooleanVar(value=True)
        self.directx_override_var = tk.StringVar(value="Auto-detect")
        
        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Game folder selection
        ttk.Label(main_frame, text="Game Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.game_folder_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_game_folder).grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Detection results
        ttk.Label(main_frame, text="Architecture:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, textvariable=self.architecture_var).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        ttk.Label(main_frame, text="DirectX Version:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, textvariable=self.directx_var).grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        # DirectX override
        ttk.Label(main_frame, text="Override DirectX:").grid(row=3, column=0, sticky=tk.W, pady=5)
        directx_combo = ttk.Combobox(main_frame, textvariable=self.directx_override_var, 
                                   values=["Auto-detect", "Direct3D 9", "Direct3D 10", "Direct3D 11"], 
                                   state="readonly")
        directx_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        # Backup option
        ttk.Checkbutton(main_frame, text="Backup existing DLLs", variable=self.backup_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Install DXVK", command=self.install_dxvk).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Uninstall DXVK", command=self.uninstall_dxvk).pack(side=tk.LEFT, padx=5)
        
        # Status/Log area
        ttk.Label(main_frame, text="Status:").grid(row=6, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        
        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.status_text = tk.Text(text_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def browse_game_folder(self):
        folder = filedialog.askdirectory(title="Select Game Folder")
        if folder:
            self.game_folder_var.set(folder)
            self.analyze_game_folder(folder)

    def analyze_game_folder(self, folder):
        """Analyzes the selected game folder for architecture and DirectX version."""
        self.log_message(f"Analyzing folder: {folder}")
        
        # Find .exe files
        exe_files = [f for f in os.listdir(folder) if f.endswith('.exe')]
        
        if not exe_files:
            self.log_message("No .exe files found in the selected folder.")
            return
        
        # If multiple .exe files, let user choose or pick the first one
        if len(exe_files) > 1:
            self.log_message(f"Multiple .exe files found: {', '.join(exe_files)}")
            self.log_message(f"Using {exe_files[0]} for analysis.")
        
        exe_path = os.path.join(folder, exe_files[0])
        
        # Analyze architecture
        try:
            from exe_analyzer import get_exe_architecture, detect_directx_version
            arch = get_exe_architecture(exe_path)
            self.architecture_var.set(arch)
            self.log_message(f"Architecture detected: {arch}")
            
            # Detect DirectX version
            dx_versions = detect_directx_version(folder)
            dx_text = ", ".join(dx_versions)
            self.directx_var.set(dx_text)
            self.log_message(f"DirectX versions detected: {dx_text}")
            
        except Exception as e:
            self.log_message(f"Error during analysis: {str(e)}")

    def install_dxvk(self):
        """Installs DXVK in a separate thread to avoid blocking the UI."""
        if not self.game_folder_var.get():
            messagebox.showerror("Error", "Please select a game folder first.")
            return
        
        # Disable the install button during installation
        self.disable_buttons()
        
        # Run installation in a separate thread
        thread = threading.Thread(target=self._install_dxvk_thread)
        thread.daemon = True
        thread.start()

    def _install_dxvk_thread(self):
        """The actual installation logic running in a separate thread."""
        try:
            game_folder = self.game_folder_var.get()
            architecture = self.architecture_var.get()
            
            # Determine DirectX version
            if self.directx_override_var.get() != "Auto-detect":
                directx_version = self.directx_override_var.get()
            else:
                directx_version = self.directx_var.get().split(", ")[0] if self.directx_var.get() != "Not detected" else "Unknown"
            
            backup_enabled = self.backup_var.get()
            
            self.log_message("Starting DXVK installation...")
            self.log_message(f"Game folder: {game_folder}")
            self.log_message(f"Architecture: {architecture}")
            self.log_message(f"DirectX version: {directx_version}")
            self.log_message(f"Backup enabled: {backup_enabled}")
            
            # Call the manager to perform the installation
            success = self.manager.install_dxvk(game_folder, architecture, directx_version, backup_enabled)
            
            if success:
                self.log_message("DXVK installation completed successfully!")
                messagebox.showinfo("Success", "DXVK installation completed successfully!")
            else:
                self.log_message("DXVK installation failed.")
                messagebox.showerror("Error", "DXVK installation failed. Check the log for details.")
                
        except Exception as e:
            self.log_message(f"Error during installation: {str(e)}")
            messagebox.showerror("Error", f"Installation error: {str(e)}")
        finally:
            # Re-enable buttons
            self.root.after(0, self.enable_buttons)

    def uninstall_dxvk(self):
        """Uninstalls DXVK by restoring backups."""
        if not self.game_folder_var.get():
            messagebox.showerror("Error", "Please select a game folder first.")
            return
        
        game_folder = self.game_folder_var.get()
        
        # Confirm uninstallation
        if messagebox.askyesno("Confirm", "Are you sure you want to uninstall DXVK and restore backups?"):
            success = self.manager.uninstall_dxvk(game_folder)
            if success:
                self.log_message("DXVK uninstalled successfully!")
                messagebox.showinfo("Success", "DXVK uninstalled successfully!")
            else:
                self.log_message("DXVK uninstallation failed or no backup found.")
                messagebox.showwarning("Warning", "Uninstallation failed or no backup found.")

    def disable_buttons(self):
        """Disables action buttons during operations."""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(state="disabled")

    def enable_buttons(self):
        """Re-enables action buttons after operations."""
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(state="normal")

    def log_message(self, message):
        """Adds a message to the status text area."""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def run(self):
        """Starts the GUI main loop."""
        self.root.mainloop()

