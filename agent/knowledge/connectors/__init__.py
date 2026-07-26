"""
V3: 知识源 connector 抽象 + 内置实现。
"""
from .base import KnowledgeConnector
from .local import LocalConnector
from .s3 import S3Connector
from .git_repo import GitConnector
from .notion import NotionConnector
from .factory import build_connector

__all__ = [
    "KnowledgeConnector",
    "LocalConnector",
    "S3Connector",
    "GitConnector",
    "NotionConnector",
    "build_connector",
]