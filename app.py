import customtkinter as ctk
import tkinter as tk
import threading
import os
import sys
import json
import traceback
from tkinter import filedialog, messagebox

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
        self.chapter_music_dropdown_vars = []  # List of StringVars for per-chapter music track
        self.current_preview_chapter_idx = None  # Track which chapter is being previewed

        # Background music state
        self.bg_music_enabled = False
        self.bg_music_tracks = []           # list of file paths
        self.bg_music_track_widgets = []    # list of (label, remove_btn) tuples
        self.bg_music_mode = "simple"       # "simple" or "per_chapter"
        self.bg_music_volume_db = -25
        self.bg_music_fade_ms = 3000
        self.bg_music_chapter_map = {}      # chapter_idx → track_idx (populated by BookSmith)
        
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
            "last_voice": None,
            "batch_size": 10,
            "chunk_size": 500,
            "guidance_scale": 2.0,
            "num_step": 32,
            "speed": 1.0,
            "show_vram": True,
            "show_timing": True,
            "debug_mode": False,
            "smart_import": True,
            # Background music
            "bg_music_enabled": False,
            "bg_music_tracks": [],
            "bg_music_mode": "simple",
            "bg_music_volume_db": -25,
            "bg_music_fade_ms": 3000,
            "bg_music_random": False,
        }

    def _save_settings(self):
        try:
            self.settings["last_voice"] = self.master_voice_path
            if hasattr(self, 'batch_size_var'):
                self.settings["batch_size"] = int(self.batch_size_var.get())
            if hasattr(self, 'chunk_size_var'):
                self.settings["chunk_size"] = int(self.chunk_size_var.get())
            if hasattr(self, 'guidance_scale_var'):
                self.settings["guidance_scale"] = float(self.guidance_scale_var.get())
            if hasattr(self, 'num_step_var'):
                self.settings["num_step"] = int(self.num_step_var.get())
            if hasattr(self, 'speed_var'):
                self.settings["speed"] = float(self.speed_var.get())
            if hasattr(self, 'show_vram_var'):
                self.settings["show_vram"] = self.show_vram_var.get()
            if hasattr(self, 'show_timing_var'):
                self.settings["show_timing"] = self.show_timing_var.get()
            if hasattr(self, 'debug_mode_var'):
                self.settings["debug_mode"] = self.debug_mode_var.get()
            if hasattr(self, 'smart_import_var'):
                self.settings["smart_import"] = self.smart_import_var.get()
            # Background music
            self.settings["bg_music_enabled"] = self.bg_music_enabled
            self.settings["bg_music_tracks"] = self.bg_music_tracks
            self.settings["bg_music_mode"] = self.bg_music_mode
            self.settings["bg_music_volume_db"] = self.bg_music_volume_db
            self.settings["bg_music_fade_ms"] = self.bg_music_fade_ms
            self.settings["bg_music_random"] = self.bg_random_var.get() if hasattr(self, 'bg_random_var') else False
            with open(self.settings_file, 'w') as f: json.dump(self.settings, f, indent=2)
        except: pass

    def _init_from_settings(self):
        self._start_engine_thread()

        # Restore background music settings
        self.bg_music_enabled = self.settings.get("bg_music_enabled", False)
        self.bg_music_tracks = [t for t in self.settings.get("bg_music_tracks", []) if os.path.exists(t)]
        self.bg_music_mode = self.settings.get("bg_music_mode", "simple")
        self.bg_music_volume_db = self.settings.get("bg_music_volume_db", -25)
        self.bg_music_fade_ms = self.settings.get("bg_music_fade_ms", 3000)
        self.bg_music_random = self.settings.get("bg_music_random", False)

        last_voice = self.settings.get("last_voice")
        if last_voice and os.path.exists(last_voice):
            self.master_voice_path = last_voice
            self.studio_status.configure(text="Master Voice: LOADED", text_color="green")
            self.log(f"Restored previous voice: {os.path.basename(last_voice)}")

        # Restore background music UI after a short delay (widgets need to exist)
        self.after(100, self._update_bg_music_ui_from_state)

        smart_import_enabled = self.settings.get("smart_import", True)
        self.smart_import_var.set(smart_import_enabled)
        self.studio_smart_import_var.set(smart_import_enabled)

    def _setup_ui(self):
        # Header Frame
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="Vox-1 // AI Audio Engine", font=("Roboto", 20, "bold"))
        self.header_label.pack(side="left", padx=20, pady=10)
        
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
        self.status_bar = ctk.CTkLabel(self, text="Loading OmniVoice engine...", anchor="w")
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
        self.tab_lab.grid_rowconfigure(0, weight=1)
        
        # Main scrollable container - ensures all content is always reachable
        self.lab_scroll = ctk.CTkScrollableFrame(self.tab_lab)
        self.lab_scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.lab_scroll.grid_columnconfigure(0, weight=1)
        
        self.mode_frame = ctk.CTkFrame(self.lab_scroll)
        self.mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.mode_var = ctk.StringVar(value="design")
        self.radio_design = ctk.CTkRadioButton(self.mode_frame, text="Design Voice", variable=self.mode_var, value="design", command=self._update_lab_mode)
        self.radio_design.pack(side="left", padx=20, pady=10)
        self.radio_clone = ctk.CTkRadioButton(self.mode_frame, text="Clone Voice", variable=self.mode_var, value="clone", command=self._update_lab_mode)
        self.radio_clone.pack(side="left", padx=20, pady=10)
        
        # --- Design Voice section ---
        self.design_frame = ctk.CTkFrame(self.lab_scroll)
        self.design_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.design_frame.grid_columnconfigure(0, weight=1)
        
        self.desc_label = ctk.CTkLabel(self.design_frame, text="Voice Attributes (comma-separated):", anchor="w")
        self.desc_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        self.desc_entry = ctk.CTkTextbox(self.design_frame, height=50)
        self.desc_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.desc_entry.insert("0.0", "male, moderate pitch, american accent")

        # Compact valid attributes info (clickable expandable area)
        self.attr_info = ctk.CTkLabel(
            self.design_frame,
            text=("Valid: male/female | child/teenager/young adult/middle-aged/elderly | "
                   "very low/low/moderate/high/very high pitch | whisper | "
                   "american/british/australian/canadian/indian/etc. accent"),
            font=("Roboto", 10),
            text_color="gray",
            anchor="w",
            justify="left",
            wraplength=700
        )
        self.attr_info.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        
        # --- Clone Voice section ---
        self.clone_frame = ctk.CTkFrame(self.lab_scroll)
        self.clone_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.clone_frame.grid_columnconfigure(0, weight=1)
        
        self.file_label = ctk.CTkLabel(self.clone_frame, text="Reference Audio:", anchor="w")
        self.file_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        self.file_btn = ctk.CTkButton(self.clone_frame, text="Choose File...", command=self._choose_ref_file)
        self.file_btn.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.ref_file_path_label = ctk.CTkLabel(self.clone_frame, text="No file selected", text_color="gray")
        self.ref_file_path_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Smart Import checkbox for Lab tab
        self.smart_import_var = ctk.BooleanVar(value=True)  # Default ON
        self.smart_import_checkbox = ctk.CTkCheckBox(
            self.clone_frame,
            text="Smart Import (auto-optimize audio)",
            variable=self.smart_import_var,
            font=("Arial", 12)
        )
        self.smart_import_checkbox.grid(row=3, column=0, sticky="w", padx=10, pady=(5, 10))
        
        # --- Preview section (always visible) ---
        self.preview_frame = ctk.CTkFrame(self.lab_scroll)
        self.preview_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        self.preview_text_label = ctk.CTkLabel(self.preview_frame, text="Preview Text:", anchor="w")
        self.preview_text_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
        self.preview_entry = ctk.CTkEntry(self.preview_frame)
        self.preview_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.preview_entry.insert(0, "This is a test of the voice generation system.")
        
        # --- Action buttons ---
        self.action_frame = ctk.CTkFrame(self.lab_scroll, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        
        self.gen_btn = ctk.CTkButton(self.action_frame, text="Generate Preview", command=self._generate_preview, state="disabled")
        self.gen_btn.pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(self.action_frame, text="Play Preview", command=self._play_preview, state="disabled", fg_color="green")
        self.play_btn.pack(side="left", padx=5)
        self.save_master_btn = ctk.CTkButton(self.action_frame, text="Save as Master Voice", command=self._save_master, state="disabled", fg_color="orange")
        self.save_master_btn.pack(side="right", padx=5)

        # Start with design mode visible
        self._update_lab_mode()

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

        # ========== Background Music Section ==========
        self.bg_music_separator = ctk.CTkFrame(self.content_frame, height=2, fg_color="gray30")
        self.bg_music_separator.pack(fill="x", padx=20, pady=(20, 5))

        self.bg_music_header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.bg_music_header_frame.pack(fill="x", padx=10, pady=(5, 0))

        self.bg_music_enabled_var = ctk.BooleanVar(value=self.bg_music_enabled)
        self.bg_music_checkbox = ctk.CTkCheckBox(
            self.bg_music_header_frame,
            text="🎵 Background Music  (experimental)",
            variable=self.bg_music_enabled_var,
            font=("Roboto", 13, "bold"),
            command=self._toggle_bg_music_ui
        )
        self.bg_music_checkbox.pack(side="left", padx=10, pady=5)

        # Background Music controls (hidden by default until enabled)
        self.bg_music_frame = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=8)

        # Mode selection
        mode_row = ctk.CTkFrame(self.bg_music_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=15, pady=(10, 5))

        self.bg_music_mode_var = ctk.StringVar(value=self.bg_music_mode)
        ctk.CTkLabel(mode_row, text="Mode:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.bg_simple_radio = ctk.CTkRadioButton(
            mode_row, text="Simple Additive (auto-cycle)",
            variable=self.bg_music_mode_var, value="simple",
            command=self._update_bg_music_mode
        )
        self.bg_simple_radio.pack(side="left", padx=5)
        self.bg_perchapter_radio = ctk.CTkRadioButton(
            mode_row, text="Per-Chapter",
            variable=self.bg_music_mode_var, value="per_chapter",
            command=self._update_bg_music_mode
        )
        self.bg_perchapter_radio.pack(side="left", padx=5)

        # Mode info label
        self.bg_mode_info = ctk.CTkLabel(
            self.bg_music_frame,
            text="Simple: tracks cycle through chapters automatically.  Per-Chapter: assign tracks in BookSmith tab.",
            font=("Roboto", 10),
            text_color="gray",
            wraplength=600,
            justify="left"
        )
        self.bg_mode_info.pack(fill="x", padx=15, pady=(0, 5))

        # Random toggle (only applies in simple mode)
        self.bg_random_var = ctk.BooleanVar(value=False)
        self.bg_random_checkbox = ctk.CTkCheckBox(
            self.bg_music_frame,
            text="Random (pick a different track each chapter, no repeats)",
            variable=self.bg_random_var,
            font=("Roboto", 11)
        )
        self.bg_random_checkbox.pack(anchor="w", padx=15, pady=(0, 5))

        # Track file management
        self.bg_tracks_frame = ctk.CTkFrame(self.bg_music_frame, fg_color="transparent")
        self.bg_tracks_frame.pack(fill="x", padx=15, pady=5)

        self.bg_add_tracks_btn = ctk.CTkButton(
            self.bg_tracks_frame,
            text="+ Add Music Files",
            command=self._add_bg_music_tracks,
            width=140
        )
        self.bg_add_tracks_btn.pack(side="left", padx=5)

        self.bg_tracks_label = ctk.CTkLabel(
            self.bg_tracks_frame,
            text="No music files loaded",
            font=("Roboto", 11),
            text_color="gray"
        )
        self.bg_tracks_label.pack(side="left", padx=10)

        # Track list (dynamic)
        self.bg_track_list_frame = ctk.CTkFrame(self.bg_music_frame, fg_color="transparent")
        self.bg_track_list_frame.pack(fill="x", padx=25, pady=5)

        # Volume slider
        vol_row = ctk.CTkFrame(self.bg_music_frame, fg_color="transparent")
        vol_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(vol_row, text="Volume:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.bg_volume_var = ctk.DoubleVar(value=abs(self.bg_music_volume_db))
        self.bg_volume_slider = ctk.CTkSlider(
            vol_row, from_=10, to=40, number_of_steps=30,
            variable=self.bg_volume_var, command=self._update_bg_volume_label
        )
        self.bg_volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.bg_volume_label = ctk.CTkLabel(vol_row, text=f"-{self.bg_volume_var.get():.0f} dB", font=("Roboto", 12), width=60)
        self.bg_volume_label.pack(side="left", padx=5)

        # Fade slider
        fade_row = ctk.CTkFrame(self.bg_music_frame, fg_color="transparent")
        fade_row.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(fade_row, text="Crossfade:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.bg_fade_var = ctk.DoubleVar(value=self.bg_music_fade_ms / 1000)
        self.bg_fade_slider = ctk.CTkSlider(
            fade_row, from_=0.5, to=10.0, number_of_steps=19,
            variable=self.bg_fade_var, command=self._update_bg_fade_label
        )
        self.bg_fade_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.bg_fade_label = ctk.CTkLabel(fade_row, text=f"{self.bg_fade_var.get():.1f}s", font=("Roboto", 12), width=60)
        self.bg_fade_label.pack(side="left", padx=5)

        # Update track list display if any tracks were restored from settings
        if self.bg_music_tracks:
            self._refresh_bg_track_list()

        # Render button
        self.render_btn = ctk.CTkButton(self.content_frame, text="Render Audiobook", command=self._render_book, state="disabled", height=50, font=("Roboto", 16))
        self.render_btn.pack(pady=30)
        self.open_output_btn = ctk.CTkButton(self.content_frame, text="Open Output Folder", command=self._open_output_folder, fg_color="#444444")
        self.open_output_btn.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.content_frame)
        self.progress_bar.pack(pady=10, padx=50, fill="x")
        self.progress_bar.set(0)

        # If music was enabled from saved settings, show the frame
        if self.bg_music_enabled:
            self.bg_music_frame.pack(fill="x", padx=10, pady=5)

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

        batch_label = ctk.CTkLabel(batch_frame, text="Batch Size (Default: 10)",
                                   font=("Roboto", 14, "bold"))
        batch_label.grid(row=0, column=0, sticky="w", pady=5)

        self.batch_size_var = ctk.IntVar(value=self.settings.get("batch_size", 10))
        self.batch_slider = ctk.CTkSlider(batch_frame, from_=1, to=64, number_of_steps=63,
                                         variable=self.batch_size_var, command=self._update_batch_label)
        self.batch_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.batch_value_label = ctk.CTkLabel(batch_frame, text=f"Current: {self.batch_size_var.get()}",
                                             font=("Roboto", 12))
        self.batch_value_label.grid(row=2, column=0, sticky="w")

        batch_info = ctk.CTkLabel(batch_frame,
            text="ℹ️ Number of text chunks processed simultaneously on your GPU.\n" +
                 "   • 8-10 GB VRAM: start at 4-6\n" +
                 "   • 12 GB VRAM: start at 8-10 (tested stable on RTX 4070 Ti)\n" +
                 "   • 16-24 GB VRAM: start at 16-32\n" +
                 "   • Watch VRAM in Activity Log — if below 50%, increase batch size",
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
        self.chunk_slider = ctk.CTkSlider(chunk_frame, from_=100, to=5000, number_of_steps=98,
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
                 "   • Range: 100-5000 characters",
            font=("Roboto", 11), justify="left", text_color="gray")
        chunk_info.grid(row=3, column=0, sticky="w", pady=5)

        # Separator
        sep2 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep2.grid(row=5, column=0, sticky="ew", pady=15)

        # Quality & Performance Section
        quality_label = ctk.CTkLabel(self.advanced_scroll, text="🎛️ Generation Quality",
                                     font=("Roboto", 16, "bold"))
        quality_label.grid(row=6, column=0, pady=(10, 10), sticky="w")

        # Guidance Scale
        gs_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        gs_frame.grid(row=7, column=0, sticky="ew", pady=10)
        gs_frame.grid_columnconfigure(0, weight=1)

        gs_label = ctk.CTkLabel(gs_frame, text="Guidance Scale (Default: 2.0)",
                                font=("Roboto", 14, "bold"))
        gs_label.grid(row=0, column=0, sticky="w", pady=5)

        self.guidance_scale_var = ctk.DoubleVar(value=self.settings.get("guidance_scale", 2.0))
        self.gs_slider = ctk.CTkSlider(gs_frame, from_=1.0, to=4.0, number_of_steps=30,
                                       variable=self.guidance_scale_var, command=self._update_gs_label)
        self.gs_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.gs_value_label = ctk.CTkLabel(gs_frame, text=f"Current: {self.guidance_scale_var.get():.1f}",
                                           font=("Roboto", 12))
        self.gs_value_label.grid(row=2, column=0, sticky="w")

        gs_info = ctk.CTkLabel(gs_frame,
            text="ℹ️ How closely generation follows the reference/instruction:\n" +
                 "   • 1.0-1.5 = Low guidance (more variation from reference)\n" +
                 "   • 2.0 = Default (good balance)\n" +
                 "   • 3.0-4.0 = High guidance (closer to reference, less creative)",
            font=("Roboto", 11), justify="left", text_color="gray")
        gs_info.grid(row=3, column=0, sticky="w", pady=5)

        # Num Diffusion Steps
        step_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        step_frame.grid(row=8, column=0, sticky="ew", pady=10)
        step_frame.grid_columnconfigure(0, weight=1)

        step_label = ctk.CTkLabel(step_frame, text="Diffusion Steps (Default: 32)",
                                  font=("Roboto", 14, "bold"))
        step_label.grid(row=0, column=0, sticky="w", pady=5)

        self.num_step_var = ctk.IntVar(value=self.settings.get("num_step", 32))
        self.step_slider = ctk.CTkSlider(step_frame, from_=8, to=64, number_of_steps=56,
                                        variable=self.num_step_var, command=self._update_step_label)
        self.step_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.step_value_label = ctk.CTkLabel(step_frame, text=f"Current: {self.num_step_var.get()}",
                                            font=("Roboto", 12))
        self.step_value_label.grid(row=2, column=0, sticky="w")

        step_info = ctk.CTkLabel(step_frame,
            text="ℹ️ Number of iterative refinement steps (speed vs quality):\n" +
                 "   • 8-16 = Fastest, slightly lower quality\n" +
                 "   • 32 = Default (good balance)\n" +
                 "   • 48-64 = Highest quality, slower",
            font=("Roboto", 11), justify="left", text_color="gray")
        step_info.grid(row=3, column=0, sticky="w", pady=5)

        # Speaking Speed
        speed_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        speed_frame.grid(row=9, column=0, sticky="ew", pady=10)
        speed_frame.grid_columnconfigure(0, weight=1)

        speed_label = ctk.CTkLabel(speed_frame, text="Speaking Speed (Default: 1.0)",
                                   font=("Roboto", 14, "bold"))
        speed_label.grid(row=0, column=0, sticky="w", pady=5)

        self.speed_var = ctk.DoubleVar(value=self.settings.get("speed", 1.0))
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.5, to=2.0, number_of_steps=30,
                                         variable=self.speed_var, command=self._update_speed_label)
        self.speed_slider.grid(row=1, column=0, sticky="ew", pady=5)

        self.speed_value_label = ctk.CTkLabel(speed_frame, text=f"Current: {self.speed_var.get():.2f}x",
                                             font=("Roboto", 12))
        self.speed_value_label.grid(row=2, column=0, sticky="w")

        speed_info = ctk.CTkLabel(speed_frame,
            text=("ℹ️ Speaking rate multiplier:\n"
                   "   • 0.50 = Half speed (slower, more deliberate)\n"
                   "   • 1.00 = Normal speed (default)\n"
                   "   • 1.50 = 50% faster\n"
                   "   • 2.00 = Double speed"),
            font=("Roboto", 11), justify="left", text_color="gray")
        speed_info.grid(row=3, column=0, sticky="w", pady=5)

        # Separator
        sep3 = ctk.CTkFrame(self.advanced_scroll, height=2, fg_color="gray30")
        sep3.grid(row=10, column=0, sticky="ew", pady=15)

        # Monitoring Section
        monitor_label = ctk.CTkLabel(self.advanced_scroll, text="📊 Monitoring & Logging",
                                     font=("Roboto", 16, "bold"))
        monitor_label.grid(row=11, column=0, pady=(10, 10), sticky="w")

        monitor_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        monitor_frame.grid(row=12, column=0, sticky="ew", pady=10)

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
        sep4.grid(row=13, column=0, sticky="ew", pady=15)

        # Quick Tips Section
        tips_label = ctk.CTkLabel(self.advanced_scroll, text="💡 Quick Tips",
                                 font=("Roboto", 16, "bold"))
        tips_label.grid(row=14, column=0, pady=(10, 10), sticky="w")

        tips_text = (
            "• Start with defaults if unsure\n" 
            "• Max VRAM used during rendering is ~3.5GB (model) + chunks\n" 
            "• If VRAM stays under 50%, increase batch size for faster rendering\n" 
            "• If you get memory errors, decrease batch size by 2-3\n" 
            "• Guidance Scale 2.0 and Diffusion Steps 32 work well for most voices"
        )
        tips_display = ctk.CTkLabel(self.advanced_scroll, text=tips_text,
                                    font=("Roboto", 11), justify="left", text_color="lightblue")
        tips_display.grid(row=15, column=0, sticky="w", pady=5)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self.advanced_scroll, fg_color="transparent")
        button_frame.grid(row=16, column=0, sticky="ew", pady=20)
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

    def _update_gs_label(self, value):
        self.gs_value_label.configure(text=f"Current: {float(value):.1f}")

    def _update_step_label(self, value):
        self.step_value_label.configure(text=f"Current: {int(float(value))}")

    def _update_speed_label(self, value):
        self.speed_value_label.configure(text=f"Current: {float(value):.2f}x")

    def _auto_detect_batch_size(self):
        """Auto-detect optimal batch size based on available VRAM."""
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                total_vram_gb = props.total_memory / (1024**3)

                # OmniVoice diffusion model — VRAM-efficient, conservative estimates
                if total_vram_gb >= 22:  # 4090 (24GB)
                    suggested = 24
                elif total_vram_gb >= 16:  # 4080 (16GB)
                    suggested = 16
                elif total_vram_gb >= 11:  # 4070 Ti / 3080 Ti (12GB)
                    suggested = 10
                elif total_vram_gb >= 7:   # 3070 / 4060 Ti (8GB)
                    suggested = 6
                elif total_vram_gb >= 5:   # 6GB cards
                    suggested = 4
                else:
                    suggested = 2

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
        self.batch_size_var.set(10)
        self.chunk_size_var.set(500)
        self.guidance_scale_var.set(2.0)
        self.num_step_var.set(32)
        self.speed_var.set(1.0)
        self.show_vram_var.set(True)
        self.show_timing_var.set(True)
        self.debug_mode_var.set(False)
        self._update_batch_label(10)
        self._update_chunk_label(500)
        self._update_gs_label(2.0)
        self._update_step_label(32)
        self._update_speed_label(1.0)
        messagebox.showinfo("Reset", "Advanced settings reset to defaults!")

    def _apply_advanced_settings(self):
        """Apply and save advanced settings without reloading the model."""
        self._save_settings()

        # Update engine parameters in-place (no model reload needed)
        if self.engine:
            self.engine.batch_size = int(self.batch_size_var.get())
            self.engine.chunk_size = int(self.chunk_size_var.get())
            self.engine.guidance_scale = float(self.guidance_scale_var.get())
            self.engine.num_step = int(self.num_step_var.get())
            self.engine.speed = float(self.speed_var.get())

        msg = (f"Advanced settings applied!\n\n" +
            f"Batch Size: {self.batch_size_var.get()}\n" +
            f"Chunk Size: {self.chunk_size_var.get()}\n" +
            f"Guidance Scale: {self.guidance_scale_var.get():.1f}\n" +
            f"Diffusion Steps: {self.num_step_var.get()}\n" +
            f"Speed: {self.speed_var.get():.2f}x")
        self.log("Settings applied: " + msg.replace('\n', ' | '))
        messagebox.showinfo("Settings Applied", msg)

    def _start_engine_thread(self):
        def load():
            try:
                self.engine = None
                batch_size = self.settings.get("batch_size", 2)
                chunk_size = self.settings.get("chunk_size", 500)
                guidance_scale = self.settings.get("guidance_scale", 2.0)
                num_step = self.settings.get("num_step", 32)
                speed = self.settings.get("speed", 1.0)
                self.engine = AudioEngine(
                    log_callback=self.log,
                    batch_size=batch_size,
                    chunk_size=chunk_size,
                    guidance_scale=guidance_scale,
                    num_step=num_step,
                    speed=speed,
                )
                self.after(0, lambda: self.status_bar.configure(text="System Ready — OmniVoice"))
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
            self.design_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            self.clone_frame.grid_forget()
        else:
            self.design_frame.grid_forget()
            self.clone_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

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
                    if not desc:
                        raise ValueError("Please enter voice attributes (e.g. 'male, moderate pitch, british accent')")
                    path = self.engine.create_voice_design(text, desc)
                else:
                    if not hasattr(self, 'ref_file_path'): raise ValueError("No file selected")
                    path = self.engine.create_voice_clone_preview(text, self.ref_file_path)
                self.preview_path = path
                self.after(0, lambda: self.play_btn.configure(state="normal"))
                self.after(0, lambda: self.save_master_btn.configure(state="normal"))
                self.after(0, lambda: self.status_bar.configure(text="Done"))
            except ValueError as e:
                err = str(e)
                self.log(f"Input error: {err}")
                # Check if it's an OmniVoice unsupported instruct error - show helpful message
                if "Unsupported instruct items" in err or "unsupported" in err.lower():
                    valid = ("Valid voice attributes (comma-separated):\n\n"
                             "Gender: male, female\n"
                             "Age: child, teenager, young adult, middle-aged, elderly\n"
                             "Pitch: very low, low, moderate, high, very high\n"
                             "Style: whisper\n"
                             "Accent: american, british, australian, canadian, indian, \n"
                             "        chinese, japanese, korean, portuguese, russian\n\n"
                             "Example: 'female, british accent'")
                    self.after(0, lambda: messagebox.showerror("Invalid Voice Attributes", valid))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", err))
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

    # ========== Background Music Handlers ========== #

    def _toggle_bg_music_ui(self):
        """Show/hide background music controls when checkbox is toggled."""
        if self.bg_music_enabled_var.get():
            self.bg_music_frame.pack(fill="x", padx=10, pady=5)
            self.bg_music_enabled = True
        else:
            self.bg_music_frame.pack_forget()
            self.bg_music_enabled = False

    def _add_bg_music_tracks(self):
        """Open file dialog to add music tracks."""
        paths = filedialog.askopenfilenames(
            title="Select Background Music Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.ogg *.m4a")]
        )
        if not paths:
            return

        for p in paths:
            if p not in self.bg_music_tracks:
                self.bg_music_tracks.append(p)

        self._refresh_bg_track_list()
        self.log(f"Added {len(paths)} background music track(s)")

    def _remove_bg_music_track(self, index):
        """Remove a music track by index."""
        if 0 <= index < len(self.bg_music_tracks):
            removed = os.path.basename(self.bg_music_tracks.pop(index))
            self._refresh_bg_track_list()
            self.log(f"Removed track: {removed}")

    def _refresh_bg_track_list(self):
        """Refresh the track list UI widgets."""
        # Clear old widgets
        for widget in self.bg_track_list_frame.winfo_children():
            widget.destroy()
        self.bg_music_track_widgets = []

        if not self.bg_music_tracks:
            self.bg_tracks_label.configure(text="No music files loaded")
            return

        self.bg_tracks_label.configure(text=f"{len(self.bg_music_tracks)} track(s) loaded")

        for idx, track_path in enumerate(self.bg_music_tracks):
            row = ctk.CTkFrame(self.bg_track_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)

            num_label = ctk.CTkLabel(row, text=f"{idx + 1}.", font=("Roboto", 11), width=25)
            num_label.pack(side="left")

            name_label = ctk.CTkLabel(
                row,
                text=os.path.basename(track_path),
                font=("Roboto", 11),
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True, padx=5)

            remove_btn = ctk.CTkButton(
                row,
                text="×",
                width=28,
                height=22,
                fg_color="#cc4444",
                hover_color="#aa2222",
                font=("Roboto", 14, "bold"),
                command=lambda i=idx: self._remove_bg_music_track(i)
            )
            remove_btn.pack(side="right")

            self.bg_music_track_widgets.append((name_label, remove_btn))

        # Refresh BookSmith chapter dropdowns if in per-chapter mode
        if self.bg_music_mode_var.get() == "per_chapter" and self.booksmith_data:
            self._display_booksmith_chapters(self.booksmith_data)

    def _update_bg_music_mode(self):
        """Called when mode radio buttons change."""
        self.bg_music_mode = self.bg_music_mode_var.get()
        if self.bg_music_mode == "per_chapter":
            self.bg_mode_info.configure(
                text="Per-Chapter: assign tracks in BookSmith tab after loading a book. Each chapter gets its own track picker."
            )
        else:
            self.bg_mode_info.configure(
                text="Simple: tracks play in order (or random if checked). Per-Chapter: assign tracks in BookSmith tab."
            )
        # Show/hide random checkbox based on mode
        if self.bg_music_mode == "simple":
            self.bg_random_checkbox.pack(anchor="w", padx=15, pady=(0, 5))
        else:
            self.bg_random_checkbox.pack_forget()
        # Refresh BookSmith chapter dropdowns if book is loaded
        if self.booksmith_data:
            self._display_booksmith_chapters(self.booksmith_data)

    def _update_bg_volume_label(self, value):
        """Update the volume label when slider moves."""
        self.bg_volume_label.configure(text=f"-{float(value):.0f} dB")
        self.bg_music_volume_db = -int(float(value))

    def _update_bg_fade_label(self, value):
        """Update the fade label when slider moves."""
        self.bg_fade_label.configure(text=f"{float(value):.1f}s")
        self.bg_music_fade_ms = int(float(value) * 1000)

    def _update_bg_music_ui_from_state(self):
        """Sync UI widgets with current state (used after loading settings)."""
        self.bg_music_enabled_var.set(self.bg_music_enabled)
        self.bg_music_mode_var.set(self.bg_music_mode)
        self.bg_volume_var.set(abs(self.bg_music_volume_db))
        self.bg_volume_label.configure(text=f"-{abs(self.bg_music_volume_db):.0f} dB")
        self.bg_fade_var.set(self.bg_music_fade_ms / 1000)
        self.bg_fade_label.configure(text=f"{self.bg_music_fade_ms / 1000:.1f}s")
        if hasattr(self, 'bg_random_var'):
            self.bg_random_var.set(self.bg_music_random)
        if self.bg_music_enabled:
            self.bg_music_frame.pack(fill="x", padx=10, pady=5)
        self._refresh_bg_track_list()

    def _apply_bg_music_to_engine(self):
        """Push current UI settings to the engine."""
        if not self.engine:
            return
        self.engine.set_background_music(
            enabled=self.bg_music_enabled_var.get(),
            tracks=self.bg_music_tracks,
            mode=self.bg_music_mode_var.get(),
            chapter_map=self.bg_music_chapter_map,
            volume_db=-int(self.bg_volume_var.get()),
            fade_ms=int(self.bg_fade_var.get() * 1000),
            randomize=self.bg_random_var.get(),
        )

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

        # Push background music settings to engine
        self._apply_bg_music_to_engine()
        if self.bg_music_enabled_var.get() and self.bg_music_tracks:
            self.log(f"Background music enabled: {self.bg_music_mode_var.get()} mode, {len(self.bg_music_tracks)} track(s)")

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
                            stop_event=self.stop_event,
                            chunk_size=int(self.chunk_size_var.get()) # UPDATED: Pass manual chunk size
                        )
                    else:
                        # JSON file - pass file path
                        out = self.engine.render_from_manifest(
                            self.book_path,
                            self.master_voice_path,
                            progress_callback=progress,
                            stop_event=self.stop_event,
                            chunk_size=int(self.chunk_size_var.get()) # UPDATED: Pass manual chunk size
                        )
                else:
                    self.log("Using standard TXT rendering mode (single MP3)")
                    # NOTE: render_book (txt) doesn't support the override arg yet, relies on engine init
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
            self.chapter_music_dropdown_vars = []

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

                # Music track dropdown (per-chapter mode)
                show_music = (
                    hasattr(self, 'bg_music_enabled_var')
                    and self.bg_music_enabled_var.get()
                    and self.bg_music_mode_var.get() == "per_chapter"
                    and self.bg_music_tracks
                )
                if show_music:
                    track_options = [os.path.basename(t) for t in self.bg_music_tracks]
                    # Default to cycling track
                    default_track = track_options[i % len(track_options)]

                    track_var = tk.StringVar(value=default_track)
                    self.chapter_music_dropdown_vars.append(track_var)

                    track_dropdown = ctk.CTkOptionMenu(
                        frame,
                        values=track_options,
                        variable=track_var,
                        width=140,
                        font=("Roboto", 10),
                        command=lambda choice, idx=i: self._on_chapter_track_change(idx, choice)
                    )
                    track_dropdown.pack(side="right", padx=(5, 5), pady=5)

                    music_label = ctk.CTkLabel(
                        frame,
                        text="🎵",
                        font=("Roboto", 12),
                        width=20
                    )
                    music_label.pack(side="right", padx=(5, 0), pady=5)


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

    def _on_chapter_track_change(self, chapter_idx, choice):
        """Called when a per-chapter music track dropdown changes."""
        if not self.bg_music_tracks:
            return
        # Find which track index matches the chosen filename
        chosen_basename = choice
        for track_idx, track_path in enumerate(self.bg_music_tracks):
            if os.path.basename(track_path) == chosen_basename:
                self.bg_music_chapter_map[chapter_idx] = track_idx
                break

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

        # Include per-chapter music track mapping in manifest
        if (
            self.bg_music_enabled_var.get()
            and self.bg_music_mode_var.get() == "per_chapter"
            and self.bg_music_tracks
            and self.chapter_music_dropdown_vars
        ):
            for ch_idx, ch_data in enumerate(self.booksmith_data.chapters):
                if ch_idx < len(self.chapter_music_dropdown_vars) and ch_data.enabled:
                    chosen_basename = self.chapter_music_dropdown_vars[ch_idx].get()
                    for track_idx, track_path in enumerate(self.bg_music_tracks):
                        if os.path.basename(track_path) == chosen_basename:
                            self.bg_music_chapter_map[ch_idx] = track_idx
                            break
            self.log(f"Per-chapter music mapping: {len(self.bg_music_chapter_map)} chapters assigned")

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
