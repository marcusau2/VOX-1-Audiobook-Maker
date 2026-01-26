import customtkinter as ctk
import tkinter as tk
import threading
import os
import sys
import json
import traceback
from tkinter import filedialog, messagebox

# ========================================================
# EMBEDDED PYTHON SETUP (Fix for Tcl/Tk)
# ========================================================
# When running in embeddable Python, Tcl/Tk libs are often not found automatically.
# We need to manually point to them.

def setup_embedded_tkinter():
    try:
        # Find site-packages where tkinter-embed installed the libs
        # usually .../Lib/site-packages
        site_packages = next((p for p in sys.path if 'site-packages' in p), None)
        
        if not site_packages:
            return

        # Path to the tcl folder installed by tkinter-embed
        tcl_root = os.path.join(site_packages, 'tcl')
        
        if os.path.exists(tcl_root):
            # Set environment variables for Tcl/Tk
            tcl_lib = os.path.join(tcl_root, 'tcl8.6')
            tk_lib = os.path.join(tcl_root, 'tk8.6')
            
            if os.path.exists(tcl_lib) and os.path.exists(tk_lib):
                os.environ['TCL_LIBRARY'] = tcl_lib
                os.environ['TK_LIBRARY'] = tk_lib
                # print(f"Set TCL_LIBRARY={tcl_lib}")
                # print(f"Set TK_LIBRARY={tk_lib}")
            
            # Add site-packages to PATH so DLLs (tcl86t.dll, tk86t.dll) can be found
            os.environ['PATH'] = site_packages + os.pathsep + os.environ['PATH']
            
    except Exception as e:
        print(f"Warning: Failed to setup embedded Tkinter: {e}")

setup_embedded_tkinter()
# ========================================================

