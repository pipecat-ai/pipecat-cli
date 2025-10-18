"""Tests for service registry integrity and completeness."""

import pytest

from pipecat_cli.registry import ServiceLoader, ServiceRegistry


class TestServiceRegistryIntegrity:
    """Test that the service registry is complete and consistent."""

    def test_all_services_have_configs(self):
        """Verify all services have corresponding configs."""
        missing = ServiceLoader.get_missing_services()

        if missing["missing_configs"]:
            pytest.fail(
                f"Services missing configs: {', '.join(missing['missing_configs'])}\n"
                f"Add these services to src/pipecat_cli/registry/_configs.py"
            )

    def test_all_services_have_imports(self):
        """Verify all services have corresponding import statements."""
        missing = ServiceLoader.get_missing_services()

        if missing["missing_imports"]:
            pytest.fail(
                f"Services missing imports: {', '.join(missing['missing_imports'])}\n"
                f"Add these services to ServiceRegistry.IMPORTS in services.py"
            )

    def test_service_definitions_are_valid(self):
        """Verify all service definitions have required fields.
        
        This test validates that all services were created successfully
        (which means they passed __post_init__ validation).
        """
        all_services = []
        all_services.extend(ServiceRegistry.WEBRTC_TRANSPORTS)
        all_services.extend(ServiceRegistry.TELEPHONY_TRANSPORTS)
        all_services.extend(ServiceRegistry.STT_SERVICES)
        all_services.extend(ServiceRegistry.LLM_SERVICES)
        all_services.extend(ServiceRegistry.TTS_SERVICES)
        all_services.extend(ServiceRegistry.REALTIME_SERVICES)

        # Verify all services have required fields
        for service in all_services:
            assert service.value, f"Service missing value"
            assert service.label, f"Service {service.value} missing label"
            assert service.package, f"Service {service.value} missing package"

    def test_no_duplicate_service_values(self):
        """Verify no duplicate service values exist."""
        all_services = []
        all_services.extend(ServiceRegistry.WEBRTC_TRANSPORTS)
        all_services.extend(ServiceRegistry.TELEPHONY_TRANSPORTS)
        all_services.extend(ServiceRegistry.STT_SERVICES)
        all_services.extend(ServiceRegistry.LLM_SERVICES)
        all_services.extend(ServiceRegistry.TTS_SERVICES)
        all_services.extend(ServiceRegistry.REALTIME_SERVICES)

        values = [s.value for s in all_services]
        duplicates = [v for v in values if values.count(v) > 1]

        if duplicates:
            pytest.fail(f"Duplicate service values found: {', '.join(set(duplicates))}")

    def test_package_extras_are_extractable(self):
        """Verify all service packages can have their extras extracted."""
        from pipecat_cli.registry import extract_package_extra

        all_services = []
        all_services.extend(ServiceRegistry.STT_SERVICES)
        all_services.extend(ServiceRegistry.LLM_SERVICES)
        all_services.extend(ServiceRegistry.TTS_SERVICES)
        all_services.extend(ServiceRegistry.REALTIME_SERVICES)

        for service in all_services:
            package = service.package
            # Should not raise an exception
            extra = extract_package_extra(package)
            # If package has brackets, extra should be extracted
            if "[" in package:
                assert extra is not None, f"Failed to extract extra from {package}"


