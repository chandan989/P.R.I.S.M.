"""
P.R.I.S.M. Custom Exceptions

Custom exception classes for better error handling and reporting.
"""

from typing import Any, Optional


class PRISMError(Exception):
    """Base exception for P.R.I.S.M. errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize PRISM error.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert error to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ModelError(PRISMError):
    """Errors related to model operations."""

    pass


class ModelNotInitializedError(ModelError):
    """Raised when model is not initialized."""

    def __init__(self, backend: Optional[str] = None):
        message = "Model not initialized"
        if backend:
            message += f" for backend: {backend}"
        super().__init__(message, {"backend": backend})


class ModelGenerationError(ModelError):
    """Raised when model generation fails."""

    def __init__(self, message: str, prompt: Optional[str] = None):
        super().__init__(message, {"prompt": prompt[:100] if prompt else None})


class KnowledgeBaseError(PRISMError):
    """Errors related to knowledge base operations."""

    pass


class KnowledgeBaseNotInitializedError(KnowledgeBaseError):
    """Raised when knowledge base is not initialized."""

    def __init__(self):
        super().__init__("Knowledge base not initialized")


class DocumentNotFoundError(KnowledgeBaseError):
    """Raised when a document is not found."""

    def __init__(self, doc_id: str):
        super().__init__(f"Document not found: {doc_id}", {"doc_id": doc_id})


class IndexCorruptedError(KnowledgeBaseError):
    """Raised when the knowledge base index is corrupted."""

    def __init__(self, path: Optional[str] = None):
        super().__init__("Knowledge base index is corrupted", {"path": path})


class VerificationError(PRISMError):
    """Errors related to claim verification."""

    pass


class ClaimVerificationError(VerificationError):
    """Raised when claim verification fails."""

    def __init__(self, claim: str, reason: str):
        super().__init__(
            f"Failed to verify claim: {reason}",
            {"claim": claim[:100], "reason": reason}
        )


class ParsingError(PRISMError):
    """Errors related to parsing operations."""

    pass


class DeliberationParseError(ParsingError):
    """Raised when deliberation parsing fails."""

    def __init__(self, reason: str):
        super().__init__(f"Failed to parse deliberation: {reason}")


class ClaimExtractionError(ParsingError):
    """Raised when claim extraction fails."""

    def __init__(self, reason: str):
        super().__init__(f"Failed to extract claims: {reason}")


class CalibrationError(PRISMError):
    """Errors related to confidence calibration."""

    pass


class CalibrationNotFittedError(CalibrationError):
    """Raised when calibration is not fitted."""

    def __init__(self, method: str):
        super().__init__(
            f"Calibration not fitted for method: {method}",
            {"method": method}
        )


class ConfigurationError(PRISMError):
    """Errors related to configuration."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid."""

    def __init__(self, setting: str, value: Any, reason: str):
        super().__init__(
            f"Invalid configuration for {setting}: {reason}",
            {"setting": setting, "value": str(value)}
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""

    def __init__(self, setting: str):
        super().__init__(
            f"Missing required configuration: {setting}",
            {"setting": setting}
        )


class SessionError(PRISMError):
    """Errors related to session management."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when a session is not found."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            {"session_id": session_id}
        )


class SessionExpiredError(SessionError):
    """Raised when a session has expired."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session expired: {session_id}",
            {"session_id": session_id}
        )
