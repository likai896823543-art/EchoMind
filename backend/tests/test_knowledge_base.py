import sys
import types


# 该单元测试只验证文档 ID 和写入语义，本机无需安装完整 ChromaDB 依赖。
if "chromadb" not in sys.modules:
    try:
        import chromadb  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["chromadb"] = types.ModuleType("chromadb")

from mcp.knowledge_base import KnowledgeBase


def test_repeated_document_import_is_idempotent():
    class FakeCollection:
        def __init__(self):
            self.calls = []

        def upsert(self, **kwargs):
            self.calls.append(kwargs)

    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb._collection = FakeCollection()
    documents = [{"title": "退款政策", "content": "7 天内可以申请退款。"}]

    assert kb.add_documents(documents) == 1
    assert kb.add_documents(documents) == 1
    assert len(kb._collection.calls) == 2
    assert kb._collection.calls[0]["ids"] == kb._collection.calls[1]["ids"]
