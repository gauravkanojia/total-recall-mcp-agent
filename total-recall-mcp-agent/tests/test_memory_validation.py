"""
Input-bound validation tests for MemoryService (no DB required).
"""

import pytest

from app.clients.embeddings import FakeEmbeddingProvider
from app.services.memory_service import (
    MAX_CONTENT_CHARS,
    MAX_KIND_CHARS,
    MAX_METADATA_BYTES,
    MAX_RECALL_LIMIT,
    MemoryService,
    validate_content,
    validate_kind,
    validate_limit,
    validate_metadata,
)


def _service() -> MemoryService:
    return MemoryService(session=None, embedding_provider=FakeEmbeddingProvider(8))


# --- validators -----------------------------------------------------------


def test_validate_content_bounds():
    assert validate_content("hello") == "hello"

    with pytest.raises(ValueError, match="must not be empty"):
        validate_content("   ")

    with pytest.raises(ValueError, match=str(MAX_CONTENT_CHARS)):
        validate_content("x" * (MAX_CONTENT_CHARS + 1))


def test_validate_kind_bounds():
    assert validate_kind("preference") == "preference"

    with pytest.raises(ValueError, match="must not be empty"):
        validate_kind("")

    with pytest.raises(ValueError, match=str(MAX_KIND_CHARS)):
        validate_kind("k" * (MAX_KIND_CHARS + 1))


def test_validate_metadata_bounds():
    assert validate_metadata(None) is None
    assert validate_metadata({"a": 1}) == {"a": 1}

    with pytest.raises(ValueError, match=str(MAX_METADATA_BYTES)):
        validate_metadata({"blob": "x" * MAX_METADATA_BYTES})


def test_validate_limit_bounds():
    assert validate_limit(1) == 1
    assert validate_limit(MAX_RECALL_LIMIT) == MAX_RECALL_LIMIT

    for bad in (0, -1, MAX_RECALL_LIMIT + 1):
        with pytest.raises(ValueError, match="limit must be between"):
            validate_limit(bad)


# --- service applies validation before touching DB/embeddings -------------


@pytest.mark.asyncio
async def test_remember_rejects_oversized_content_before_db():
    with pytest.raises(ValueError, match=str(MAX_CONTENT_CHARS)):
        await _service().remember(
            principal_id="local-test-user",
            kind="fact",
            content="x" * (MAX_CONTENT_CHARS + 1),
        )


@pytest.mark.asyncio
async def test_recall_rejects_bad_limit_before_db():
    with pytest.raises(ValueError, match="limit must be between"):
        await _service().recall(
            principal_id="local-test-user",
            query="anything",
            limit=0,
        )


@pytest.mark.asyncio
async def test_forget_rejects_invalid_uuid_before_db():
    with pytest.raises(ValueError, match="valid UUID"):
        await _service().forget(
            principal_id="local-test-user",
            memory_id="not-a-uuid",
        )


@pytest.mark.asyncio
async def test_list_rejects_bad_limit_before_db():
    with pytest.raises(ValueError, match="limit must be between"):
        await _service().list_memories(
            principal_id="local-test-user",
            limit=0,
        )
