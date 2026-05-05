from __future__ import annotations

from pathlib import Path


class VdfParseError(ValueError):
    pass


def parse_key_values(text: str) -> dict[str, object]:
    tokens = _tokenize(text)
    parser = _KeyValueParser(tokens)
    return parser.parse()


def parse_key_values_file(path: Path) -> dict[str, object]:
    return parse_key_values(path.read_text(encoding="utf-8-sig", errors="replace"))


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]

        if char.isspace():
            index += 1
            continue

        if char == "/" and index + 1 < len(text) and text[index + 1] == "/":
            newline = text.find("\n", index)
            if newline == -1:
                break
            index = newline + 1
            continue

        if char in "{}":
            tokens.append(char)
            index += 1
            continue

        if char == '"':
            value, index = _read_quoted(text, index)
            tokens.append(value)
            continue

        start = index
        while index < len(text) and not text[index].isspace() and text[index] not in "{}":
            index += 1
        tokens.append(text[start:index])

    return tokens


def _read_quoted(text: str, start: int) -> tuple[str, int]:
    chars: list[str] = []
    index = start + 1

    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in {'"', "\\"}:
            chars.append(text[index + 1])
            index += 2
            continue
        if char == '"':
            return "".join(chars), index + 1
        chars.append(char)
        index += 1

    raise VdfParseError("unterminated quoted string")


class _KeyValueParser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.index = 0

    def parse(self) -> dict[str, object]:
        data = self._parse_object(stop_at_closing_brace=False)
        if self.index != len(self.tokens):
            raise VdfParseError("unexpected trailing tokens")
        return data

    def _parse_object(self, stop_at_closing_brace: bool) -> dict[str, object]:
        result: dict[str, object] = {}

        while self.index < len(self.tokens):
            if self.tokens[self.index] == "}":
                if not stop_at_closing_brace:
                    raise VdfParseError("unexpected closing brace")
                self.index += 1
                return result

            key = self._consume()
            if self.index >= len(self.tokens):
                raise VdfParseError(f"missing value for key {key!r}")

            if self.tokens[self.index] == "{":
                self.index += 1
                result[key] = self._parse_object(stop_at_closing_brace=True)
            else:
                result[key] = self._consume()

        if stop_at_closing_brace:
            raise VdfParseError("missing closing brace")

        return result

    def _consume(self) -> str:
        token = self.tokens[self.index]
        self.index += 1
        return token
