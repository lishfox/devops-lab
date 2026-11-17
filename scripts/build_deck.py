"""Build anki/*.yaml into dist/devops.apkg for AnkiDroid.

Card ids must never change: the note GUID is derived from them,
so re-importing the deck updates cards and keeps review progress.
"""
import glob
import html
import os
import re
import sys

import genanki
import yaml

MODEL_ID = 1638202589  # never change
DECK_ID = 2113173111  # never change

CSS = """
.card { font-family: sans-serif; font-size: 18px; text-align: left; padding: 8px; }
code { background: rgba(127,127,127,.18); padding: 1px 4px; border-radius: 4px; }
pre { background: rgba(127,127,127,.18); padding: 8px; border-radius: 6px;
      white-space: pre-wrap; word-break: break-word; font-size: 15px; }
.tags { color: gray; font-size: 13px; margin-top: 16px; }
"""

MODEL = genanki.Model(
    MODEL_ID,
    "DevOps Lab",
    fields=[{"name": "Id"}, {"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}",
    }],
    css=CSS,
)


def render(text: str) -> str:
    """Tiny markdown: ``` blocks, `code`, **bold**, line breaks."""
    out = []
    parts = re.split(r"```[a-z]*\n(.*?)```", text.strip(), flags=re.S)
    for i, part in enumerate(parts):
        if i % 2:
            out.append("<pre>" + html.escape(part.rstrip("\n")) + "</pre>")
            continue
        p = html.escape(part)
        p = re.sub(r"`([^`]+)`", r"<code>\1</code>", p)
        p = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", p)
        out.append(p.strip("\n").replace("\n", "<br>"))
    return "".join(out)


def main() -> int:
    deck = genanki.Deck(DECK_ID, "DevOps")
    seen = set()
    for path in sorted(glob.glob("anki/*.yaml")):
        with open(path, encoding="utf-8") as f:
            cards = yaml.safe_load(f) or []
        for c in cards:
            cid = c["id"]
            if cid in seen:
                print(f"::error file={path}::duplicate card id {cid}")
                return 1
            seen.add(cid)
            deck.add_note(genanki.Note(
                model=MODEL,
                fields=[cid, render(c["front"]), render(c["back"])],
                tags=c.get("tags", []),
                guid=genanki.guid_for("devops-lab", cid),
            ))
    os.makedirs("dist", exist_ok=True)
    genanki.Package(deck).write_to_file("dist/devops.apkg")
    print(f"Built dist/devops.apkg with {len(seen)} cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