class TestServiceLoader:
    """Test ServiceLoader functionality."""

    def test_get_service_by_value(self):
        """Test finding a service by value."""
        service = ServiceLoader.get_service_by_value(ServiceRegistry.STT_SERVICES, "deepgram_stt")
        assert service is not None
        assert service.value == "deepgram_stt"
        assert service.label == "Deepgram"

    def test_get_service_by_value_not_found(self):
        """Test finding a non-existent service."""
        service = ServiceLoader.get_service_by_value(
            ServiceRegistry.STT_SERVICES, "nonexistent_service"
        )
        assert service is None

    def test_get_service_config(self):
        """Test retrieving service configuration."""
        config = ServiceLoader.get_service_config("deepgram_stt")
        assert config is not None
        assert "DeepgramSTTService" in config
        assert "DEEPGRAM_API_KEY" in config

    def test_get_service_import(self):
        """Test retrieving service imports."""
        imports = ServiceLoader.get_service_import("deepgram_stt")
        assert imports is not None
        assert len(imports) > 0
        assert any("DeepgramSTTService" in imp for imp in imports)

    @pytest.mark.parametrize(
        "service",
        ServiceRegistry.STT_SERVICES
        + ServiceRegistry.LLM_SERVICES
        + ServiceRegistry.TTS_SERVICES
        + ServiceRegistry.REALTIME_SERVICES,
        ids=lambda s: s.value,
    )
    def test_every_service_has_config(self, service):
        """Test that every single service has a valid config."""
        service_value = service.value
        config = ServiceLoader.get_service_config(service_value)

        assert config is not None, f"Service {service_value} missing config in _configs.py"
        assert len(config.strip()) > 0, f"Service {service_value} has empty config"
        # Config should contain the service class name (e.g., "DeepgramSTTService")
        assert (
            "Service" in config or "LLM" in config
        ), f"Service {service_value} config doesn't look like valid service initialization code"

    @pytest.mark.parametrize(
        "service",
        ServiceRegistry.STT_SERVICES
        + ServiceRegistry.LLM_SERVICES
        + ServiceRegistry.TTS_SERVICES
        + ServiceRegistry.REALTIME_SERVICES,
        ids=lambda s: s.value,
    )
    def test_every_service_has_imports(self, service):
        """Test that every single service has import statements."""
        service_value = service.value
        imports = ServiceLoader.get_service_import(service_value)

        assert (
            imports is not None
        ), f"Service {service_value} missing imports in ServiceRegistry.IMPORTS"
        assert len(imports) > 0, f"Service {service_value} has empty imports list"
        # At least one import should reference pipecat
        assert any(
            "pipecat" in imp for imp in imports
        ), f"Service {service_value} imports don't reference pipecat"

    @pytest.mark.parametrize(
        "transport",
        ServiceRegistry.WEBRTC_TRANSPORTS + ServiceRegistry.TELEPHONY_TRANSPORTS,
        ids=lambda t: t.value,
    )
    def test_every_transport_has_imports(self, transport):
        """Test that every transport has import statements."""
        transport_value = transport.value
        imports = ServiceLoader.get_service_import(transport_value)

        assert (
            imports is not None
        ), f"Transport {transport_value} missing imports in ServiceRegistry.IMPORTS"
        assert len(imports) > 0, f"Transport {transport_value} has empty imports list"
        # Transport imports should reference pipecat
        assert any(
            "pipecat" in imp for imp in imports
        ), f"Transport {transport_value} imports don't reference pipecat"

    @pytest.mark.parametrize(
        "service",
        ServiceRegistry.STT_SERVICES
        + ServiceRegistry.LLM_SERVICES
        + ServiceRegistry.TTS_SERVICES
        + ServiceRegistry.REALTIME_SERVICES,
        ids=lambda s: s.value,
    )
    def test_every_service_package_is_extractable(self, service):
        """Test that every service's package extra can be extracted."""
        from pipecat_cli.registry import extract_package_extra

        service_value = service.value
        package = service.package

        # Should not raise an exception
        extra = extract_package_extra(package)

        # Package should have correct format
        assert package.startswith(
            "pipecat-ai"
        ), f"Service {service_value} package should start with 'pipecat-ai', got: {package}"

        # If package has brackets, extra should be extracted
        if "[" in package:
            assert (
                extra is not None
            ), f"Failed to extract extra from {service_value} package: {package}"
            assert len(extra) > 0, f"Empty extra extracted from {service_value} package: {package}"

    def test_extract_extras_for_cascade(self):
        """Test extracting extras for a cascade pipeline."""
        services = {
            "transports": ["daily"],
            "stt": "deepgram_stt",
            "llm": "openai_llm",
            "tts": "cartesia_tts",
        }

        extras = ServiceLoader.extract_extras_for_services(services)

        # Should always include these
        assert "runner" in extras
        assert "silero" in extras

        # Should include service-specific extras
        assert "daily" in extras
        assert "deepgram" in extras
        assert "openai" in extras
        assert "cartesia" in extras

    def test_extract_extras_for_realtime(self):
        """Test extracting extras for a realtime pipeline."""
        services = {
            "transports": ["daily"],
            "realtime": "openai_realtime",
        }

        extras = ServiceLoader.extract_extras_for_services(services)

        assert "runner" in extras
        assert "silero" in extras
        assert "daily" in extras
        assert "openai" in extras

    def test_validate_service_exists(self):
        """Test service existence validation."""
        assert ServiceLoader.validate_service_exists("deepgram_stt") is True
        assert ServiceLoader.validate_service_exists("daily") is True
        assert ServiceLoader.validate_service_exists("nonexistent") is False
