"""
AWS client factories.
"""

from functools import lru_cache

import boto3

from app.core.config import settings


@lru_cache
def get_bedrock_runtime_client():
    """
    Return a cached Bedrock Runtime client.
    """

    return boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
