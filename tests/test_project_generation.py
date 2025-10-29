"""Integration tests for project generation with different configurations."""

import ast
import shutil
import subprocess

import pytest

from pipecat_cli.generators.project import ProjectGenerator
from pipecat_cli.prompts.questions import ProjectConfig


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test projects."""
    output_dir = tmp_path / "test_projects"
    output_dir.mkdir()
    yield output_dir
    # Cleanup happens automatically with tmp_path

    # For debugging: Uncomment these lines to preserve test files
    # from pathlib import Path
    # output_dir = Path("/tmp/pipecat-cli-test-projects")
    # output_dir.mkdir(parents=True, exist_ok=True)
    # print(f"\n✅ Test files preserved at: {output_dir}")
    # return  # Skip cleanup


def validate_python_syntax(file_path):
    """Validate that a Python file has valid syntax."""
    with open(file_path) as f:
        code = f.read()
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def validate_pyproject_toml(file_path):
    """Validate that pyproject.toml is valid TOML and has required fields."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # Fallback for older Python

    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    # Check required fields
    assert "project" in data, "pyproject.toml must have [project] section"
    assert "name" in data["project"], "project.name is required"
    assert "dependencies" in data["project"], "project.dependencies is required"
    assert len(data["project"]["dependencies"]) > 0, "Must have at least one dependency"

    # Check for pipecat-ai dependency
    has_pipecat = any("pipecat-ai" in dep for dep in data["project"]["dependencies"])
    assert has_pipecat, "Must include pipecat-ai dependency"

    return True


def validate_project_installable(project_path):
    """Validate that the project can be installed with uv."""
    # pyproject.toml is now in server/ subdirectory
    server_path = project_path / "server"
    result = subprocess.run(
        ["uv", "pip", "compile", str(server_path / "pyproject.toml")],
        capture_output=True,
        text=True,
        cwd=server_path,
    )
    return result.returncode == 0, result.stderr


