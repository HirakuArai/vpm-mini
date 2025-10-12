#!/usr/bin/env python3
import argparse
import pathlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--in", dest="input_path", required=True)
    parser.add_argument("--out", dest="output_path", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "# VPM Output (engine stub)\n"
        f"mode: {args.mode}\n\n"
        f"(read {args.input_path})\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
