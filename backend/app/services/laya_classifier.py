"""
Laya AI Classification Service

This service provides AI-assisted classification for REVIEW items from the
deterministic Excel validator. It uses LiteLLM to interface with various
LLM providers (Anthropic, OpenAI, Gemini, or local models via Ollama/LMStudio).

CRITICAL: This service NEVER overrides deterministic validation results.
It only provides classification and reasoning to assist human review of
items that the deterministic validator could not conclusively verify.
"""

import json
import time
import logging
from typing import Any, Optional
from enum import Enum

from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential
from pydantic import BaseModel, Field, ValidationError

from app.core.config import (
    LAYA_ENABLED,
    LAYA_MODEL,
    LAYA_API_KEY,
    LAYA_API_BASE,
    LAYA_TIMEOUT_SECONDS,
    LAYA_MAX_TOKENS,
)

log = logging.getLogger(__name__)


class ReviewClassification(str, Enum):
    """Classification types for REVIEW items."""
    LIKELY_VALID = "likely_valid"
    LIKELY_ISSUE = "likely_issue"
    FORMATTING_VARIATION = "formatting_variation"
    UNVERIFIABLE = "unverifiable"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class AIReviewClassification(BaseModel):
    """Structured output from AI classification."""
    classification: ReviewClassification = Field(
        description="The classification of this review item"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 to 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description="Optional: what the user should check"
    )


