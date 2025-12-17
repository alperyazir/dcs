"""
Validation Rules API Endpoint Tests (Story 3.4, AC: #8).

Tests for GET /api/v1/upload/validation-rules endpoint.
"""

from fastapi.testclient import TestClient


class TestValidationRulesEndpoint:
    """Tests for the validation rules endpoint."""

    def test_endpoint_returns_200(self, client: TestClient) -> None:
        """Endpoint returns 200 OK."""
        response = client.get("/api/v1/upload/validation-rules")
        assert response.status_code == 200

    def test_no_auth_required(self, client: TestClient) -> None:
        """Endpoint does not require authentication."""
        # No auth headers provided
        response = client.get("/api/v1/upload/validation-rules")
        assert response.status_code == 200

    def test_returns_allowed_mime_types(self, client: TestClient) -> None:
        """Response includes allowed MIME types."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert "allowed_mime_types" in data
        assert isinstance(data["allowed_mime_types"], list)
        assert len(data["allowed_mime_types"]) > 0

    def test_allowed_types_include_common_formats(self, client: TestClient) -> None:
        """Allowed types include PDF, images, videos, audio."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        allowed = data["allowed_mime_types"]
        assert "application/pdf" in allowed
        assert "image/jpeg" in allowed
        assert "video/mp4" in allowed
        assert "audio/mpeg" in allowed

    def test_returns_size_limits(self, client: TestClient) -> None:
        """Response includes size limits per category."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert "size_limits" in data
        assert isinstance(data["size_limits"], list)
        assert len(data["size_limits"]) >= 4  # video, image, audio, default

    def test_size_limits_have_categories(self, client: TestClient) -> None:
        """Size limits include all expected categories."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        categories = [limit["category"] for limit in data["size_limits"]]
        assert "video" in categories
        assert "image" in categories
        assert "audio" in categories
        assert "default" in categories

    def test_size_limits_have_bytes_and_human(self, client: TestClient) -> None:
        """Size limits include both bytes and human-readable values."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        for limit in data["size_limits"]:
            assert "max_size_bytes" in limit
            assert "max_size_human" in limit
            assert isinstance(limit["max_size_bytes"], int)
            assert isinstance(limit["max_size_human"], str)
            assert limit["max_size_bytes"] > 0

    def test_video_limit_is_10gb(self, client: TestClient) -> None:
        """Video size limit is 10GB."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        video_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "video"),
            None,
        )
        assert video_limit is not None
        assert video_limit["max_size_bytes"] == 10 * 1024 * 1024 * 1024
        assert "10" in video_limit["max_size_human"]
        assert "GB" in video_limit["max_size_human"]

    def test_image_limit_is_500mb(self, client: TestClient) -> None:
        """Image size limit is 500MB."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        image_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "image"),
            None,
        )
        assert image_limit is not None
        assert image_limit["max_size_bytes"] == 500 * 1024 * 1024
        assert "500" in image_limit["max_size_human"]
        assert "MB" in image_limit["max_size_human"]

    def test_audio_limit_is_100mb(self, client: TestClient) -> None:
        """Audio size limit is 100MB (Story 3.4, AC: #5)."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        audio_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "audio"),
            None,
        )
        assert audio_limit is not None
        assert audio_limit["max_size_bytes"] == 100 * 1024 * 1024
        assert "100" in audio_limit["max_size_human"]
        assert "MB" in audio_limit["max_size_human"]

    def test_default_limit_is_5gb(self, client: TestClient) -> None:
        """Default size limit is 5GB."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        default_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "default"),
            None,
        )
        assert default_limit is not None
        assert default_limit["max_size_bytes"] == 5 * 1024 * 1024 * 1024
        assert "5" in default_limit["max_size_human"]
        assert "GB" in default_limit["max_size_human"]

    def test_returns_extension_mappings(self, client: TestClient) -> None:
        """Response includes extension-to-MIME mappings."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert "extension_mappings" in data
        assert isinstance(data["extension_mappings"], list)
        assert len(data["extension_mappings"]) > 0

    def test_extension_mappings_have_correct_structure(
        self, client: TestClient
    ) -> None:
        """Extension mappings have extension and mime_types fields."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        for mapping in data["extension_mappings"]:
            assert "extension" in mapping
            assert "mime_types" in mapping
            assert isinstance(mapping["extension"], str)
            assert isinstance(mapping["mime_types"], list)
            assert mapping["extension"].startswith(".")

    def test_pdf_extension_mapped(self, client: TestClient) -> None:
        """PDF extension is mapped to application/pdf."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        pdf_mapping = next(
            (m for m in data["extension_mappings"] if m["extension"] == ".pdf"), None
        )
        assert pdf_mapping is not None
        assert "application/pdf" in pdf_mapping["mime_types"]

    def test_image_extensions_mapped(self, client: TestClient) -> None:
        """Image extensions are mapped correctly."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        extensions = [m["extension"] for m in data["extension_mappings"]]
        assert ".jpg" in extensions
        assert ".jpeg" in extensions
        assert ".png" in extensions

    def test_returns_max_filename_length(self, client: TestClient) -> None:
        """Response includes max filename length."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert "max_filename_length" in data
        assert data["max_filename_length"] == 255

    def test_returns_dangerous_extensions(self, client: TestClient) -> None:
        """Response includes list of dangerous extensions."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert "dangerous_extensions" in data
        assert isinstance(data["dangerous_extensions"], list)
        assert len(data["dangerous_extensions"]) > 0

    def test_dangerous_extensions_include_executables(self, client: TestClient) -> None:
        """Dangerous extensions include common executables."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        dangerous = data["dangerous_extensions"]
        assert ".exe" in dangerous
        assert ".bat" in dangerous
        assert ".cmd" in dangerous

    def test_dangerous_extensions_include_scripts(self, client: TestClient) -> None:
        """Dangerous extensions include server-side scripts."""
        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        dangerous = data["dangerous_extensions"]
        assert ".php" in dangerous
        assert ".jsp" in dangerous
        assert ".asp" in dangerous

    def test_response_is_json(self, client: TestClient) -> None:
        """Response has correct content type."""
        response = client.get("/api/v1/upload/validation-rules")
        assert "application/json" in response.headers.get("content-type", "")


