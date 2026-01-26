import PyInstaller.__main__
import customtkinter
import os
import sys

# locate customtkinter to include its assets
ctk_path = os.path.dirname(customtkinter.__file__)
print(f"CustomTkinter found at: {ctk_path}")

# locate whisper to include its assets (FIX for mel_filters.npz error)
import whisper
whisper_path = os.path.dirname(whisper.__file__)
print(f"Whisper found at: {whisper_path}")

# locate ffmpeg bundle
script_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_bundle_path = os.path.join(script_dir, 'ffmpeg_bundle')
if os.path.exists(ffmpeg_bundle_path):
    print(f"ffmpeg bundle found at: {ffmpeg_bundle_path}")
else:
    print("WARNING: ffmpeg_bundle not found!")

# Format for --add-data is "source;destination" on Windows
add_data_ctk = f"{ctk_path};customtkinter/"
add_data_whisper = f"{os.path.join(whisper_path, 'assets')};whisper/assets/"
add_data_ffmpeg = f"{ffmpeg_bundle_path};ffmpeg_bundle/"

# Define the build command arguments
args = [
    'app.py',                        # Main script
    '--name=Vox-1',                  # Name of the executable
    '--noconfirm',                   # Overwrite existing build
    '--onedir',                      # Generate a directory (faster startup than --onefile)
    '--windowed',                    # No console window (GUI only)
    '--clean',                       # Clean cache
    f'--add-data={add_data_ctk}',    # Include CTK assets
    f'--add-data={add_data_whisper}', # Include Whisper assets
    f'--add-data={add_data_ffmpeg}', # Include ffmpeg binaries
    
    # Hidden imports often missed by PyInstaller for these specific libs
    '--hidden-import=torch',
    '--hidden-import=torchaudio',
    '--hidden-import=whisper',
    '--hidden-import=soundfile',
    '--hidden-import=qwen_tts',
    '--collect-all=qwen_tts',  # Collect entire qwen_tts package
    '--hidden-import=sox',
    '--collect-all=sox',
    '--hidden-import=transformers',
    '--collect-all=transformers',
    '--hidden-import=accelerate',
    '--hidden-import=pydub',
    '--hidden-import=ebooklib',
    '--hidden-import=bs4',
    '--hidden-import=lxml',
    '--hidden-import=lxml.etree',
    '--hidden-import=cffi',
    '--hidden-import=PyPDF2',
    '--hidden-import=sklearn.utils._typedefs', # Common whisper/sklearn issue
    '--hidden-import=sklearn.neighbors._partition_nodes',
    '--hidden-import=librosa',
    '--hidden-import=numpy',
    '--hidden-import=scipy',
    '--hidden-import=safetensors',
    '--hidden-import=tokenizers',
    '--hidden-import=huggingface_hub',
    
    # Exclude heavy modules we definitely don't need to save space
    # '--exclude-module=tkinter',    # REMOVED: Required by customtkinter
    '--exclude-module=matplotlib',
    '--exclude-module=ipython',
    '--exclude-module=triton',        # Sage attention dependency (not used, breaks PyInstaller)
    '--exclude-module=sageattention',  # Not used (sdpa is default)
    '--exclude-module=flash_attn',     # Not compatible with Qwen3-TTS
]

print("Starting PyInstaller build...")
print(f"Command args: {args}")

PyInstaller.__main__.run(args)
