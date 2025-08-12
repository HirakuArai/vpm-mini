import os
import json
import tempfile
from vpm_mini.summary import (
    summarize_last_session,
    prepend_memory,
    build_session_digest,
)


def test_summarize_short_text():
    """短いテキストは変更されない"""
    text = "これは短いテキストです。"
    result = summarize_last_session(text, max_chars=400)
    assert result == text
    assert len(result) <= 400


def test_summarize_long_text():
    """長いテキストは400文字以内に要約される"""
    text = "これは非常に長いテキストです。" * 50
    result = summarize_last_session(text, max_chars=400)
    assert len(result) <= 400
    assert result != ""


def test_summarize_with_keywords():
    """キーワードを含む文が優先される"""
    text = "普通の文です。目的はテストを成功させることです。これも普通の文です。"
    result = summarize_last_session(text, max_chars=50)
    assert "目的" in result


def test_prepend_memory_new_file():
    """新規ファイルへの書き込み"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        os.remove(temp_path)  # ファイルを削除して新規作成をテスト
        prepend_memory("新しい要約", temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert data[0] == "新しい要約"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_prepend_memory_existing_file():
    """既存ファイルへの先頭追加"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(["既存の要約"], f)
        temp_path = f.name

    try:
        prepend_memory("新しい要約", temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data[0] == "新しい要約"
        assert data[1] == "既存の要約"
    finally:
        os.remove(temp_path)


def test_prepend_memory_corrupted_file():
    """壊れたファイルの処理"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        f.write("壊れたJSON{")
        temp_path = f.name

    try:
        prepend_memory("新しい要約", temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert data[0] == "新しい要約"
        assert os.path.exists(temp_path + ".bak")
    finally:
        os.remove(temp_path)
        if os.path.exists(temp_path + ".bak"):
            os.remove(temp_path + ".bak")


def test_build_session_digest():
    """Session Digest構築の基本テスト"""
    text = "テストトランスクリプト"
    digest = build_session_digest(text)

    assert digest["type"] == "session_digest"
    assert "session_id" in digest
    assert "summary_ja_<=400chars" in digest
    assert len(digest["summary_ja_<=400chars"]) <= 400
