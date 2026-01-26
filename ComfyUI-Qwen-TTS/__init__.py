# ComfyUI-Qwen-TTS Custom Nodes
# Based on the open-source Qwen3-TTS project by Alibaba Qwen team

import os
import sys
import torch

# Add current directory to path for qwen_tts package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import nodes
from .nodes import (
    VoiceDesignNode,
    VoiceCloneNode,
    CustomVoiceNode,
    VoiceClonePromptNode,
    RoleBankNode,
    DialogueInferenceNode,
)

# Node mappings
NODE_CLASS_MAPPINGS = {
    "FB_Qwen3TTSVoiceClone": VoiceCloneNode,
    "FB_Qwen3TTSVoiceDesign": VoiceDesignNode,
    "FB_Qwen3TTSCustomVoice": CustomVoiceNode,
    "FB_Qwen3TTSVoiceClonePrompt": VoiceClonePromptNode,
    "FB_Qwen3TTSRoleBank": RoleBankNode,
    "FB_Qwen3TTSDialogueInference": DialogueInferenceNode,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "FB_Qwen3TTSVoiceClone": "🎭 Qwen3-TTS VoiceClone",
    "FB_Qwen3TTSVoiceDesign": "🎨 Qwen3-TTS VoiceDesign",
    "FB_Qwen3TTSCustomVoice": "🎵 Qwen3-TTS CustomVoice",
    "FB_Qwen3TTSVoiceClonePrompt": "🎭 Qwen3-TTS VoiceClonePrompt",
    "FB_Qwen3TTSRoleBank": "📇 Qwen3-TTS RoleBank",
    "FB_Qwen3TTSDialogueInference": "💬 Qwen3-TTS DialogueInference",
}

# Version information
__version__ = "1.0.1"

print(f"✅ ComfyUI-Qwen-TTS v{__version__} loaded")
