#!/usr/bin/env python3
"""Deterministically reverse stored UTF-8/Windows-1252 mojibake in JSON strings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


JSON_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
BAD_TOKENS = ("Ã", "Â", "â", "Æ", "ï»¿", "\ufffd")


def build_windows_1252_inverse() -> dict[str, int]:
    inverse: dict[str, int] = {}
    for value in range(256):
        try:
            character = bytes([value]).decode("cp1252")
        except UnicodeDecodeError:
            character = chr(value)
        inverse[character] = value
    return inverse


WINDOWS_1252_INVERSE = build_windows_1252_inverse()


def badness(value: str) -> int:
    return sum(value.count(token) for token in BAD_TOKENS)


def decode_one_generation(value: str) -> str:
    encoded: list[tuple[bool, int | str]] = []
    for character in value:
        if ord(character) <= 255:
            encoded.append((True, ord(character)))
        elif character in WINDOWS_1252_INVERSE:
            encoded.append((True, WINDOWS_1252_INVERSE[character]))
        else:
            encoded.append((False, character))

    output: list[str] = []
    index = 0
    while index < len(encoded):
        is_byte, item = encoded[index]
        if not is_byte:
            output.append(str(item))
            index += 1
            continue

        byte = int(item)
        if byte < 128:
            output.append(chr(byte))
            index += 1
            continue

        length = 2 if 194 <= byte <= 223 else 3 if 224 <= byte <= 239 else 4 if 240 <= byte <= 244 else 0
        if length and index + length <= len(encoded):
            sequence = encoded[index : index + length]
            if all(flag and 128 <= int(part) <= 191 for flag, part in sequence[1:]):
                try:
                    output.append(bytes(int(part) for _, part in sequence).decode("utf-8"))
                    index += length
                    continue
                except UnicodeDecodeError:
                    pass

        try:
            output.append(bytes([byte]).decode("cp1252"))
        except UnicodeDecodeError:
            output.append(chr(byte))
        index += 1

    repaired = "".join(output)
    if value.startswith("ï»¿") and repaired.startswith("\ufeff"):
        repaired = repaired.removeprefix("\ufeff")
    return repaired


def repair_string(value: str) -> tuple[str, int]:
    current = value
    generations = 0
    while generations < 8:
        candidate = decode_one_generation(current)
        if badness(candidate) >= badness(current):
            break
        current = candidate
        generations += 1
    return current, generations


def repair_json_text(raw: str) -> tuple[str, int, int]:
    changed = 0
    maximum_generations = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed, maximum_generations
        original_token = match.group(0)
        original = json.loads(original_token)
        repaired, generations = repair_string(original)
        if repaired == original:
            return original_token
        changed += 1
        maximum_generations = max(maximum_generations, generations)
        return json.dumps(repaired, ensure_ascii=False)

    repaired_text = JSON_STRING.sub(replace, raw)
    json.loads(repaired_text)
    return repaired_text, changed, maximum_generations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inventory",
        default="project-state/master-inventory.json",
        help="Path to the master inventory JSON file.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    path = Path(args.inventory)
    raw_bytes = path.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("Inventory unexpectedly contains a UTF-8 BOM.")
    raw = raw_bytes.decode("utf-8")
    repaired, changed, maximum_generations = repair_json_text(raw)
    result = {
        "inventory": str(path),
        "strings_requiring_repair": changed,
        "maximum_encoding_generations": maximum_generations,
        "utf8_bom": False,
    }
    print(json.dumps(result, ensure_ascii=False))

    if args.check:
        return 1 if changed else 0

    path.write_text(repaired, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
