"""V2: evaluators + dataset（local fallback）。"""
import json
from pathlib import Path

from agent.eval.dataset import fetch_examples, push_examples
from agent.eval.evaluators import heuristic, similarity


def test_heuristic_intent_match():
    example = {"expect_intent": "faq"}
    output = {"intent": "faq", "answer": "ok"}
    s = heuristic(example, output)
    assert s["intent"]["score"] == 1.0
    assert s["intent"]["comment"].startswith("expect=faq")


def test_heuristic_intent_mismatch():
    s = heuristic({"expect_intent": "faq"}, {"intent": "refuse", "answer": ""})
    assert s["intent"]["score"] == 0.0
    assert s["keywords"]["score"] == 1.0


def test_heuristic_keywords_partial():
    # "充值" 命中、"支付宝" 命中 → 2/2；用第三个不存在关键词触发 partial
    s = heuristic(
        {"expect_intent": "faq", "expect_keywords": ["充值", "支付宝", "微信"]},
        {"intent": "faq", "answer": "你可以用支付宝充值"},
    )
    assert s["keywords"]["score"] == 2 / 3


def test_heuristic_tools_match():
    s = heuristic(
        {"expect_intent": "account", "expect_tools": ["balance"]},
        {"intent": "account", "answer": "ok", "tool_results": [{"tool": "balance"}]},
    )
    assert s["tools"]["score"] == 1.0


def test_similarity_empty():
    from unittest.mock import MagicMock
    ev = similarity(MagicMock(), expected_answer="")
    out = ev({"q": "x"}, {"answer": ""})
    assert out["similarity"]["score"] == 0.0


def test_dataset_local_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    examples = [
        {"q": "怎么充值", "expect_intent": "faq", "expect_keywords": ["支付宝"]},
        {"q": "我的余额", "expect_intent": "account"},
    ]
    n = push_examples("test-ds", examples)
    assert n == 2
    out = fetch_examples("test-ds")
    assert len(out) == 2
    assert out[0]["q"] == "怎么充值"
    assert out[1]["expect_intent"] == "account"


def test_dataset_local_jsonl_format(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    push_examples("x", [{"q": "Q1", "expect_intent": "faq"}])
    path = Path("data/datasets/x.jsonl")
    assert path.is_file()
    line = path.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["q"] == "Q1"