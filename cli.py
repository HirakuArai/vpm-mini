#!/usr/bin/env python
"""
使い方: python cli.py <objective_id> <メッセージ>
例    : python cli.py demo "こんにちは"
"""

import sys, pathlib

# src/ を import パスへ追加
sys.path.append(str(pathlib.Path(__file__).resolve().parent / "src"))
from core import ask_openai

def main():
    if len(sys.argv) < 3:
        print("Usage: python cli.py <objective_id> <message>")
        sys.exit(1)

    obj_id   = sys.argv[1]
    user_msg = " ".join(sys.argv[2:])
    print(ask_openai(obj_id, user_msg))

if __name__ == "__main__":
    main()
