#!/usr/bin/env python3
import argparse
import os
import sys

PROMPT_WRAP = """\
You will receive two inputs:

[PROMPT_TEMPLATE]
{prompt}

[STATE_MD]
{state}

Respond strictly following the OUTPUT sections and style described in [PROMPT_TEMPLATE].
If any field is missing in STATE, infer conservatively and explain assumptions briefly in Notes.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--in", dest="state_path", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read()
    with open(args.state_path, "r", encoding="utf-8") as f:
        state = f.read()

    full_prompt = PROMPT_WRAP.format(prompt=prompt, state=state)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    content = None
    try:
        if anthropic_key:
            # Anthropic
            from anthropic import Anthropic

            client = Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=4000,
                system="You are VPM. Output in Japanese unless the input is not Japanese.",
                messages=[{"role": "user", "content": full_prompt}],
            )
            content = "".join(
                block.text for block in resp.content if hasattr(block, "text")
            )
        elif openai_key:
            # OpenAI
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4-0125-preview")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are VPM. Output in Japanese unless the input is not Japanese.",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content
        else:
            raise RuntimeError("Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is set.")
    except Exception as e:
        sys.stderr.write(f"[codex_shim] LLM call failed: {e}\n")
        sys.exit(2)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content or "# ERROR: empty content\n")

    print(f"[codex_shim] wrote: {args.out}")


if __name__ == "__main__":
    main()
