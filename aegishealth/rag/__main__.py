"""Build a guideline index or retrieve two exact evidence snippets."""

import argparse
import json
from pathlib import Path

from aegishealth.rag.store import DEFAULT_INDEX, GuidelineRetriever, ingest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("ingest")
    build.add_argument("--source", required=True, type=Path)
    query = commands.add_parser("query")
    query.add_argument("text")
    for subparser in (build, query):
        subparser.add_argument("--index", default=DEFAULT_INDEX, type=Path)
        subparser.add_argument(
            "--offline", action="store_true", help="Use cached MiniLM weights only"
        )
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            result = ingest(args.source, args.index, offline=args.offline)
        else:
            result = {
                "query": args.text,
                "snippets": GuidelineRetriever(args.index, offline=args.offline).retrieve(
                    args.text
                ),
            }
    except (ValueError, FileNotFoundError, RuntimeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
