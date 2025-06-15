class KnowledgeAcquisitionWorker(QObject):
    """Worker for knowledge acquisition in a background thread"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    result = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, deepsoul, source_path):
        super().__init__()
        self.deepsoul = deepsoul
        self.source_path = source_path
    
    def run(self):
        """Run knowledge acquisition"""
        try:
            self.progress.emit(f"Acquiring knowledge from {self.source_path}...")
            
            # Determine source type
            if os.path.isfile(self.source_path):
                source_type = "file"
                self.progress.emit(f"Processing file: {os.path.basename(self.source_path)}")
            elif os.path.isdir(self.source_path):
                source_type = "repo"
                self.progress.emit(f"Processing repository: {os.path.basename(self.source_path)}")
            elif self.source_path.startswith(("http://", "https://")):
                source_type = "doc"
                self.progress.emit(f"Processing URL: {self.source_path}")
            else:
                source_type = "auto"
            
            # Use DeepSoul to acquire knowledge
            result = self.deepsoul.acquire_knowledge(self.source_path, source_type)
            
            self.progress.emit(f"Knowledge acquisition complete. Acquired {len(result)} items.")
            self.result.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))
        
        self.finished.emit()

class SettingsDialog(QDialog):
    """Settings dialog for DeepSeek-Coder"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DeepSeek-Coder Settings")
        self.setMinimumWidth(500)
        
        # Store config
        self.config = config.copy()
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create general settings tab
        self.create_general_tab()
        
        # Create watched directories tab
        self.create_watched_dirs_tab()
        
        # Create memory tab
        self.create_memory_tab()
        
        # Create Windows integration tab (if on Windows)
        if sys.platform.startswith('win'):
            self.create_windows_tab()
        
        # Create button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    
    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Model selection
        group_box = QGroupBox("Model")
        group_layout = QVBoxLayout(group_box)
        
        model_combo = QComboBox()
        model_combo.addItems([
            "deepseek-ai/deepseek-coder-1.3b-instruct",
            "deepseek-ai/deepseek-coder-6.7b-instruct",
            "deepseek-ai/deepseek-coder-33b-instruct"
        ])
        model_combo.setEditable(True)
        model_combo.setCurrentText(self.config.get("model_name", "deepseek-ai/deepseek-coder-1.3b-instruct"))
        group_layout.addWidget(model_combo)
        
        # Connect model combo
        model_combo.currentTextChanged.connect(lambda text: self.config.update({"model_name": text}))
        
        layout.addWidget(group_box)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        light_radio = QRadioButton("Light Theme")
        dark_radio = QRadioButton("Dark Theme")
        system_radio = QRadioButton("System Theme")
        
        # Set current theme
        current_theme = self.config.get("theme", "dark")
        if current_theme == "light":
            light_radio.setChecked(True)
        elif current_theme == "dark":
            dark_radio.setChecked(True)
        else:
            system_radio.setChecked(True)
        
        # Connect theme radios
        light_radio.toggled.connect(lambda checked: checked and self.config.update({"theme": "light"}))
        dark_radio.toggled.connect(lambda checked: checked and self.config.update({"theme": "dark"}))
        system_radio.toggled.connect(lambda checked: checked and self.config.update({"theme": "system"}))
        
        theme_layout.addWidget(light_radio)
        theme_layout.addWidget(dark_radio)
        theme_layout.addWidget(system_radio)
        
        layout.addWidget(theme_group)
        
        # Auto features
        auto_group = QGroupBox("Automation")
        auto_layout = QVBoxLayout(auto_group)
        
        auto_analyze_check = QCheckBox("Automatically analyze modified code files")
        auto_analyze_check.setChecked(self.config.get("auto_analyze", False))
        auto_analyze_check.toggled.connect(lambda checked: self.config.update({"auto_analyze": checked}))
        
        auto_enhance_check = QCheckBox("Automatically enhance code on demand")
        auto_enhance_check.setChecked(self.config.get("auto_enhance", False))
        auto_enhance_check.toggled.connect(lambda checked: self.config.update({"auto_enhance": checked}))
        
        auto_layout.addWidget(auto_analyze_check)
        auto_layout.addWidget(auto_enhance_check)
        
        layout.addWidget(auto_group)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(tab, "General")
    
    def create_watched_dirs_tab(self):
        """Create the watched directories tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Description label
        desc_label = QLabel("Configure directories to monitor for file changes:")
        layout.addWidget(desc_label)
        
        # Directory list
        self.dir_list = QListWidget()
        for directory in self.config.get("watched_directories", []):
            self.dir_list.addItem(directory)
        layout.addWidget(self.dir_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Directory")
        add_button.clicked.connect(self.add_watched_directory)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_watched_directory)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(button_layout)
        
        # Add tab
        self.tab_widget.addTab(tab, "Watched Directories")
    
    def create_memory_tab(self):
        """Create the memory settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Memory protection settings
        protection_group = QGroupBox("Memory Protection")
        protection_layout = QVBoxLayout(protection_group)
        
        low_memory_check = QCheckBox("Enable low memory mode")
        low_memory_check.setChecked(self.config.get("low_memory", False))
        low_memory_check.toggled.connect(lambda checked: self.config.update({"low_memory": checked}))
        
        auto_offload_check = QCheckBox("Automatically offload tensors to CPU when memory is low")
        auto_offload_check.setChecked(self.config.get("auto_offload_to_cpu", True))
        auto_offload_check.toggled.connect(lambda checked: self.config.update({"auto_offload_to_cpu": checked}))
        
        memory_dump_check = QCheckBox("Create memory dumps on OOM errors")
        memory_dump_check.setChecked(self.config.get("memory_dump_enabled", True))
        memory_dump_check.toggled.connect(lambda checked: self.config.update({"memory_dump_enabled": checked}))
        
        protection_layout.addWidget(low_memory_check)
        protection_layout.addWidget(auto_offload_check)
        protection_layout.addWidget(memory_dump_check)
        
        layout.addWidget(protection_group)
        
        # Memory thresholds
        thresholds_group = QGroupBox("Memory Thresholds")
        thresholds_layout = QVBoxLayout(thresholds_group)
        
        ram_warning_label = QLabel("RAM warning threshold (%)")
        ram_warning_slider = QSlider(Qt.Orientation.Horizontal)
        ram_warning_slider.setRange(50, 95)
        ram_warning_slider.setValue(int(self.config.get("ram_warning_threshold", 85)))
        ram_warning_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        ram_warning_slider.setTickInterval(5)
        ram_warning_slider.valueChanged.connect(lambda value: self.config.update({"ram_warning_threshold": value}))
        
        gpu_warning_label = QLabel("GPU warning threshold (%)")
        gpu_warning_slider = QSlider(Qt.Orientation.Horizontal)
        gpu_warning_slider.setRange(50, 95)
        gpu_warning_slider.setValue(int(self.config.get("gpu_warning_threshold", 85)))
        gpu_warning_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        gpu_warning_slider.setTickInterval(5)
        gpu_warning_slider.valueChanged.connect(lambda value: self.config.update({"gpu_warning_threshold": value}))
        
        thresholds_layout.addWidget(ram_warning_label)
        thresholds_layout.addWidget(ram_warning_slider)
        thresholds_layout.addWidget(gpu_warning_label)
        thresholds_layout.addWidget(gpu_warning_slider)
        
        layout.addWidget(thresholds_group)
        
        # System information
        system_group = QGroupBox("System Information")
        system_layout = QVBoxLayout(system_group)
        
        # Get system information
        total_ram = psutil.virtual_memory().total / (1024**3)  # GB
        available_ram = psutil.virtual_memory().available / (1024**3)  # GB
        
        system_layout.addWidget(QLabel(f"Total RAM: {total_ram:.2f} GB"))
        system_layout.addWidget(QLabel(f"Available RAM: {available_ram:.2f} GB"))
        
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                total_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # GB
                system_layout.addWidget(QLabel(f"GPU {i}: {device_name} ({total_memory:.2f} GB)"))
        else:
            system_layout.addWidget(QLabel("No CUDA-compatible GPU detected"))
        
        layout.addWidget(system_group)
        
        # Add stretch
        layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(tab, "Memory")
    
    def create_windows_tab(self):
        """Create the Windows integration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Context menu integration
        context_group = QGroupBox("File Explorer Integration")
        context_layout = QVBoxLayout(context_group)
        
        context_check = QCheckBox("Add to file context menu")
        context_check.setChecked(self.config.get("context_menu_enabled", False))
        context_check.toggled.connect(lambda checked: self.config.update({"context_menu_enabled": checked}))
        
        dir_context_check = QCheckBox("Add to directory context menu")
        dir_context_check.setChecked(self.config.get("dir_context_menu_enabled", False))
        dir_context_check.toggled.connect(lambda checked: self.config.update({"dir_context_menu_enabled": checked}))
        
        context_layout.addWidget(context_check)
        context_layout.addWidget(dir_context_check)
        
        layout.addWidget(context_group)
        
        # File associations
        assoc_group = QGroupBox("File Associations")
        assoc_layout = QVBoxLayout(assoc_group)
        
        # File type checkboxes
        py_check = QCheckBox("Python Files (.py)")
        py_check.setChecked(self.config.get("file_associations", {}).get("py", False))
        py_check.toggled.connect(lambda checked: self._update_file_assoc("py", checked))
        
        js_check = QCheckBox("JavaScript Files (.js, .ts)")
        js_check.setChecked(self.config.get("file_associations", {}).get("js", False))
        js_check.toggled.connect(lambda checked: self._update_file_assoc("js", checked))
        
        cpp_check = QCheckBox("C/C++ Files (.c, .cpp, .h)")
        cpp_check.setChecked(self.config.get("file_associations", {}).get("cpp", False))
        cpp_check.toggled.connect(lambda checked: self._update_file_assoc("cpp", checked))
        
        java_check = QCheckBox("Java Files (.java)")
        java_check.setChecked(self.config.get("file_associations", {}).get("java", False))
        java_check.toggled.connect(lambda checked: self._update_file_assoc("java", checked))
        
        assoc_layout.addWidget(py_check)
        assoc_layout.addWidget(js_check)
        assoc_layout.addWidget(cpp_check)
        assoc_layout.addWidget(java_check)
        
        layout.addWidget(assoc_group)
        
        # Startup options
        startup_group = QGroupBox("Startup Options")
        startup_layout = QVBoxLayout(startup_group)
        
        autostart_check = QCheckBox("Start DeepSeek-Coder with Windows")
        autostart_check.setChecked(self.config.get("auto_start", False))
        autostart_check.toggled.connect(lambda checked: self.config.update({"auto_start": checked}))
        
        startup_layout.addWidget(autostart_check)
        
        layout.addWidget(startup_group)
        
        # Add button to apply Windows integration settings immediately
        apply_button = QPushButton("Apply Windows Integration Settings")
        apply_button.clicked.connect(self.apply_windows_integration)
        layout.addWidget(apply_button)
        
        # Add stretch
        layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(tab, "Windows Integration")
    
    def _update_file_assoc(self, key: str, value: bool):
        """Update file association in config"""
        if "file_associations" not in self.config:
            self.config["file_associations"] = {}
        
        self.config["file_associations"][key] = value
    
    def add_watched_directory(self):
        """Add a directory to watch"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Watch")
        if directory:
            self.dir_list.addItem(directory)
            
            # Update config
            if "watched_directories" not in self.config:
                self.config["watched_directories"] = []
                
            self.config["watched_directories"].append(directory)
    
    def remove_watched_directory(self):
        """Remove selected directory from watch list"""
        selected_items = self.dir_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            # Remove from list widget
            row = self.dir_list.row(item)
            self.dir_list.takeItem(row)
            
            # Remove from config
            if "watched_directories" in self.config:
                if item.text() in self.config["watched_directories"]:
                    self.config["watched_directories"].remove(item.text())
    
    def apply_windows_integration(self):
        """Apply Windows integration settings immediately"""
        if not sys.platform.startswith('win'):
            return
            
        try:
            from utils.windows_integration import get_windows_integration
            
            # Get Windows integration
            integration = get_windows_integration()
            if not integration:
                QMessageBox.warning(self, "Windows Integration", "Could not initialize Windows integration")
                return
                
            # Apply context menu settings
            if self.config.get("context_menu_enabled"):
                integration.add_context_menu_for_all_files()
                integration.add_submenu_actions()
            else:
                integration.remove_context_menu_items()
                
            # Apply directory context menu settings
            if self.config.get("dir_context_menu_enabled"):
                integration.add_context_menu_for_directory()
                
            # Apply file associations
            if "file_associations" in self.config:
                file_associations = []
                
                assoc_map = {
                    "py": [".py"],
                    "js": [".js", ".ts", ".jsx", ".tsx"],
                    "cpp": [".c", ".cpp", ".h", ".hpp"],
                    "java": [".java"]
                }
                
                for key, enabled in self.config["file_associations"].items():
                    if enabled and key in assoc_map:
                        file_associations.extend(assoc_map[key])
                        
                if file_associations:
                    integration.register_file_associations(file_associations)
                    
            # Apply auto-start setting
            if self.config.get("auto_start"):
                integration.setup_auto_start()
            else:
                integration.remove_auto_start()
                
            QMessageBox.information(self, "Windows Integration", "Windows integration settings applied successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Windows Integration Error", f"Error applying Windows integration settings: {str(e)}")
    
    def get_settings(self) -> dict:
        """Get the current settings"""
        # Update watched directories
        watched_dirs = []
        for i in range(self.dir_list.count()):
            watched_dirs.append(self.dir_list.item(i).text())
        
        self.config["watched_directories"] = watched_dirs
        
        return self.config

def main():
    """Main function"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setApplicationVersion(APP_VERSION)
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    # Run application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