# Ensure current directory is in path for embedded python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend import AudioEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Vox1App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vox-1 Audiobook Generator")
        self.geometry("1000x800")
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        
        # State
        self.engine = None
        self.master_voice_path = None
        self.preview_path = None
        self.book_path = None
        self.book_is_json = False  # Track if loaded book is JSON manifest
        self.book_metadata = None  # Store JSON metadata (title, author, chapter count)
        self.stop_event = threading.Event()
        self.is_rendering = False

        # BookSmith state
        self.booksmith_data = None  # Stores BookData object from BookSmith
        self.chapter_checkboxes = []  # List of chapter checkbox widgets
        self.chapter_var_list = []  # List of BooleanVars for checkboxes
        self.current_preview_chapter_idx = None  # Track which chapter is being previewed
        
        self.settings_file = "user_settings.json"
        self.settings = self._load_settings()
        
        self._setup_ui()
        # Don't auto-start engine, let user pick size first
        self.after(500, self._init_from_settings)

    def _load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f: return json.load(f)
        except: pass
        return {
            "model_size": "0.6B",
            "last_voice": None,
            "batch_size": 5,
            "chunk_size": 500,
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 20,
            "repetition_penalty": 1.05,
            "show_vram": True,
            "show_timing": True,
            "debug_mode": False,
            "smart_import": True
        }

    def _save_settings(self):
        try:
            self.settings["model_size"] = self.model_size_var.get()
            self.settings["last_voice"] = self.master_voice_path
            # Save advanced settings if they exist
            if hasattr(self, 'batch_size_var'):
                self.settings["batch_size"] = int(self.batch_size_var.get())
            if hasattr(self, 'chunk_size_var'):
                self.settings["chunk_size"] = int(self.chunk_size_var.get())
            if hasattr(self, 'temperature_var'):
                self.settings["temperature"] = float(self.temperature_var.get())
            if hasattr(self, 'repetition_penalty_var'):
                self.settings["repetition_penalty"] = float(self.repetition_penalty_var.get())
            if hasattr(self, 'show_vram_var'):
                self.settings["show_vram"] = self.show_vram_var.get()
            if hasattr(self, 'show_timing_var'):
                self.settings["show_timing"] = self.show_timing_var.get()
            if hasattr(self, 'debug_mode_var'):
                self.settings["debug_mode"] = self.debug_mode_var.get()
            # Save Smart Import setting
            if hasattr(self, 'smart_import_var'):
                self.settings["smart_import"] = self.smart_import_var.get()
            with open(self.settings_file, 'w') as f: json.dump(self.settings, f, indent=2)
        except: pass

    def _init_from_settings(self):
        # Restore model selection
        saved_size = self.settings.get("model_size", "0.6B")
        if saved_size == "1.7B":
            self.model_size_var.set("1.7B (High Quality)")
            self._start_engine_thread("1.7B")
        else:
            self.model_size_var.set("0.6B (Fastest)")
            self._start_engine_thread("0.6B")

        # Restore last voice
        last_voice = self.settings.get("last_voice")
        if last_voice and os.path.exists(last_voice):
            self.master_voice_path = last_voice
            self.studio_status.configure(text="Master Voice: LOADED", text_color="green")
            self.log(f"Restored previous voice: {os.path.basename(last_voice)}")

        # Restore Smart Import setting
        smart_import_enabled = self.settings.get("smart_import", True)
        self.smart_import_var.set(smart_import_enabled)
        self.studio_smart_import_var.set(smart_import_enabled)

    def _setup_ui(self):
        # Header Frame
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="Vox-1 // AI Audio Engine", font=("Roboto", 20, "bold"))
        self.header_label.pack(side="left", padx=20, pady=10)
        
        # Model Selector
        self.model_size_var = ctk.StringVar(value="0.6B (Fastest)")
        self.model_selector = ctk.CTkOptionMenu(self.header_frame, values=["0.6B (Fastest)", "1.7B (High Quality)"],
                                                command=self._on_model_change, width=180)
        self.model_selector.pack(side="right", padx=20, pady=10)
        self.model_label = ctk.CTkLabel(self.header_frame, text="Model Size:", font=("Roboto", 12))
        self.model_label.pack(side="right", padx=5)
        
        # Tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        self.tab_lab = self.tab_view.add("The Lab (Voice Creation)")
        self.tab_booksmith = self.tab_view.add("BookSmith (EPUB/PDF)")
        self.tab_studio = self.tab_view.add("The Studio (Rendering)")
        self.tab_advanced = self.tab_view.add("Advanced Settings")

        self._setup_lab_tab()
        self._setup_booksmith_tab()
        self._setup_studio_tab()
        self._setup_advanced_tab()
        
        # Log
        self.log_frame = ctk.CTkFrame(self, height=150)
        self.log_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_propagate(False)
        
        self.log_label = ctk.CTkLabel(self.log_frame, text="Activity Log (Check here for VRAM/Speed)", font=("Roboto", 12, "bold"))
        self.log_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 11))
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_box.configure(state="disabled")
        
        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Waiting for model selection...", anchor="w")
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=5)

    def log(self, message):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", str(message) + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _write)

    def _setup_lab_tab(self):
        self.tab_lab.grid_columnconfigure(0, weight=1)
        self.tab_lab.grid_rowconfigure(1, weight=1)
        
        self.mode_frame = ctk.CTkFrame(self.tab_lab)
        self.mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.mode_var = ctk.StringVar(value="design")
        self.radio_design = ctk.CTkRadioButton(self.mode_frame, text="Design Voice", variable=self.mode_var, value="design", command=self._update_lab_mode)
        self.radio_design.pack(side="left", padx=20, pady=10)
        self.radio_clone = ctk.CTkRadioButton(self.mode_frame, text="Clone Voice", variable=self.mode_var, value="clone", command=self._update_lab_mode)
        self.radio_clone.pack(side="left", padx=20, pady=10)
        
        self.input_frame = ctk.CTkFrame(self.tab_lab)
        self.input_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.desc_label = ctk.CTkLabel(self.input_frame, text="Description:", anchor="w")
        self.desc_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        self.desc_entry = ctk.CTkTextbox(self.input_frame, height=80)
        self.desc_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.desc_entry.insert("0.0", "A deep, soothing male voice.")
        
        self.file_label = ctk.CTkLabel(self.input_frame, text="Reference Audio:", anchor="w")
        self.file_btn = ctk.CTkButton(self.input_frame, text="Choose File...", command=self._choose_ref_file)
        self.ref_file_path_label = ctk.CTkLabel(self.input_frame, text="No file selected", text_color="gray")

        # Smart Import checkbox for Lab tab
        self.smart_import_var = ctk.BooleanVar(value=True)  # Default ON
        self.smart_import_checkbox = ctk.CTkCheckBox(
            self.input_frame,
            text="Smart Import (auto-optimize audio)",
            variable=self.smart_import_var,
            font=("Arial", 12)
        )

        self.preview_text_label = ctk.CTkLabel(self.input_frame, text="Preview Text:", anchor="w")
        self.preview_text_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10,0))
        self.preview_entry = ctk.CTkEntry(self.input_frame)
        self.preview_entry.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.preview_entry.insert(0, "This is a test of the voice generation system.")
        
        self.action_frame = ctk.CTkFrame(self.tab_lab, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.gen_btn = ctk.CTkButton(self.action_frame, text="Generate Preview", command=self._generate_preview, state="disabled")
        self.gen_btn.pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(self.action_frame, text="Play Preview", command=self._play_preview, state="disabled", fg_color="green")
        self.play_btn.pack(side="left", padx=5)
        self.save_master_btn = ctk.CTkButton(self.action_frame, text="Save as Master Voice", command=self._save_master, state="disabled", fg_color="orange")
        self.save_master_btn.pack(side="right", padx=5)

    def _setup_booksmith_tab(self):
        """Setup BookSmith tab for EPUB/PDF processing."""
        # Use same pattern as Studio tab - scrollable frame at top level
        self.tab_booksmith.grid_columnconfigure(0, weight=1)
        self.tab_booksmith.grid_rowconfigure(0, weight=1)

        # Main scrollable container (like Studio tab)
        booksmith_scroll = ctk.CTkScrollableFrame(self.tab_booksmith)
        booksmith_scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        booksmith_scroll.grid_columnconfigure(0, weight=1)

        # Header
        header_label = ctk.CTkLabel(
            booksmith_scroll,
            text="📚 BookSmith - EPUB & PDF Processor",
            font=("Roboto", 18, "bold")
        )
        header_label.pack(pady=10)

        info_label = ctk.CTkLabel(
            booksmith_scroll,
            text="Load EPUB/PDF files, configure chapters, and create audiobook manifests",
            font=("Roboto", 11),
            text_color="gray"
        )
        info_label.pack(pady=(0, 20))

        # File selection
        self.load_epub_btn = ctk.CTkButton(
            booksmith_scroll,
            text="Load EPUB/PDF File",
            command=self._load_epub_pdf,
            width=200,
            height=40
        )
        self.load_epub_btn.pack(pady=10)

        self.booksmith_file_label = ctk.CTkLabel(
            booksmith_scroll,
            text="No file loaded",
            font=("Roboto", 12)
        )
        self.booksmith_file_label.pack(pady=5)

        self.booksmith_info_label = ctk.CTkLabel(
            booksmith_scroll,
            text="",
            font=("Roboto", 11),
            text_color="gray"
        )
        self.booksmith_info_label.pack(pady=5)

        # Chapter controls
        controls_frame = ctk.CTkFrame(booksmith_scroll, fg_color="transparent")
        controls_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(
            controls_frame,
            text="Chapters:",
            font=("Roboto", 14, "bold")
        ).pack(side="left", padx=10)

        self.select_all_btn = ctk.CTkButton(
            controls_frame,
            text="Select All",
            command=self._select_all_chapters,
            width=100,
            state="disabled"
        )
        self.select_all_btn.pack(side="left", padx=5)

        self.deselect_all_btn = ctk.CTkButton(
            controls_frame,
            text="Deselect All",
            command=self._deselect_all_chapters,
            width=100,
            state="disabled"
        )
        self.deselect_all_btn.pack(side="left", padx=5)

        # Two-column layout: chapters list + text preview
        chapters_container = ctk.CTkFrame(booksmith_scroll, fg_color="transparent")
        chapters_container.pack(fill="both", expand=True, pady=10)

        # Left: Chapter list with checkboxes
        left_frame = ctk.CTkFrame(chapters_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            left_frame,
            text="Select Chapters to Include:",
            font=("Roboto", 12, "bold")
        ).pack(pady=5, padx=10, anchor="w")

        self.chapter_scroll = ctk.CTkFrame(left_frame)
        self.chapter_scroll.pack(fill="both", expand=True, pady=5, padx=5)

        # Placeholder
        self.chapter_placeholder = ctk.CTkLabel(
            self.chapter_scroll,
            text="📂 Chapters will appear here after loading a file",
            font=("Roboto", 12),
            text_color="gray"
        )
        self.chapter_placeholder.pack(pady=50)

        # Right: Text preview pane
        right_frame = ctk.CTkFrame(chapters_container)
        right_frame.pack(side="right", fill="both", expand=True)

        preview_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        preview_header.pack(fill="x", pady=5, padx=10)

        ctk.CTkLabel(
            preview_header,
            text="Chapter Preview & Edit:",
            font=("Roboto", 12, "bold")
        ).pack(side="left")

        # Edit controls
        edit_controls = ctk.CTkFrame(preview_header, fg_color="transparent")
        edit_controls.pack(side="right")

        self.save_chapter_btn = ctk.CTkButton(
            edit_controls,
            text="Save Changes",
            command=self._save_chapter_changes,
            width=120,
            state="disabled",
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_chapter_btn.pack(side="left", padx=5)

        self.discard_chapter_btn = ctk.CTkButton(
            edit_controls,
            text="Discard",
            command=self._discard_chapter_changes,
            width=80,
            state="disabled"
        )
        self.discard_chapter_btn.pack(side="left", padx=5)

        # Chapter title editor
        title_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=5, padx=10)

        ctk.CTkLabel(
            title_frame,
            text="Chapter Title:",
            font=("Roboto", 10)
        ).pack(side="left", padx=(0, 5))

        self.chapter_title_entry = ctk.CTkEntry(
            title_frame,
            font=("Roboto", 11),
            placeholder_text="Chapter title..."
        )
        self.chapter_title_entry.pack(side="left", fill="x", expand=True)

        # Text editor
        self.chapter_preview_box = ctk.CTkTextbox(
            right_frame,
            font=("Roboto", 11),
            wrap="word"
        )
        self.chapter_preview_box.pack(fill="both", expand=True, pady=5, padx=5)
        self.chapter_preview_box.insert("1.0", "Click on a chapter to preview and edit its text here...")
        self.chapter_preview_box.configure(state="disabled")

        # Process button
        self.process_booksmith_btn = ctk.CTkButton(
            booksmith_scroll,
            text="Process & Send to Studio",
            command=self._process_booksmith_to_studio,
            height=50,
            font=("Roboto", 16),
            state="disabled",
            fg_color="green",
            hover_color="darkgreen"
        )
        self.process_booksmith_btn.pack(pady=20)

        ctk.CTkLabel(
            booksmith_scroll,
            text="After processing, go to Studio tab to load voice and render",
            font=("Roboto", 10),
            text_color="gray"
        ).pack()

    def _setup_studio_tab(self):
        self.tab_studio.grid_columnconfigure(0, weight=1)
        self.tab_studio.grid_rowconfigure(0, weight=1)

        # Use scrollable frame to ensure all buttons are visible
        self.studio_scroll = ctk.CTkScrollableFrame(self.tab_studio)
        self.studio_scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.studio_scroll.grid_columnconfigure(0, weight=1)

        self.content_frame = self.studio_scroll
        
        self.studio_status = ctk.CTkLabel(self.content_frame, text="Master Voice: NOT LOADED", text_color="red", font=("Roboto", 16))
        self.studio_status.pack(pady=20)

        # Smart Import checkbox for Studio tab
        self.studio_smart_import_var = ctk.BooleanVar(value=True)  # Default ON
        self.studio_smart_import_checkbox = ctk.CTkCheckBox(
            self.content_frame,
            text="Smart Import (auto-optimize audio)",
            variable=self.studio_smart_import_var,
            font=("Arial", 12)
        )
        self.studio_smart_import_checkbox.pack(pady=(0, 10))

        self.load_voice_btn = ctk.CTkButton(self.content_frame, text="Load Master Voice (.wav/.mp3)", command=self._load_master_voice_direct, fg_color="#555555")
        self.load_voice_btn.pack(pady=5)
        
        self.load_book_btn = ctk.CTkButton(self.content_frame, text="Load Book (.txt/.json)", command=self._load_book)
        self.load_book_btn.pack(pady=10)
        self.book_label = ctk.CTkLabel(self.content_frame, text="No book loaded")
        self.book_label.pack(pady=5)
        self.book_info_label = ctk.CTkLabel(self.content_frame, text="", text_color="gray", font=("Roboto", 11))
        self.book_info_label.pack(pady=2)
        
        self.render_btn = ctk.CTkButton(self.content_frame, text="Render Audiobook", command=self._render_book, state="disabled", height=50, font=("Roboto", 16))
        self.render_btn.pack(pady=30)
        self.open_output_btn = ctk.CTkButton(self.content_frame, text="Open Output Folder", command=self._open_output_folder, fg_color="#444444")
        self.open_output_btn.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.content_frame)
        self.progress_bar.pack(pady=10, padx=50, fill="x")
        self.progress_bar.set(0)

    def _setup_advanced_tab(self):
        """Setup the Advanced Settings tab with performance tuning options."""
        self.tab_advanced.grid_columnconfigure(0, weight=1)

        # Main scrollable frame
        self.advanced_scroll = ctk.CTkScrollableFrame(self.tab_advanced)
        self.advanced_scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.advanced_scroll.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(self.advanced_scroll, text="⚙️ ADVANCED SETTINGS",
                             font=("Roboto", 20, "bold"))
        header.grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Performance Tuning Section
        perf_label = ctk.CTkLabel(self.advanced_scroll, text="🔧 Performance Tuning",
                                 font=("Roboto", 16, "bold"))
        perf_label.grid(row=1, column=0, pady=(10, 10), sticky="w")

        # Batch Size
        batch_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        batch_frame.grid(row=2, column=0, sticky="ew", pady=10)
        batch_frame.grid_columnconfigure(0, weight=1)

        batch_label = ctk.CTkLabel(batch_frame, text="Batch Size (Default: 3)",
                                   font=("Roboto", 14, "bold"))
        batch_label.grid(row=0, column=0, sticky="w", pady=5)

        self.batch_size_var = ctk.IntVar(value=self.settings.get("batch_size", 3))
        self.batch_slider = ctk.CTkSlider(batch_frame, from_=1, to=20, number_of_steps=19,
                                         variable=self.batch_size_var, command=self._update_batch_label)
        self.batch_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.batch_value_label = ctk.CTkLabel(batch_frame, text=f"Current: {self.batch_size_var.get()}",
                                             font=("Roboto", 12))
        self.batch_value_label.grid(row=2, column=0, sticky="w")

        batch_info = ctk.CTkLabel(batch_frame,
            text="ℹ️ Number of text chunks processed simultaneously on your GPU.\n" +
                 "   • Higher values = Faster generation, but uses more VRAM\n" +
                 "   • Lower values = Slower, but safer for GPUs with less VRAM\n" +
                 "   • If you get \"out of memory\" errors, reduce this value",
            font=("Roboto", 11), justify="left", text_color="gray")
        batch_info.grid(row=3, column=0, sticky="w", pady=5)

        self.auto_detect_btn = ctk.CTkButton(batch_frame, text="Auto-Detect Optimal Size",
                                            command=self._auto_detect_batch_size,
                                            fg_color="#555555", width=200)
        self.auto_detect_btn.grid(row=4, column=0, sticky="w", pady=5)

        # Separator
        sep1 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep1.grid(row=3, column=0, sticky="ew", pady=15)

        # Chunk Size
        chunk_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        chunk_frame.grid(row=4, column=0, sticky="ew", pady=10)
        chunk_frame.grid_columnconfigure(0, weight=1)

        chunk_label = ctk.CTkLabel(chunk_frame, text="Chunk Size (Default: 500 chars)",
                                   font=("Roboto", 14, "bold"))
        chunk_label.grid(row=0, column=0, sticky="w", pady=5)

        self.chunk_size_var = ctk.IntVar(value=self.settings.get("chunk_size", 500))
        self.chunk_slider = ctk.CTkSlider(chunk_frame, from_=100, to=1000, number_of_steps=18,
                                         variable=self.chunk_size_var, command=self._update_chunk_label)
        self.chunk_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.chunk_value_label = ctk.CTkLabel(chunk_frame, text=f"Current: {self.chunk_size_var.get()} characters",
                                             font=("Roboto", 12))
        self.chunk_value_label.grid(row=2, column=0, sticky="w")

        chunk_info = ctk.CTkLabel(chunk_frame,
            text="ℹ️ Maximum text length per segment before splitting.\n" +
                 "   • Larger = Fewer total chunks, faster overall processing\n" +
                 "   • Smaller = More chunks, lower VRAM per chunk\n" +
                 "   • Default (500) works well for most books and GPUs\n" +
                 "   • Range: 100-1000 characters",
            font=("Roboto", 11), justify="left", text_color="gray")
        chunk_info.grid(row=3, column=0, sticky="w", pady=5)

        # Separator
        sep2 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep2.grid(row=5, column=0, sticky="ew", pady=15)

        # Quality & Performance Section
        quality_label = ctk.CTkLabel(self.advanced_scroll, text="🎛️ Quality & Performance",
                                     font=("Roboto", 16, "bold"))
        quality_label.grid(row=6, column=0, pady=(10, 10), sticky="w")

        # Temperature
        temp_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        temp_frame.grid(row=7, column=0, sticky="ew", pady=10)
        temp_frame.grid_columnconfigure(0, weight=1)

        temp_label = ctk.CTkLabel(temp_frame, text="Temperature (Default: 0.7)",
                                 font=("Roboto", 14, "bold"))
        temp_label.grid(row=0, column=0, sticky="w", pady=5)

        self.temperature_var = ctk.DoubleVar(value=self.settings.get("temperature", 0.7))
        self.temp_slider = ctk.CTkSlider(temp_frame, from_=0.1, to=2.0, number_of_steps=19,
                                        variable=self.temperature_var, command=self._update_temp_label)
        self.temp_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.temp_value_label = ctk.CTkLabel(temp_frame, text=f"Current: {self.temperature_var.get():.1f}",
                                            font=("Roboto", 12))
        self.temp_value_label.grid(row=2, column=0, sticky="w")

        temp_info = ctk.CTkLabel(temp_frame,
            text="ℹ️ Controls voice creativity and variation:\n" +
                 "   • Lower (0.3-0.5) = More consistent, monotone\n" +
                 "   • Default (0.7) = Balanced naturalness\n" +
                 "   • Higher (1.0-1.5) = More expressive, variable",
            font=("Roboto", 11), justify="left", text_color="gray")
        temp_info.grid(row=3, column=0, sticky="w", pady=5)

        # Repetition Penalty
        rep_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        rep_frame.grid(row=8, column=0, sticky="ew", pady=10)
        rep_frame.grid_columnconfigure(0, weight=1)

        rep_label = ctk.CTkLabel(rep_frame, text="Repetition Penalty (Default: 1.05)",
                                font=("Roboto", 14, "bold"))
        rep_label.grid(row=0, column=0, sticky="w", pady=5)

        self.repetition_penalty_var = ctk.DoubleVar(value=self.settings.get("repetition_penalty", 1.05))
        self.rep_slider = ctk.CTkSlider(rep_frame, from_=1.0, to=2.0, number_of_steps=20,
                                       variable=self.repetition_penalty_var, command=self._update_rep_label)
        self.rep_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.rep_value_label = ctk.CTkLabel(rep_frame, text=f"Current: {self.repetition_penalty_var.get():.2f}",
                                           font=("Roboto", 12))
        self.rep_value_label.grid(row=2, column=0, sticky="w")

        rep_info = ctk.CTkLabel(rep_frame,
            text="ℹ️ Prevents voice from getting stuck in loops:\n" +
                 "   • 1.0 = No penalty (may loop/repeat)\n" +
                 "   • 1.05 = Slight penalty (recommended)\n" +
                 "   • 1.2+ = Strong penalty (prevents repetition)",
            font=("Roboto", 11), justify="left", text_color="gray")
        rep_info.grid(row=3, column=0, sticky="w", pady=5)

        # Separator
        sep3 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep3.grid(row=9, column=0, sticky="ew", pady=15)

        # Monitoring Section
        monitor_label = ctk.CTkLabel(self.advanced_scroll, text="📊 Monitoring & Logging",
                                     font=("Roboto", 16, "bold"))
        monitor_label.grid(row=10, column=0, pady=(10, 10), sticky="w")

        monitor_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        monitor_frame.grid(row=11, column=0, sticky="ew", pady=10)

        self.show_vram_var = ctk.BooleanVar(value=self.settings.get("show_vram", True))
        self.vram_checkbox = ctk.CTkCheckBox(monitor_frame, text="Show VRAM usage in Activity Log",
                                            variable=self.show_vram_var)
        self.vram_checkbox.grid(row=0, column=0, sticky="w", pady=5)

        self.show_timing_var = ctk.BooleanVar(value=self.settings.get("show_timing", True))
        self.timing_checkbox = ctk.CTkCheckBox(monitor_frame, text="Show per-chunk timing information",
                                              variable=self.show_timing_var)
        self.timing_checkbox.grid(row=1, column=0, sticky="w", pady=5)

        self.debug_mode_var = ctk.BooleanVar(value=self.settings.get("debug_mode", False))
        self.debug_checkbox = ctk.CTkCheckBox(monitor_frame, text="Enable verbose debug logging",
                                             variable=self.debug_mode_var)
        self.debug_checkbox.grid(row=2, column=0, sticky="w", pady=5)

        # Separator
        sep4 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep4.grid(row=12, column=0, sticky="ew", pady=15)

        # Quick Tips Section
        tips_label = ctk.CTkLabel(self.advanced_scroll, text="💡 Quick Tips",
                                 font=("Roboto", 16, "bold"))
        tips_label.grid(row=13, column=0, pady=(10, 10), sticky="w")

        tips_text = (
            "• Start with defaults if unsure\n" 
            "• Watch Activity Log during first render to see VRAM usage\n" 
            "• If VRAM usage stays low (under 50%), try increasing batch size\n" 
            "• If you get memory errors, decrease batch size by 2-3\n" 
            "• Temperature 0.7 and Rep Penalty 1.05 work well for most voices"
        )
        tips_display = ctk.CTkLabel(self.advanced_scroll, text=tips_text,
                                    font=("Roboto", 11), justify="left", text_color="lightblue")
        tips_display.grid(row=14, column=0, sticky="w", pady=5)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        button_frame.grid(row=15, column=0, sticky="ew", pady=20)
        button_frame.grid_columnconfigure(1, weight=1)

        reset_btn = ctk.CTkButton(button_frame, text="Reset to Defaults",
                                 command=self._reset_advanced_settings,
                                 fg_color="#cc5555", hover_color="#aa4444", width=150)
        reset_btn.grid(row=0, column=0, padx=5)

        apply_btn = ctk.CTkButton(button_frame, text="Apply Settings",
                                 command=self._apply_advanced_settings,
                                 fg_color="#55cc55", hover_color="#44aa44", width=150)
        apply_btn.grid(row=0, column=2, padx=5)

    def _update_batch_label(self, value):
        """Update the batch size label when slider moves."""
        self.batch_value_label.configure(text=f"Current: {int(float(value))}")

    def _update_chunk_label(self, value):
        """Update the chunk size label when slider moves."""
        self.chunk_value_label.configure(text=f"Current: {int(float(value))} characters")

    def _update_temp_label(self, value):
        """Update the temperature label when slider moves."""
        self.temp_value_label.configure(text=f"Current: {float(value):.1f}")

    def _update_rep_label(self, value):
        """Update the repetition penalty label when slider moves."""
        self.rep_value_label.configure(text=f"Current: {float(value):.2f}")

    def _auto_detect_batch_size(self):
        """Auto-detect optimal batch size based on available VRAM."""
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total_vram_gb = props.total_memory / (1024**3)

                # Conservative formula: suggest batch size based on VRAM
                # 12GB GPU -> 5, 24GB GPU -> 10
                suggested = min(20, max(1, int(total_vram_gb / 2.4)))

                self.batch_size_var.set(suggested)
                self._update_batch_label(suggested)

                messagebox.showinfo("Auto-Detect",
                    f"Detected {total_vram_gb:.1f}GB VRAM\n" +
                    f"Suggested batch size: {suggested}\n\n" +
                    f"You can adjust manually if needed.")
            else:
                messagebox.showwarning("Auto-Detect", "No CUDA GPU detected!")
        except Exception as e:
            messagebox.showerror("Auto-Detect Error", f"Failed to detect GPU: {str(e)}")

    def _reset_advanced_settings(self):
        """Reset all advanced settings to defaults."""
        self.batch_size_var.set(5)
        self.chunk_size_var.set(500)
        self.temperature_var.set(0.7)
        self.repetition_penalty_var.set(1.05)
        self.show_vram_var.set(True)
        self.show_timing_var.set(True)
        self.debug_mode_var.set(False)
        self._update_batch_label(5)
        self._update_chunk_label(500)
        self._update_temp_label(0.7)
        self._update_rep_label(1.05)
        messagebox.showinfo("Reset", "Advanced settings reset to defaults!")

    def _apply_advanced_settings(self):
        """Apply and save advanced settings, then reload engine."""
        self._save_settings()

        # Get current model size
        current_choice = self.model_size_var.get()
        if "0.6B" in current_choice:
            size = "0.6B"
        else:
            size = "1.7B"

        # Show applying message
        self.status_bar.configure(text="Applying new settings...")
        self.gen_btn.configure(state="disabled")
        self.render_btn.configure(state="disabled")

        # Reload engine with new settings in background thread
        def apply_and_reload():
            try:
                # Brief delay to let UI update
                import time
                time.sleep(0.5)

                # Reload engine
                self._start_engine_thread(size)

                # Show success message
                self.after(0, lambda: messagebox.showinfo("Settings Applied",
                    f"Advanced settings applied successfully!\n\n" +
                    f"Batch Size: {self.batch_size_var.get()}\n" +
                    f"Chunk Size: {self.chunk_size_var.get()}\n" +
                    f"Temperature: {self.temperature_var.get():.1f}\n" +
                    f"Repetition Penalty: {self.repetition_penalty_var.get():.2f}\n\n" +
                    f"Engine reloaded with new settings."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to apply settings: {str(e)}"))

        threading.Thread(target=apply_and_reload, daemon=True).start()

    def _init_engine_default(self):
        self._start_engine_thread("1.7B")

    def _on_model_change(self, choice):
        if choice == "0.6B (Fastest)":
            size = "0.6B"
        else:
            size = "1.7B"
        
        self.status_bar.configure(text=f"Switching to {size} model...")
        self.gen_btn.configure(state="disabled")
        self.render_btn.configure(state="disabled")
        self._start_engine_thread(size)

    def _start_engine_thread(self, size):
        def load():
            try:
                # Force engine reload
                self.engine = None
                # Pass advanced settings to engine
                batch_size = self.settings.get("batch_size", 5)
                chunk_size = self.settings.get("chunk_size", 500)
                temperature = self.settings.get("temperature", 0.7)
                top_p = self.settings.get("top_p", 0.8)
                top_k = self.settings.get("top_k", 20)
                repetition_penalty = self.settings.get("repetition_penalty", 1.05)
                self.engine = AudioEngine(
                    log_callback=self.log,
                    model_size=size,
                    batch_size=batch_size,
                    chunk_size=chunk_size,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty
                )
                self.after(0, lambda: self.status_bar.configure(text=f"System Ready ({size})"))
                self.after(0, lambda: self.gen_btn.configure(state="normal"))
                self.after(0, self._check_render_ready)
            except Exception as e:
                err_msg = traceback.format_exc()
                self.log("ENGINE ERROR:\n" + err_msg)
                self.after(0, lambda: self.status_bar.configure(text="Engine Failed"))
        
        threading.Thread(target=load, daemon=True).start()

    # --- Rest of the handlers same as before ---
    def _update_lab_mode(self):
        mode = self.mode_var.get()
        if mode == "design":
            self.file_label.grid_forget(); self.file_btn.grid_forget(); self.ref_file_path_label.grid_forget()
            self.smart_import_checkbox.grid_forget()
            self.desc_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
            self.desc_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        else:
            self.desc_label.grid_forget(); self.desc_entry.grid_forget()
            self.file_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
            self.file_btn.grid(row=1, column=0, sticky="w", padx=10, pady=5)
            self.ref_file_path_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
            self.smart_import_checkbox.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 10))

    def _choose_ref_file(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3")])
        if not path:
            return

        # Smart Import processing
        if self.smart_import_var.get():
            self.log("Smart Import: Processing audio...")
            try:
                from backend import smart_import_audio
                optimized_path, info_msg = smart_import_audio(path, log_callback=self.log)
                self.ref_file_path = optimized_path
                self.log(f"✓ {info_msg}")
            except Exception as e:
                self.log(f"Smart Import failed: {e}, using original file")
                self.ref_file_path = path
        else:
            self.ref_file_path = path

        self.ref_file_path_label.configure(text=os.path.basename(path))

    def _generate_preview(self):
        mode = self.mode_var.get()
        text = self.preview_entry.get()
        self.gen_btn.configure(state="disabled", text="Working...")
        self.status_bar.configure(text="Generating...")
        def run():
            try:
                if mode == "design":
                    desc = self.desc_entry.get("0.0", "end").strip()
                    path = self.engine.create_voice_design(text, desc)
                else:
                    if not hasattr(self, 'ref_file_path'): raise ValueError("No file selected")
                    path = self.engine.create_voice_clone_preview(text, self.ref_file_path)
                self.preview_path = path
                self.after(0, lambda: self.play_btn.configure(state="normal"))
                self.after(0, lambda: self.save_master_btn.configure(state="normal"))
                self.after(0, lambda: self.status_bar.configure(text="Done"))
            except Exception as e:
                self.log(traceback.format_exc())
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, lambda: self.gen_btn.configure(state="normal", text="Generate Preview"))
        threading.Thread(target=run, daemon=True).start()

    def _play_preview(self):
        if self.preview_path: os.startfile(self.preview_path)

    def _save_master(self):
        if self.preview_path:
            import shutil
            target = "master_voice.wav"
            if self.mode_var.get() == "design": shutil.copy(self.preview_path, target)
            else: shutil.copy(self.ref_file_path, target)
            self.master_voice_path = target
            self.studio_status.configure(text="Master Voice: LOADED", text_color="green")
            self._check_render_ready()
            self.log("Master voice saved.")

    def _load_master_voice_direct(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3")])
        if not path:
            return

        # Smart Import processing
        if self.studio_smart_import_var.get():
            self.log("Smart Import: Processing master voice...")
            try:
                from backend import smart_import_audio
                optimized_path, info_msg = smart_import_audio(path, log_callback=self.log)
                self.master_voice_path = optimized_path
                self.log(f"✓ {info_msg}")
            except Exception as e:
                self.log(f"Smart Import failed: {e}, using original file")
                self.master_voice_path = path
        else:
            self.master_voice_path = path

        self.studio_status.configure(text="Master Voice: LOADED", text_color="green")
        self._check_render_ready()
        self.log(f"Loaded voice: {os.path.basename(path)}")

    def _load_book(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", "*.txt *.json"),
                ("Text Files", "*.txt"),
                ("JSON Manifest", "*.json"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return

        # Clear any previously converted files
        if self.engine:
            self.engine.clear_converted_files()

        self.book_path = path
        file_ext = path.lower().split('.')[-1]
        self.book_is_json = file_ext == 'json'

        # Handle different file types
        if file_ext == 'json':
            # JSON manifest - load and display summary
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                title = manifest.get("title", "Untitled")
                author = manifest.get("author", "Unknown")
                chapter_count = len(manifest.get("chapters", []))

                self.book_metadata = {
                    "title": title,
                    "author": author,
                    "chapter_count": chapter_count
                }

                self.book_label.configure(text=f"📖 {title}")
                self.book_info_label.configure(
                    text=f"by {author} • {chapter_count} chapters • JSON Manifest"
                )
                self.log(f"Loaded JSON manifest: '{title}' by {author} ({chapter_count} chapters)")

            except Exception as e:
                self.log(f"Error reading JSON manifest: {e}")
                messagebox.showerror("JSON Error", f"Failed to read JSON manifest:\n{str(e)}")
                self.book_path = None
                self.book_is_json = False
                return

        else:
            # Regular TXT file
            self.book_metadata = None
            self.book_label.configure(text=os.path.basename(path))
            self.book_info_label.configure(text="")
            self.log(f"Loaded book: {path}")

        self._check_render_ready()

    def _check_render_ready(self):
        # Book is ready if we have book_path OR book_metadata (from BookSmith)
        book_ready = self.book_path or (self.book_metadata and self.book_metadata.get("manifest"))

        if self.master_voice_path and book_ready and self.engine:
            self.render_btn.configure(state="normal")

    def _render_book(self):
        if self.is_rendering:
            # STOP COMMAND
            self.stop_event.set()
            self.render_btn.configure(text="Stopping...", state="disabled")
            return

        # START COMMAND
        self.stop_event.clear()
        self.is_rendering = True
        self.render_btn.configure(text="STOP RENDER", fg_color="red", hover_color="darkred")
        
        # Save settings on start
        self._save_settings()
        
        self.status_bar.configure(text="Rendering...")
        self.progress_bar.set(0)
        def progress(p): self.after(0, lambda: self.progress_bar.set(p))
        
        def run():
            try:
                # Check if we're rendering from JSON manifest or regular TXT
                if self.book_is_json:
                    self.log("Using JSON manifest rendering mode (M4B with chapters)")

                    # Check if we have a processed manifest (EPUB/PDF) or JSON file
                    if self.book_metadata and "manifest" in self.book_metadata:
                        # EPUB/PDF processed to manifest - pass manifest directly
                        out = self.engine.render_from_manifest_dict(
                            self.book_metadata["manifest"],
                            self.master_voice_path,
                            progress_callback=progress,
                            stop_event=self.stop_event
                        )
                    else:
                        # JSON file - pass file path
                        out = self.engine.render_from_manifest(
                            self.book_path,
                            self.master_voice_path,
                            progress_callback=progress,
                            stop_event=self.stop_event
                        )
                else:
                    self.log("Using standard TXT rendering mode (single MP3)")
                    out = self.engine.render_book(
                        self.book_path,
                        self.master_voice_path,
                        progress_callback=progress,
                        stop_event=self.stop_event
                    )

                if out:
                    self.after(0, lambda: messagebox.showinfo("Success", f"Audiobook created!\n\nSaved to:\n{out}"))
                    self.after(0, lambda: self.status_bar.configure(text="Done"))
                else:
                    self.after(0, lambda: self.status_bar.configure(text="Stopped"))
            except Exception as e:
                self.log(traceback.format_exc())
                self.after(0, lambda: messagebox.showerror("Error", "Render failed. Check Activity Log for details."))
            finally:
                self.is_rendering = False
                self.after(0, lambda: self.render_btn.configure(state="normal", text="Render Audiobook", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"]))

        threading.Thread(target=run, daemon=True).start()

    def _open_output_folder(self):
        if self.engine: os.startfile(self.engine.output_dir)

    # ========== BookSmith Tab Handlers ========== #

    def _load_epub_pdf(self):
        """Load and process EPUB/PDF file with BookSmith."""
        path = filedialog.askopenfilename(
            filetypes=[
                ("EPUB Files", "*.epub"),
                ("PDF Files", "*.pdf"),
                ("All Supported", "*.epub *.pdf")
            ]
        )
        if not path:
            return

        file_ext = path.lower().split('.')[-1]
        self.booksmith_file_label.configure(text=f"Processing {os.path.basename(path)}...")
        self.booksmith_info_label.configure(text="Please wait...")
        self.process_booksmith_btn.configure(state="disabled")

        def process():
            try:
                from booksmith_module import EPUBProcessor, PDFProcessor

                self.log(f"BookSmith: Processing {file_ext.upper()} file...")

                if file_ext == 'epub':
                    book_data = EPUBProcessor.process(path)
                else:  # pdf
                    def progress(msg):
                        self.log(f"[BookSmith] {msg}")
                    book_data = PDFProcessor.process(path, progress_callback=progress)

                self.booksmith_data = book_data

                # Update UI
                self.after(0, lambda: self._display_booksmith_chapters(book_data))
                self.after(0, lambda: self.booksmith_file_label.configure(text=f"📖 {book_data.title}"))
                self.after(0, lambda: self.booksmith_info_label.configure(
                    text=f"by {book_data.author} • {len(book_data.chapters)} chapters detected"
                ))
                self.after(0, lambda: self.log(f"✓ BookSmith: Loaded '{book_data.title}' ({len(book_data.chapters)} chapters)"))

            except Exception as e:
                self.log(f"BookSmith error: {str(e)}")
                self.log(traceback.format_exc())
                self.after(0, lambda: messagebox.showerror("Processing Error", f"Failed to process {file_ext.upper()}:\n{str(e)}"))
                self.after(0, lambda: self.booksmith_file_label.configure(text="No file loaded"))
                self.after(0, lambda: self.booksmith_info_label.configure(text=""))

        threading.Thread(target=process, daemon=True).start()

    def _display_booksmith_chapters(self, book_data):
        """Display chapter list with checkboxes."""
        try:
            self.log(f"Displaying {len(book_data.chapters)} chapters in BookSmith tab...")

            # Clear existing widgets in scroll frame
            for widget in self.chapter_scroll.winfo_children():
                widget.destroy()

            self.chapter_checkboxes = []
            self.chapter_var_list = []

            if not book_data.chapters:
                error_label = ctk.CTkLabel(
                    self.chapter_scroll,
                    text="No chapters detected in this file",
                    font=("Roboto", 12),
                    text_color="red"
                )
                error_label.pack(pady=20)
                self.log("ERROR: No chapters found in book data")
                return

            # Create checkbox for each chapter
            for i, chapter in enumerate(book_data.chapters):
                # Create frame for this chapter row (clickable)
                frame = ctk.CTkFrame(self.chapter_scroll, fg_color="#2b2b2b", corner_radius=5)
                frame.pack(fill="x", padx=10, pady=5, ipady=5)

                # Make frame clickable to show preview
                frame.bind("<Button-1>", lambda e, idx=i: self._show_chapter_preview(idx))

                # Checkbox variable
                var = tk.BooleanVar(value=True)
                self.chapter_var_list.append(var)

                # Checkbox with chapter title
                checkbox = ctk.CTkCheckBox(
                    frame,
                    text=f"{chapter.id}. {chapter.label}",
                    variable=var,
                    font=("Roboto", 13),
                    command=lambda idx=i: self._on_chapter_toggle(idx)
                )
                checkbox.pack(side="left", padx=10, pady=5)
                # Also bind checkbox click to show preview
                checkbox.bind("<Button-1>", lambda e, idx=i: self._show_chapter_preview(idx))
                self.chapter_checkboxes.append(checkbox)

                # Preview button
                preview_btn = ctk.CTkButton(
                    frame,
                    text="Preview",
                    width=80,
                    command=lambda idx=i: self._show_chapter_preview(idx)
                )
                preview_btn.pack(side="right", padx=10, pady=5)

                # Word count label
                word_count = len(chapter.text.split())
                word_label = ctk.CTkLabel(
                    frame,
                    text=f"({word_count:,} words)",
                    font=("Roboto", 11),
                    text_color="#808080"
                )
                word_label.pack(side="right", padx=15, pady=5)

            # Enable controls
            self.select_all_btn.configure(state="normal")
            self.deselect_all_btn.configure(state="normal")
            self.process_booksmith_btn.configure(state="normal")

            self.log(f"✓ Created {len(self.chapter_checkboxes)} checkboxes in scroll frame")
            self.log(f"✓ Scroll frame has {len(self.chapter_scroll.winfo_children())} child widgets")

        except Exception as e:
            self.log(f"ERROR displaying chapters: {str(e)}")
            self.log(traceback.format_exc())

    def _on_chapter_toggle(self, chapter_idx):
        """Update chapter enabled state when checkbox is toggled."""
        if self.booksmith_data and chapter_idx < len(self.booksmith_data.chapters):
            self.booksmith_data.chapters[chapter_idx].enabled = self.chapter_var_list[chapter_idx].get()

    def _show_chapter_preview(self, chapter_idx):
        """Show chapter text in preview pane for editing."""
        if not self.booksmith_data or chapter_idx >= len(self.booksmith_data.chapters):
            return

        chapter = self.booksmith_data.chapters[chapter_idx]
        self.current_preview_chapter_idx = chapter_idx

        # Update chapter title entry
        self.chapter_title_entry.delete(0, "end")
        self.chapter_title_entry.insert(0, chapter.label)

        # Update preview box with editable text
        self.chapter_preview_box.configure(state="normal")
        self.chapter_preview_box.delete("1.0", "end")

        # Show chapter info header
        info = f"Chapter {chapter.id}\n"
        info += f"Word count: {len(chapter.text.split()):,}\n"
        info += f"Character count: {len(chapter.text):,}\n"
        info += "=" * 60 + "\n\n"

        self.chapter_preview_box.insert("1.0", info + chapter.text)
        # Keep editable
        # self.chapter_preview_box.configure(state="disabled")

        # Enable save/discard buttons
        self.save_chapter_btn.configure(state="normal")
        self.discard_chapter_btn.configure(state="normal")

        self.log(f"Editing: {chapter.label}")

    def _save_chapter_changes(self):
        """Save edited chapter text and title back to BookData."""
        if self.current_preview_chapter_idx is None or not self.booksmith_data:
            return

        chapter_idx = self.current_preview_chapter_idx
        if chapter_idx >= len(self.booksmith_data.chapters):
            return

        chapter = self.booksmith_data.chapters[chapter_idx]

        # Get edited content
        full_content = self.chapter_preview_box.get("1.0", "end-1c")

        # Remove the info header (everything before the "====" line)
        lines = full_content.split('\n')
        separator_idx = -1
        for i, line in enumerate(lines):
            if '=' * 60 in line:
                separator_idx = i
                break

        if separator_idx >= 0 and separator_idx + 1 < len(lines):
            # Get text after separator (skip separator and empty line)
            edited_text = '\n'.join(lines[separator_idx + 2:])
        else:
            # Fallback: use all content
            edited_text = full_content

        # Update chapter data
        old_label = chapter.label
        new_label = self.chapter_title_entry.get().strip()

        if new_label and new_label != old_label:
            chapter.label = new_label
            # Update checkbox text
            if chapter_idx < len(self.chapter_checkboxes):
                self.chapter_checkboxes[chapter_idx].configure(text=f"{chapter.id}. {new_label}")
            self.log(f"Updated chapter title: '{old_label}' → '{new_label}'")

        chapter.text = edited_text.strip()

        self.log(f"✓ Saved changes to chapter {chapter.id}: {chapter.label}")
        messagebox.showinfo("Saved", f"Changes saved to:\n{chapter.label}")

        # Refresh preview to show updated word counts
        self._show_chapter_preview(chapter_idx)

    def _discard_chapter_changes(self):
        """Reload the original chapter text without saving."""
        if self.current_preview_chapter_idx is not None:
            self._show_chapter_preview(self.current_preview_chapter_idx)
            self.log("Discarded changes")

    def _select_all_chapters(self):
        """Select all chapters."""
        if not self.booksmith_data:
            return

        for i, var in enumerate(self.chapter_var_list):
            var.set(True)
            if i < len(self.booksmith_data.chapters):
                self.booksmith_data.chapters[i].enabled = True

        self.log("Selected all chapters")

    def _deselect_all_chapters(self):
        """Deselect all chapters."""
        if not self.booksmith_data:
            return

        for i, var in enumerate(self.chapter_var_list):
            var.set(False)
            if i < len(self.booksmith_data.chapters):
                self.booksmith_data.chapters[i].enabled = False

        self.log("Deselected all chapters")

    def _process_booksmith_to_studio(self):
        """Process selected chapters and send manifest to Studio tab."""
        if not self.booksmith_data:
            messagebox.showwarning("No Book", "Please load an EPUB/PDF file first.")
            return

        # Update chapter enabled states from checkboxes
        for i, var in enumerate(self.chapter_var_list):
            if i < len(self.booksmith_data.chapters):
                self.booksmith_data.chapters[i].enabled = var.get()

        # Count enabled chapters
        enabled_count = sum(1 for ch in self.booksmith_data.chapters if ch.enabled)

        if enabled_count == 0:
            messagebox.showwarning("No Chapters Selected", "Please select at least one chapter to process.")
            return

        self.log(f"Processing {enabled_count} selected chapters...")

        # Generate manifest from enabled chapters
        manifest = self.booksmith_data.to_manifest()

        # Store book path and metadata for rendering
        self.book_path = None  # No file path needed (using manifest directly)
        self.book_metadata = {
            "title": manifest["title"],
            "author": manifest["author"],
            "chapter_count": len(manifest["chapters"]),
            "manifest": manifest
        }
        self.book_is_json = True  # Treat as JSON manifest for rendering

        # Update Studio tab display to show book is loaded
        self.book_label.configure(text=f"📖 {manifest['title']}")
        self.book_info_label.configure(
            text=f"by {manifest['author']} • {len(manifest['chapters'])} chapters • From BookSmith"
        )

        self.log(f"✓ Book ready: '{manifest['title']}' with {len(manifest['chapters'])} chapters")

        # Mark book as ready for rendering
        self._check_render_ready()

        # Switch to Studio tab
        self.tab_view.set("The Studio (Rendering)")

        messagebox.showinfo(
            "Ready to Render",
            f"✓ Book: {manifest['title']}\n" 
            f"✓ {len(manifest['chapters'])} chapters selected\n\n" 
            f"Next step:\n" 
            f"1. Load your master voice (if not already loaded)\n" 
            f"2. Click 'Render Audiobook'"
        )

    def _open_output_folder(self):
        if self.engine: os.startfile(self.engine.output_dir)

if __name__ == "__main__":
    app = Vox1App()
    app.mainloop()
