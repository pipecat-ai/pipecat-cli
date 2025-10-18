#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
SERVICE METADATA REGISTRY - SOURCE OF TRUTH

⭐ THIS IS THE SOURCE OF TRUTH FOR ALL PIPECAT SERVICES ⭐

To add a new service:
  1. Add a ServiceDefinition to the appropriate list below
  2. Run: uv run scripts/imports/update_imports.py
  3. Run: uv run scripts/configs/update_configs.py

DO NOT edit _configs.py or _imports.py directly - they are auto-generated from this file.

This module contains:
  - ServiceDefinition dataclass
  - Service lists (WEBRTC_TRANSPORTS, STT_SERVICES, LLM_SERVICES, etc.)
  - FEATURE_DEFINITIONS dict
  - MANUAL_SERVICE_CONFIGS for complex initialization

For operations on services, use ServiceLoader from service_loader.py.
"""

from dataclasses import dataclass
from typing import Literal

from ._configs import SERVICE_CONFIGS
from ._imports import BASE_IMPORTS, FEATURE_IMPORTS, IMPORTS

# Type aliases for service categorization
ServiceType = Literal["transport", "stt", "llm", "tts", "realtime"]
BotType = Literal["web", "telephony"]


@dataclass
class ServiceDefinition:
    """Service metadata definition.

    Required fields:
        value: Service identifier (e.g., "openai_llm")
        label: Human-readable name (e.g., "OpenAI")
        package: Python package requirement (e.g., "pipecat-ai[openai]")

    Optional fields:
        class_name: List of class names to import for this service
        env_prefix: Prefix for environment variables (e.g., "OPENAI" -> "OPENAI_API_KEY")
        include_params: Parameters to include in generated config even if they have defaults
        manual_config: If True, config must be manually written (not auto-generated)
        recommended: If True, this service is marked as recommended in prompts
    """

    value: str
    label: str
    package: str
    class_name: list[str] | None = None
    env_prefix: str | None = None
    include_params: list[str] | None = None
    manual_config: bool = False
    recommended: bool = False

    def __post_init__(self):
        """Validate service definition after initialization."""
        if not self.value:
            raise ValueError("Service must have a value")
        if not self.label:
            raise ValueError("Service must have a label")
        if not self.package:
            raise ValueError("Service must have a package")


# Feature definitions with metadata for auto-generation
# Maps feature names to the list of classes/functions that need to be imported
FEATURE_DEFINITIONS: dict[str, list[str]] = {
    "recording": ["AudioBufferProcessor"],
    "transcription": ["TranscriptProcessor"],
    "smart_turn": ["LocalSmartTurnAnalyzerV3", "SileroVADAnalyzer", "VADParams"],
    "vad": ["SileroVADAnalyzer"],
    "pipeline": ["Pipeline", "PipelineRunner", "PipelineParams", "PipelineTask"],
    "context": ["LLMContext", "LLMContextAggregatorPair"],
    "runner": [
        "load_dotenv",
        "LLMRunFrame",
        "RunnerArguments",
        "create_transport",
        "BaseTransport",
    ],
    "rtvi": ["RTVIConfig", "RTVIObserver", "RTVIProcessor"],
}


class ServiceRegistry:
    """
    Central registry for all Pipecat services and their configurations.

    This class contains only DATA - service definitions, import mappings,
    and feature configurations. All logic for querying and working with
    services has been moved to ServiceLoader for better separation of concerns.

    For operations like:
    - Finding services: use ServiceLoader.get_service_by_value()
    - Getting imports: use ServiceLoader.get_imports_for_services()
    - Extracting extras: use ServiceLoader.extract_extras_for_services()
    """

    # Service configs from separate module for better maintainability
    SERVICE_CONFIGS = SERVICE_CONFIGS

    # Auto-generated imports from separate module (DO NOT EDIT - regenerate with update_imports.py)
    IMPORTS = IMPORTS
    FEATURE_IMPORTS = FEATURE_IMPORTS
    BASE_IMPORTS = BASE_IMPORTS

    # Feature definitions (defined at module level for consistency)
    FEATURE_DEFINITIONS = FEATURE_DEFINITIONS

    # Web/Mobile Transports (WebRTC)
    WEBRTC_TRANSPORTS: list[ServiceDefinition] = [
        ServiceDefinition(
            value="daily",
            label="Daily (WebRTC)",
            package="pipecat-ai[daily]",
            class_name=["DailyParams"],
        ),
        ServiceDefinition(
            value="smallwebrtc",
            label="SmallWebRTC",
            package="pipecat-ai[webrtc]",
            class_name=["TransportParams"],
        ),
    ]

    # Telephony Transports
    TELEPHONY_TRANSPORTS: list[ServiceDefinition] = [
        ServiceDefinition(
            value="twilio",
            label="Twilio",
            package="pipecat-ai[websocket]",
            class_name=["FastAPIWebsocketParams"],
        ),
        ServiceDefinition(
            value="telnyx",
            label="Telnyx",
            package="pipecat-ai[websocket]",
            class_name=["FastAPIWebsocketParams"],
        ),
        ServiceDefinition(
            value="plivo",
            label="Plivo",
            package="pipecat-ai[websocket]",
            class_name=["FastAPIWebsocketParams"],
        ),
        ServiceDefinition(
            value="exotel",
            label="Exotel",
            package="pipecat-ai[websocket]",
            class_name=["FastAPIWebsocketParams"],
        ),
        # ServiceDefinition(
        #     value="daily_telephony",
        #     label="Daily",
        #     package="pipecat-ai[daily]",
        #     class_name=["DailyParams"],
        # ),
    ]

    # Speech-to-Text Services
    STT_SERVICES: list[ServiceDefinition] = [
        ServiceDefinition(
            value="assemblyai_stt",
            label="AssemblyAI",
            package="pipecat-ai[assemblyai]",
            class_name=["AssemblyAISTTService"],
            env_prefix="ASSEMBLYAI",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="aws_transcribe_stt",
            label="AWS Transcribe",
            package="pipecat-ai[aws]",
            class_name=["AWSTranscribeSTTService"],
            env_prefix="AWS",
            include_params=["aws_access_key_id", "aws_session_token", "region"],
        ),
        ServiceDefinition(
            value="azure_stt",
            label="Azure Speech",
            package="pipecat-ai[azure]",
            class_name=["AzureSTTService"],
            env_prefix="AZURE_SPEECH",
            include_params=["api_key", "region"],
        ),
        ServiceDefinition(
            value="cartesia_stt",
            label="Cartesia",
            package="pipecat-ai[cartesia]",
            class_name=["CartesiaSTTService"],
            env_prefix="CARTESIA",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="deepgram_stt",
            label="Deepgram",
            package="pipecat-ai[deepgram]",
            class_name=["DeepgramSTTService"],
            env_prefix="DEEPGRAM",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="deepgram_flux_stt",
            label="Deepgram Flux",
            package="pipecat-ai[deepgram]",
            class_name=["DeepgramFluxSTTService"],
            env_prefix="DEEPGRAM",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="elevenlabs_stt",
            label="ElevenLabs",
            package="pipecat-ai[elevenlabs]",
            class_name=["ElevenLabsSTTService"],
            env_prefix="ELEVENLABS",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="fal_stt",
            label="Fal (Wizper)",
            package="pipecat-ai[fal]",
            class_name=["FalSTTService"],
            env_prefix="FAL",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="gladia_stt",
            label="Gladia",
            package="pipecat-ai[gladia]",
            class_name=["GladiaSTTService"],
            env_prefix="GLADIA",
            include_params=["api_key", "region"],
        ),
        ServiceDefinition(
            value="google_stt",
            label="Google Speech-to-Text",
            package="pipecat-ai[google]",
            class_name=["GoogleSTTService"],
            env_prefix="GOOGLE",
            include_params=["credentials", "location"],
        ),
        ServiceDefinition(
            value="groq_stt",
            label="Groq (Whisper)",
            package="pipecat-ai[groq]",
            class_name=["GroqSTTService"],
            env_prefix="GROQ",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="nvidia_riva_stt",
            label="NVIDIA Riva",
            package="pipecat-ai[riva]",
            class_name=["RivaSTTService"],
            env_prefix="NVIDIA",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="openai_stt",
            label="OpenAI (Whisper)",
            package="pipecat-ai[openai]",
            class_name=["OpenAISTTService"],
            env_prefix="OPENAI",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="sambanova_stt",
            label="SambaNova (Whisper)",
            package="pipecat-ai[sambanova]",
            class_name=["SambaNovaSTTService"],
            env_prefix="SAMBANOVA",
            include_params=["model", "api_key"],
        ),
        ServiceDefinition(
            value="soniox_stt",
            label="Soniox",
            package="pipecat-ai[soniox]",
            class_name=["SonioxSTTService"],
            env_prefix="SONIOX",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="speechmatics_stt",
            label="Speechmatics",
            package="pipecat-ai[speechmatics]",
            class_name=["SpeechmaticsSTTService"],
            env_prefix="SPEECHMATICS",
            include_params=["api_key"],
        ),
        ServiceDefinition(
            value="ultravox_stt",
            label="Ultravox",
            package="pipecat-ai[ultravox]",
            class_name=["UltravoxSTTService"],
            env_prefix="ULTRAVOX",
            include_params=["model_name", "hf_token"],
            manual_config=True,
        ),
        ServiceDefinition(
            value="whisper_stt",
            label="Whisper (Local)",
            package="pipecat-ai[whisper]",
            class_name=["WhisperSTTService"],
            env_prefix="OPENAI",
            include_params=["model"],
        ),
    ]

    # Large Language Model Services
    LLM_SERVICES: list[ServiceDefinition] = [
        ServiceDefinition(
            value="anthropic_llm",
            label="Anthropic Claude",
            package="pipecat-ai[anthropic]",
            class_name=["AnthropicLLMService"],
            env_prefix="ANTHROPIC",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="aws_bedrock_llm",
            label="AWS Bedrock",
            package="pipecat-ai[aws]",
            class_name=["AWSBedrockLLMService"],
            env_prefix="AWS",
            include_params=["aws_region", "model"],
            manual_config=True,
        ),
        ServiceDefinition(
            value="azure_llm",
            label="Azure OpenAI",
            package="pipecat-ai[azure]",
            class_name=["AzureLLMService"],
            env_prefix="AZURE_CHATGPT",
            include_params=["api_key", "endpoint", "model"],
        ),
        ServiceDefinition(
            value="cerebras_llm",
            label="Cerebras",
            package="pipecat-ai[cerebras]",
            class_name=["CerebrasLLMService"],
            env_prefix="CEREBRAS",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="deepseek_llm",
            label="DeepSeek",
            package="pipecat-ai[deepseek]",
            class_name=["DeepSeekLLMService"],
            env_prefix="DEEPSEEK",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="fireworks_llm",
            label="Fireworks AI",
            package="pipecat-ai[fireworks]",
            class_name=["FireworksLLMService"],
            env_prefix="FIREWORKS",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="google_gemini_llm",
            label="Google Gemini",
            package="pipecat-ai[google]",
            class_name=["GoogleLLMService"],
            env_prefix="GOOGLE",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="google_vertex_llm",
            label="Google Vertex AI",
            package="pipecat-ai[google]",
            class_name=["GoogleVertexLLMService"],
            env_prefix="GOOGLE",
            include_params=["credentials", "location", "project_id"],
        ),
        ServiceDefinition(
            value="grok_llm",
            label="Grok",
            package="pipecat-ai[grok]",
            class_name=["GrokLLMService"],
            env_prefix="GROK",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="groq_llm",
            label="Groq",
            package="pipecat-ai[groq]",
            class_name=["GroqLLMService"],
            env_prefix="GROQ",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="mistral_llm",
            label="Mistral",
            package="pipecat-ai[mistral]",
            class_name=["MistralLLMService"],
            env_prefix="MISTRAL",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="nvidia_nim_llm",
            label="NVIDIA NIM",
            package="pipecat-ai[nim]",
            class_name=["NimLLMService"],
            env_prefix="NVIDIA",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="ollama_llm",
            label="Ollama",
            package="pipecat-ai[ollama]",
            class_name=["OLLamaLLMService"],
            env_prefix="OLLAMA",
            include_params=["model"],
        ),
        ServiceDefinition(
            value="openai_llm",
            label="OpenAI",
            package="pipecat-ai[openai]",
            class_name=["OpenAILLMService"],
            env_prefix="OPENAI",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="openpipe_llm",
            label="OpenPipe",
            package="pipecat-ai[openpipe]",
            class_name=["OpenPipeLLMService"],
            env_prefix="OPENPIPE",
            include_params=["api_key", "openpipe_api_key"],
        ),
        ServiceDefinition(
            value="openrouter_llm",
            label="OpenRouter",
            package="pipecat-ai[openrouter]",
            class_name=["OpenRouterLLMService"],
            env_prefix="OPENROUTER",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="perplexity_llm",
            label="Perplexity",
            package="pipecat-ai[perplexity]",
            class_name=["PerplexityLLMService"],
            env_prefix="PERPLEXITY",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="qwen_llm",
            label="Qwen",
            package="pipecat-ai[qwen]",
            class_name=["QwenLLMService"],
            env_prefix="QWEN",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="sambanova_llm",
            label="SambaNova",
            package="pipecat-ai[sambanova]",
            class_name=["SambaNovaLLMService"],
            env_prefix="SAMBANOVA",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="together_llm",
            label="Together AI",
            package="pipecat-ai[together]",
            class_name=["TogetherLLMService"],
            env_prefix="TOGETHER",
            include_params=["api_key", "model"],
        ),
    ]

    # Text-to-Speech Services
    TTS_SERVICES: list[ServiceDefinition] = [
        ServiceDefinition(
            value="asyncai_tts",
            label="Async",
            package="pipecat-ai[asyncai]",
            class_name=["AsyncAITTSService"],
            env_prefix="ASYNCAI",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="aws_polly_tts",
            label="AWS Polly",
            package="pipecat-ai[aws]",
            class_name=["AWSPollyTTSService"],
            env_prefix="AWS",
            include_params=["region", "voice_id"],
            manual_config=True,
        ),
        ServiceDefinition(
            value="azure_tts",
            label="Azure TTS",
            package="pipecat-ai[azure]",
            class_name=["AzureTTSService"],
            env_prefix="AZURE_SPEECH",
            include_params=["api_key", "region", "voice"],
        ),
        ServiceDefinition(
            value="cartesia_tts",
            label="Cartesia",
            package="pipecat-ai[cartesia]",
            class_name=["CartesiaTTSService"],
            env_prefix="CARTESIA",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="deepgram_tts",
            label="Deepgram",
            package="pipecat-ai[deepgram]",
            class_name=["DeepgramTTSService"],
            env_prefix="DEEPGRAM",
            include_params=["api_key", "voice"],
        ),
        ServiceDefinition(
            value="elevenlabs_tts",
            label="ElevenLabs",
            package="pipecat-ai[elevenlabs]",
            class_name=["ElevenLabsTTSService"],
            env_prefix="ELEVENLABS",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="fish_tts",
            label="Fish",
            package="pipecat-ai[fish]",
            class_name=["FishAudioTTSService"],
            env_prefix="FISH",
            include_params=["api_key", "model"],
        ),
        ServiceDefinition(
            value="google_tts",
            label="Google TTS",
            package="pipecat-ai[google]",
            class_name=["GoogleTTSService"],
            env_prefix="GOOGLE",
            include_params=["voice_id", "credentials"],
        ),
        ServiceDefinition(
            value="groq_tts",
            label="Groq TTS",
            package="pipecat-ai[groq]",
            class_name=["GroqTTSService"],
            env_prefix="GROQ",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="hume_tts",
            label="Hume TTS",
            package="pipecat-ai[hume]",
            class_name=["HumeTTSService"],
            env_prefix="HUME",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="inworld_tts",
            label="Inworld",
            package="pipecat-ai",
            class_name=["InworldTTSService"],
            env_prefix="INWORLD",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="lmnt_tts",
            label="LMNT",
            package="pipecat-ai[lmnt]",
            class_name=["LmntTTSService"],
            env_prefix="LMNT",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="minimax_tts",
            label="MiniMax",
            package="pipecat-ai",
            class_name=["MiniMaxHttpTTSService"],
            env_prefix="MINIMAX",
            include_params=["api_key", "group_id", "voice_id"],
        ),
        ServiceDefinition(
            value="neuphonic_tts",
            label="Neuphonic",
            package="pipecat-ai[neuphonic]",
            class_name=["NeuphonicTTSService"],
            env_prefix="NEUPHONIC",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="nvidia_riva_tts",
            label="NVIDIA Riva",
            package="pipecat-ai[riva]",
            class_name=["RivaTTSService"],
            env_prefix="NVIDIA",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="openai_tts",
            label="OpenAI TTS",
            package="pipecat-ai[openai]",
            class_name=["OpenAITTSService"],
            env_prefix="OPENAI",
            include_params=["api_key", "voice"],
        ),
        ServiceDefinition(
            value="piper_tts",
            label="Piper",
            package="pipecat-ai",
            class_name=["PiperTTSService"],
            env_prefix="PIPER",
            include_params=["base_url"],
        ),
        ServiceDefinition(
            value="rime_tts",
            label="Rime",
            package="pipecat-ai[rime]",
            class_name=["RimeTTSService"],
            env_prefix="RIME",
            include_params=["api_key", "voice_id"],
        ),
        ServiceDefinition(
            value="sarvam_tts",
            label="Sarvam",
            package="pipecat-ai",
            class_name=["SarvamTTSService"],
            env_prefix="SARVAM",
            include_params=["api_key", "model", "voice_id"],
        ),
        ServiceDefinition(
            value="xtts_tts",
            label="XTTS (Coqui)",
            package="pipecat-ai[xtts]",
            class_name=["XTTSService"],
            env_prefix="XTTS",
            include_params=["voice_id", "base_url"],
        ),
    ]

    # Realtime (Speech-to-Speech) Services
    REALTIME_SERVICES: list[ServiceDefinition] = [
        ServiceDefinition(
            value="aws_nova_realtime",
            label="AWS Nova Sonic",
            package="pipecat-ai[aws]",
            class_name=["AWSNovaSonicLLMService"],
            env_prefix="AWS",
            include_params=[],
            manual_config=True,
        ),
        ServiceDefinition(
            value="azure_realtime",
            label="Azure Realtime",
            package="pipecat-ai[azure]",
            class_name=[
                "AzureRealtimeLLMService",
                "SessionProperties",
                "InputAudioTranscription",
            ],
            env_prefix="AZURE",
            include_params=[],
            manual_config=True,
        ),
        ServiceDefinition(
            value="gemini_live_realtime",
            label="Gemini Live",
            package="pipecat-ai[google]",
            class_name=["GeminiLiveLLMService"],
            env_prefix="GOOGLE",
            include_params=[],
            manual_config=True,
        ),
        ServiceDefinition(
            value="gemini_vertex_live_realtime",
            label="Gemini Vertex Live",
            package="pipecat-ai[google]",
            class_name=["GeminiLiveVertexLLMService"],
            env_prefix="GOOGLE_VERTEX",
            include_params=[],
            manual_config=True,
        ),
        ServiceDefinition(
            value="openai_realtime",
            label="OpenAI Realtime",
            package="pipecat-ai[openai]",
            class_name=[
                "OpenAIRealtimeLLMService",
                "SessionProperties",
                "AudioConfiguration",
                "AudioInput",
                "InputAudioTranscription",
                "SemanticTurnDetection",
                "InputAudioNoiseReduction",
            ],
            env_prefix="OPENAI",
            include_params=[],
            manual_config=True,
        ),
    ]


# Manual service configurations for services that require custom initialization
# These services have complex initialization logic that cannot be auto-generated
# (e.g., nested InputParams, SessionProperties, or other special requirements)
MANUAL_SERVICE_CONFIGS = {
    "ultravox_stt": (
        "UltravoxSTTService(\n"
        '        model_name=os.getenv("ULTRAVOX_MODEL_NAME"),\n'
        '        hf_token=os.getenv("HF_TOKEN"),\n'
        '        region=os.getenv("ULTRAVOX_REGION")\n'
        "    )"
    ),
    "aws_bedrock_llm": (
        "AWSBedrockLLMService(\n"
        '        aws_region=os.getenv("AWS_REGION"),\n'
        '        model=os.getenv("AWS_BEDROCK_MODEL"),\n'
        '        params=AWSBedrockLLMService.InputParams(temperature=0.8, latency="optimized")\n'
        "    )"
    ),
    "aws_polly_tts": (
        "AWSPollyTTSService(\n"
        '        region=os.getenv("AWS_REGION"),\n'
        '        voice_id=os.getenv("AWS_VOICE_ID"),\n'
        '        params=AWSPollyTTSService.InputParams(engine="generative"),\n'
        "    )"
    ),
    "azure_realtime": (
        "session_properties = SessionProperties(\n"
        '        input_audio_transcription=InputAudioTranscription(model="whisper-1"),\n'
        '        instructions=os.getenv("AZURE_INSTRUCTIONS"),\n'
        "    )\n"
        "\n"
        "    llm = AzureRealtimeLLMService(\n"
        '        api_key=os.getenv("AZURE_REALTIME_API_KEY"),\n'
        '        base_url=os.getenv("AZURE_REALTIME_BASE_URL"),\n'
        "        session_properties=session_properties,\n"
        "        start_audio_paused=False,\n"
        "    )"
    ),
    "openai_realtime": (
        "session_properties = SessionProperties(\n"
        "        audio=AudioConfiguration(\n"
        "            input=AudioInput(\n"
        "                transcription=InputAudioTranscription(),\n"
        "                turn_detection=SemanticTurnDetection(),\n"
        '                noise_reduction=InputAudioNoiseReduction(type="near_field"),\n'
        "            )\n"
        "        ),\n"
        '        instructions=os.getenv("OPENAI_INSTRUCTIONS"),\n'
        "    )\n"
        "\n"
        "    llm = OpenAIRealtimeLLMService(\n"
        '        api_key=os.getenv("OPENAI_API_KEY"),\n'
        "        session_properties=session_properties,\n"
        "        start_audio_paused=False,\n"
        "    )"
    ),
    "gemini_live_realtime": (
        "llm = GeminiLiveLLMService(\n"
        '        api_key=os.getenv("GOOGLE_API_KEY"),\n'
        '        model=os.getenv("GOOGLE_MODEL"),\n'
        '        voice_id=os.getenv("GOOGLE_VOICE_ID"),\n'
        '        system_instruction=os.getenv("GOOGLE_SYSTEM_INSTRUCTION"),\n'
        "    )"
    ),
    "gemini_vertex_live_realtime": (
        "llm = GeminiLiveVertexLLMService(\n"
        '        credentials=os.getenv("GOOGLE_VERTEX_TEST_CREDENTIALS"),\n'
        '        project_id=os.getenv("GOOGLE_CLOUD_PROJECT_ID"),\n'
        '        location=os.getenv("GOOGLE_CLOUD_LOCATION"),\n'
        '        voice_id=os.getenv("GOOGLE_VOICE_ID"),\n'
        '        system_instruction=os.getenv("GOOGLE_SYSTEM_INSTRUCTION"),\n'
        "    )"
    ),
    "aws_nova_realtime": (
        "llm = AWSNovaSonicLLMService(\n"
        '        secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),\n'
        '        access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),\n'
        '        region=os.getenv("AWS_REGION"),\n'
        '        session_token=os.getenv("AWS_SESSION_TOKEN"),\n'
        '        voice_id=os.getenv("AWS_VOICE_ID"),\n'
        "    )"
    ),
}
