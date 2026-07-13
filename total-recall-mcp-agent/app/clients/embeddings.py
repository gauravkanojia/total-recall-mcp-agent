"""
Embedding provider abstractions.
"""

import asyncio
import hashlib
import json
from typing import Protocol

from app.clients.aws import get_bedrock_runtime_client
from app.core.config import settings


class EmbeddingProvider(Protocol):
    """
    Interface for text-to-vector embedding providers.
    """

    async def embed(self, text: str) -> list[float]:
        """
        Convert text into an embedding vector.
        """


class FakeEmbeddingProvider:
    """
    Deterministic local embedding provider for tests and local development.
    """

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """
        Build a stable pseudo-embedding from the input text.
        """

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []

        while len(values) < self.dimensions:
            for byte in digest:
                values.append((byte / 255.0) * 2 - 1)
                if len(values) == self.dimensions:
                    break
            digest = hashlib.sha256(digest).digest()

        return values


class BedrockEmbeddingProvider:
    """
    Amazon Bedrock Titan Text Embeddings V2 provider.
    """

    def __init__(
        self,
        *,
        model_id: str,
        dimensions: int,
    ) -> None:
        self.model_id = model_id
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """
        Invoke Bedrock and return the embedding vector.
        """

        client = get_bedrock_runtime_client()
        body = json.dumps(
            {
                "inputText": text,
                "dimensions": self.dimensions,
                "normalize": True,
            }
        )

        response = await asyncio.to_thread(
            client.invoke_model,
            modelId=self.model_id,
            body=body,
            accept="application/json",
            contentType="application/json",
        )

        payload = json.loads(response["body"].read())
        return payload["embedding"]


def get_embedding_provider() -> EmbeddingProvider:
    """
    Return the configured embedding provider.
    """

    if settings.EMBEDDING_PROVIDER == "bedrock":
        return BedrockEmbeddingProvider(
            model_id=settings.EMBEDDING_MODEL_ID,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )

    return FakeEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)