class TestValidationRulesConsistency:
    """Tests to ensure rules match actual validation behavior."""

    def test_allowed_types_match_config(self, client: TestClient) -> None:
        """Allowed types match settings.ALLOWED_MIME_TYPES."""
        from app.core.config import settings

        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        assert data["allowed_mime_types"] == settings.ALLOWED_MIME_TYPES

    def test_video_limit_matches_config(self, client: TestClient) -> None:
        """Video limit matches settings.MAX_FILE_SIZE_VIDEO."""
        from app.core.config import settings

        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        video_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "video"),
            None,
        )
        assert video_limit["max_size_bytes"] == settings.MAX_FILE_SIZE_VIDEO

    def test_audio_limit_matches_config(self, client: TestClient) -> None:
        """Audio limit matches settings.MAX_FILE_SIZE_AUDIO."""
        from app.core.config import settings

        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        audio_limit = next(
            (limit for limit in data["size_limits"] if limit["category"] == "audio"),
            None,
        )
        assert audio_limit["max_size_bytes"] == settings.MAX_FILE_SIZE_AUDIO

    def test_extension_map_matches_service(self, client: TestClient) -> None:
        """Extension mappings match file_validation_service.EXTENSION_MIME_MAP."""
        from app.services.file_validation_service import EXTENSION_MIME_MAP

        response = client.get("/api/v1/upload/validation-rules")
        data = response.json()

        returned_map = {
            m["extension"]: m["mime_types"] for m in data["extension_mappings"]
        }

        for ext, mimes in EXTENSION_MIME_MAP.items():
            assert ext in returned_map, f"Extension {ext} not in response"
            assert returned_map[ext] == mimes, f"MIME types for {ext} don't match"