class LayaClassificationResult(BaseModel):
    """Result of Laya classification for a review item."""
    success: bool
    classification: Optional[ReviewClassification] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    suggested_action: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class LayaClassifier:
    """
    AI classifier for Excel validation REVIEW items.

    This service uses LiteLLM to interface with various LLM providers
    and provides structured classification of review items that the
    deterministic validator could not conclusively verify.
    """

    def __init__(self):
        self.enabled = LAYA_ENABLED
        self.model = LAYA_MODEL
        self.api_key = LAYA_API_KEY
        self.api_base = LAYA_API_BASE
        self.timeout = LAYA_TIMEOUT_SECONDS
        self.max_tokens = LAYA_MAX_TOKENS

        if not self.enabled:
            log.info("laya_classifier_disabled")
        else:
            log.info(
                f"laya_classifier_initialized: model={self.model}, "
                f"has_api_key={bool(self.api_key)}, has_custom_base={bool(self.api_base)}"
            )

    def is_enabled(self) -> bool:
        """Check if Laya classification is enabled."""
        return self.enabled

    def _build_system_prompt(self) -> str:
        """Build the system prompt for classification."""
        return """You are an expert analyst of Excel assessment reports. Your job is to classify REVIEW items from a deterministic validation system.

IMPORTANT CONTEXT:
- The deterministic validator has already checked this workbook using strict rules
- This item is marked REVIEW because the validator could not conclusively verify it
- You are NOT replacing the deterministic validation
- You are providing classification to assist human review

CLASSIFICATION OPTIONS:
1. likely_valid - The item appears to be correct based on context, but needs human confirmation
2. likely_issue - The item appears to be a genuine data issue that needs correction
3. formatting_variation - The item is likely just a formatting/representation difference, not a data problem
4. unverifiable - There is insufficient context to make a determination
5. needs_human_review - The item is complex or ambiguous and requires human expertise

Your response must be a valid JSON object with these fields:
{
  "classification": "one of the 5 options above",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation",
  "suggested_action": "optional: what the user should check"
}

Be concise and specific. Focus on whether this can be verified automatically or needs human review."""

    def _build_user_prompt(self, review_context: dict[str, Any]) -> str:
        """Build the user prompt with review item context."""
        parts = [
            f"Filename: {review_context.get('filename', 'unknown')}",
            f"Template: {review_context.get('template', 'unknown')}",
            f"Review Type: {review_context.get('review_type', 'unknown')}",
        ]

        if review_context.get('sheet'):
            parts.append(f"Sheet: {review_context['sheet']}")
        if review_context.get('cell'):
            parts.append(f"Cell: {review_context['cell']}")

        parts.append(f"\nValidation Message: {review_context.get('validation_message', 'N/A')}")
        parts.append(f"Validation Rule: {review_context.get('validation_rule', 'N/A')}")

        if review_context.get('actual_value'):
            parts.append(f"Actual Value: {review_context['actual_value']}")
        if review_context.get('expected_value'):
            parts.append(f"Expected Value: {review_context['expected_value']}")

        if review_context.get('relevant_context'):
            parts.append(f"\nRelevant Context:\n{review_context['relevant_context']}")

        return "\n".join(parts)

    def _prepare_litellm_kwargs(self) -> dict[str, Any]:
        """Prepare kwargs for LiteLLM completion."""
        kwargs = {
            "model": self.model,
            "messages": [],
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

        # Add API key if provided
        if self.api_key:
            kwargs["api_key"] = self.api_key

        # Add custom API base for local providers
        if self.api_base:
            kwargs["api_base"] = self.api_base

        return kwargs

    @retry(
        stop=stop_after_attempt(2),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    def _call_llm(self, messages: list[dict]) -> str:
        """Call the LLM via LiteLLM with retry logic."""
        try:
            import litellm
        except ImportError:
            raise RuntimeError("litellm package is not installed")

        kwargs = self._prepare_litellm_kwargs()
        kwargs["messages"] = messages

        log.debug(f"laya_llm_call_start: model={self.model}")

        response = litellm.completion(**kwargs)

        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
        log.debug(f"laya_llm_call_success: model={self.model}, tokens_used={tokens_used}")

        return content

    def _parse_llm_response(self, response_text: str) -> AIReviewClassification:
        """Parse and validate the LLM response."""
        # Try to extract JSON from the response
        try:
            # Handle markdown code blocks
            if response_text.strip().startswith("```"):
                lines = response_text.strip().split("\n")
                if lines[0].startswith("```json"):
                    response_text = "\n".join(lines[1:-1])
                else:
                    response_text = "\n".join(lines[1:-1])

            data = json.loads(response_text.strip())
            return AIReviewClassification(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            log.warning(f"laya_response_parse_failed: error={str(e)}, response={response_text[:200]}")
            raise ValueError(f"Failed to parse LLM response: {e}")

    def classify_review_item(self, review_context: dict[str, Any]) -> LayaClassificationResult:
        """
        Classify a single REVIEW item using AI.

        Args:
            review_context: Dictionary containing review item details:
                - filename: str
                - template: str
                - review_type: str
                - sheet: str | None
                - cell: str | None
                - actual_value: Any
                - expected_value: Any
                - validation_message: str
                - validation_rule: str
                - relevant_context: str

        Returns:
            LayaClassificationResult with classification or error details
        """
        start_time = time.time()

        if not self.enabled:
            return LayaClassificationResult(
                success=False,
                error="Laya classification is disabled"
            )

        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(review_context)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Call LLM
            response_text = self._call_llm(messages)

            # Parse response
            classification = self._parse_llm_response(response_text)

            latency_ms = int((time.time() - start_time) * 1000)

            log.info(
                f"laya_classification_success: filename={review_context.get('filename')}, "
                f"review_type={review_context.get('review_type')}, "
                f"classification={classification.classification}, "
                f"confidence={classification.confidence}, "
                f"latency_ms={latency_ms}"
            )

            return LayaClassificationResult(
                success=True,
                classification=classification.classification,
                confidence=classification.confidence,
                reasoning=classification.reasoning,
                suggested_action=classification.suggested_action,
                model_used=self.model,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            log.error(
                f"laya_classification_failed: filename={review_context.get('filename')}, "
                f"review_type={review_context.get('review_type')}, "
                f"error={str(e)}, latency_ms={latency_ms}"
            )

            return LayaClassificationResult(
                success=False,
                error=str(e),
                model_used=self.model,
                latency_ms=latency_ms,
            )

    def classify_review_items_batch(
        self,
        review_items: list[dict[str, Any]]
    ) -> list[LayaClassificationResult]:
        """
        Classify multiple REVIEW items in batch.

        Args:
            review_items: List of review context dictionaries

        Returns:
            List of LayaClassificationResult in the same order as input
        """
        if not self.enabled:
            return [
                LayaClassificationResult(
                    success=False,
                    error="Laya classification is disabled"
                )
                for _ in review_items
            ]

        results = []
        for item in review_items:
            result = self.classify_review_item(item)
            results.append(result)

        return results


# Singleton instance
_laya_classifier_instance: Optional[LayaClassifier] = None


def get_laya_classifier() -> LayaClassifier:
    """Get the singleton Laya classifier instance."""
    global _laya_classifier_instance
    if _laya_classifier_instance is None:
        _laya_classifier_instance = LayaClassifier()
    return _laya_classifier_instance