def validate_imports_resolvable(bot_file_path):
    """Check that all imports in bot.py could theoretically resolve."""
    with open(bot_file_path) as f:
        tree = ast.parse(f.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    # Check that we have the expected Pipecat imports
    has_pipecat = any("pipecat" in imp for imp in imports)
    assert has_pipecat, "bot.py should import from pipecat"

    return True, imports


# Test configurations for different transport types
TEST_CONFIGS = [
    # WebRTC Transports - Cascade
    {
        "name": "daily-cascade",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
    },
    {
        "name": "smallwebrtc-cascade",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "cascade",
        "stt_service": "assemblyai_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
    },
    # Telephony Transports - Cascade
    {
        "name": "twilio-cascade",
        "bot_type": "telephony",
        "transports": ["twilio"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
    },
    {
        "name": "telnyx-cascade",
        "bot_type": "telephony",
        "transports": ["telnyx"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
    },
    # Realtime Pipelines
    {
        "name": "daily-realtime",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "realtime",
        "realtime_service": "openai_realtime",
    },
    {
        "name": "smallwebrtc-realtime",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "realtime",
        "realtime_service": "gemini_live_realtime",
    },
    # Mixed Transports (Telephony + WebRTC)
    {
        "name": "twilio-webrtc-mixed",
        "bot_type": "telephony",
        "transports": ["twilio", "smallwebrtc"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
    },
    # With features
    {
        "name": "daily-with-features",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "video_input": True,
        "video_output": True,
        "recording": True,
        "transcription": True,
        "smart_turn": True,
        "deploy_to_cloud": True,
        "enable_krisp": True,
    },
    # With observability
    {
        "name": "daily-with-observability",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "enable_observability": True,
    },
    # More telephony providers
    {
        "name": "plivo-cascade",
        "bot_type": "telephony",
        "transports": ["plivo"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "anthropic_llm",
        "tts_service": "elevenlabs_tts",
    },
    {
        "name": "exotel-cascade",
        "bot_type": "telephony",
        "transports": ["exotel"],
        "mode": "cascade",
        "stt_service": "assemblyai_stt",
        "llm_service": "groq_llm",
        "tts_service": "playht_tts",
    },
    # More realtime services
    {
        "name": "azure-realtime",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "realtime",
        "realtime_service": "azure_realtime",
    },
    {
        "name": "aws-nova-realtime",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "realtime",
        "realtime_service": "aws_nova_realtime",
    },
    # Different service combinations for cascade
    {
        "name": "google-vertex-stack",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "google_stt",
        "llm_service": "google_vertex_llm",
        "tts_service": "google_tts",
    },
    {
        "name": "azure-stack",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "azure_stt",
        "llm_service": "azure_llm",
        "tts_service": "azure_tts",
    },
    {
        "name": "aws-stack",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "cascade",
        "stt_service": "aws_transcribe_stt",
        "llm_service": "aws_bedrock_llm",
        "tts_service": "aws_polly_tts",
    },
    # Recording and transcription features
    {
        "name": "daily-recording",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "recording": True,
    },
    {
        "name": "daily-transcription",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "elevenlabs_tts",
        "transcription": True,
    },
    # Cloud deployment variations
    {
        "name": "twilio-cloud-no-krisp",
        "bot_type": "telephony",
        "transports": ["twilio"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "deploy_to_cloud": True,
        "enable_krisp": False,
    },
    {
        "name": "smallwebrtc-cloud-with-video",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "video_input": True,
        "video_output": True,
        "deploy_to_cloud": True,
    },
    # Video combinations
    {
        "name": "daily-video-input-only",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "anthropic_llm",
        "tts_service": "cartesia_tts",
        "video_input": True,
        "video_output": False,
    },
    {
        "name": "smallwebrtc-video-output-only",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "elevenlabs_tts",
        "video_input": False,
        "video_output": True,
    },
    # Multiple transports with different features
    {
        "name": "daily-smallwebrtc-multi",
        "bot_type": "web",
        "transports": ["daily", "smallwebrtc"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "smart_turn": True,
    },
    {
        "name": "telnyx-daily-mixed-cloud",
        "bot_type": "telephony",
        "transports": ["telnyx", "daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "deploy_to_cloud": True,
        "enable_krisp": True,
    },
    # Video avatar services
    {
        "name": "daily-tavus-video",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "video_service": "tavus_video",
        "video_output": True,
    },
    {
        "name": "smallwebrtc-heygen-video",
        "bot_type": "web",
        "transports": ["smallwebrtc"],
        "mode": "cascade",
        "stt_service": "assemblyai_stt",
        "llm_service": "anthropic_llm",
        "tts_service": "elevenlabs_tts",
        "video_service": "heygen_video",
        "video_output": True,
    },
    {
        "name": "daily-simli-video",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "video_service": "simli_video",
        "video_output": True,
        "smart_turn": True,
    },
    {
        "name": "daily-tavus-video-cloud",
        "bot_type": "web",
        "transports": ["daily"],
        "mode": "cascade",
        "stt_service": "deepgram_stt",
        "llm_service": "openai_llm",
        "tts_service": "cartesia_tts",
        "video_service": "tavus_video",
        "video_output": True,
        "deploy_to_cloud": True,
        "enable_krisp": True,
    },
]


@pytest.mark.parametrize("config_data", TEST_CONFIGS, ids=lambda c: c["name"])
def test_project_generation(config_data, temp_output_dir):
    """Test that projects generate successfully with different configurations."""
    # Create config with defaults for optional fields
    config = ProjectConfig(
        project_name=config_data["name"],
        bot_type=config_data["bot_type"],
        transports=config_data["transports"],
        mode=config_data["mode"],
        stt_service=config_data.get("stt_service"),
        llm_service=config_data.get("llm_service"),
        tts_service=config_data.get("tts_service"),
        realtime_service=config_data.get("realtime_service"),
        video_service=config_data.get("video_service"),
        video_input=config_data.get("video_input", False),
        video_output=config_data.get("video_output", False),
        recording=config_data.get("recording", False),
        transcription=config_data.get("transcription", False),
        smart_turn=config_data.get("smart_turn", False),
        deploy_to_cloud=config_data.get("deploy_to_cloud", False),
        enable_krisp=config_data.get("enable_krisp", False),
        enable_observability=config_data.get("enable_observability", False),
    )

    # Generate project
    generator = ProjectGenerator(config)

    # Ensure clean output directory
    project_path = temp_output_dir / config.project_name
    if project_path.exists():
        shutil.rmtree(project_path)

    # Generate into temp directory
    generator.generate(output_dir=temp_output_dir)

    # Verify core files exist (in monorepo structure)
    assert (project_path / "server" / "bot.py").exists(), "server/bot.py should exist"
    assert (project_path / "server" / "pyproject.toml").exists(), "server/pyproject.toml should exist"
    assert (project_path / "server" / ".env.example").exists(), "server/.env.example should exist"
    assert (project_path / ".gitignore").exists(), ".gitignore should exist"
    assert (project_path / "README.md").exists(), "README.md should exist"

    # Verify cloud deployment files
    if config.deploy_to_cloud:
        assert (project_path / "server" / "Dockerfile").exists(), (
            "server/Dockerfile should exist for cloud deployment"
        )
        assert (project_path / "server" / "pcc-deploy.toml").exists(), (
            "server/pcc-deploy.toml should exist for cloud deployment"
        )

    # Validate Python syntax
    bot_file = project_path / "server" / "bot.py"
    is_valid, error = validate_python_syntax(bot_file)
    assert is_valid, f"bot.py has syntax errors: {error}"

    # Validate imports are resolvable
    is_valid, imports = validate_imports_resolvable(bot_file)
    assert is_valid, "bot.py should have valid Pipecat imports"

    # Verify bot.py structure
    bot_content = bot_file.read_text()
    assert "async def run_bot" in bot_content, "bot.py should have run_bot function"
    assert "async def bot" in bot_content, "bot.py should have bot function"

    # Verify imports are present
    if config.mode == "cascade":
        if config.stt_service:
            assert "STT" in bot_content or "stt" in bot_content, "STT should be referenced"
        if config.llm_service:
            assert "LLM" in bot_content or "llm" in bot_content, "LLM should be referenced"
        if config.tts_service:
            assert "TTS" in bot_content or "tts" in bot_content, "TTS should be referenced"
    elif config.mode == "realtime":
        assert "llm" in bot_content, "Realtime LLM should be referenced"

    # Verify transport-specific code
    for transport in config.transports:
        if transport == "daily":
            assert "DailyParams" in bot_content or "daily" in bot_content.lower()
        elif transport == "smallwebrtc":
            assert "TransportParams" in bot_content or "webrtc" in bot_content.lower()
        elif transport in ["twilio", "telnyx", "plivo", "exotel"]:
            assert "FastAPIWebsocketParams" in bot_content, (
                f"{transport} should use FastAPIWebsocketParams"
            )

    # Validate pyproject.toml syntax and structure
    pyproject_file = project_path / "server" / "pyproject.toml"
    validate_pyproject_toml(pyproject_file)

    # Verify pyproject.toml has correct dependencies
    pyproject_content = pyproject_file.read_text()
    assert "pipecat-ai[" in pyproject_content, "pyproject.toml should have pipecat-ai dependencies"

    # Verify transport extras
    for transport in config.transports:
        if transport == "daily":
            assert "daily" in pyproject_content
        elif transport == "smallwebrtc":
            assert "webrtc" in pyproject_content

    # Verify cloud deployment extras
    if config.deploy_to_cloud:
        assert "pipecatcloud" in pyproject_content

    # Verify observability dependencies
    if config.enable_observability:
        assert "pipecat-ai-whisker" in pyproject_content
        assert "pipecat-ai-tail" in pyproject_content
        # Verify observability imports in bot.py
        assert "WhiskerObserver" in bot_content
        assert "TailObserver" in bot_content
        assert "from pipecat_whisker import WhiskerObserver" in bot_content
        assert "from pipecat_tail.observer import TailObserver" in bot_content

    # Verify video service dependencies and imports
    if config.video_service:
        # Video services should be in bot.py
        if config.video_service == "tavus_video":
            assert "TavusVideoService" in bot_content, "TavusVideoService should be imported"
            assert "tavus" in pyproject_content, "tavus extra should be in dependencies"
        elif config.video_service == "heygen_video":
            assert "HeyGenVideoService" in bot_content, "HeyGenVideoService should be imported"
            assert "heygen" in pyproject_content, "heygen extra should be in dependencies"
            assert "NewSessionRequest" in bot_content, "NewSessionRequest should be imported for HeyGen"
            assert "AvatarQuality" in bot_content, "AvatarQuality should be imported for HeyGen"
        elif config.video_service == "simli_video":
            assert "SimliVideoService" in bot_content, "SimliVideoService should be imported"
            assert "simli" in pyproject_content, "simli extra should be in dependencies"
        
        # Video service should be initialized in bot.py
        assert "video" in bot_content.lower(), "video service variable should be present"


@pytest.mark.slow
@pytest.mark.parametrize(
    "config_data",
    [
        # Just test a few representative configs for dependency resolution
        TEST_CONFIGS[0],  # daily-cascade
        TEST_CONFIGS[5],  # daily-realtime
        TEST_CONFIGS[8],  # daily-with-features
    ],
    ids=lambda c: f"{c['name']}-installable",
)
def test_project_installable(config_data, temp_output_dir):
    """Test that projects have resolvable dependencies (slow test)."""
    # Create config
    config = ProjectConfig(
        project_name=config_data["name"],
        bot_type=config_data["bot_type"],
        transports=config_data["transports"],
        mode=config_data["mode"],
        stt_service=config_data.get("stt_service"),
        llm_service=config_data.get("llm_service"),
        tts_service=config_data.get("tts_service"),
        realtime_service=config_data.get("realtime_service"),
        video_service=config_data.get("video_service"),
        video_input=config_data.get("video_input", False),
        video_output=config_data.get("video_output", False),
        recording=config_data.get("recording", False),
        transcription=config_data.get("transcription", False),
        smart_turn=config_data.get("smart_turn", False),
        deploy_to_cloud=config_data.get("deploy_to_cloud", False),
        enable_krisp=config_data.get("enable_krisp", False),
        enable_observability=config_data.get("enable_observability", False),
    )

    # Generate project
    generator = ProjectGenerator(config)

    # Ensure clean output directory
    project_path = temp_output_dir / config.project_name
    if project_path.exists():
        shutil.rmtree(project_path)

    # Generate into temp directory
    generator.generate(output_dir=temp_output_dir)

    # Test that dependencies can be resolved
    is_installable, error = validate_project_installable(project_path)
    assert is_installable, f"Project dependencies cannot be resolved: {error}"


def test_project_name_conflict(temp_output_dir):
    """Test that project generation handles name conflicts."""
    config = ProjectConfig(
        project_name="test-project",
        bot_type="web",
        transports=["daily"],
        mode="cascade",
        stt_service="deepgram_stt",
        llm_service="openai_llm",
        tts_service="cartesia_tts",
    )

    generator = ProjectGenerator(config)
    project_path = temp_output_dir / config.project_name

    # Generate first project
    generator.generate(output_dir=temp_output_dir)
    assert project_path.exists()
    assert (project_path / "server" / "bot.py").exists()

    # Note: The CLI prompts for a new name on conflict, but we can't test
    # that interactively here. This test just verifies the first generation works.


def test_invalid_service_combination():
    """Test that invalid service combinations are caught."""
    # This test would check validation logic if we add it
    # For now, we rely on the interactive prompts to guide users
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
