"""Generate .zenodo.json for the current repository."""

import json
import subprocess
from pathlib import Path

OUTPUT_PATH = Path("../.zenodo.json")
CI_EMAILS = {"my-bot@email.com"}


def get_commit_counts() -> dict[str, int]:
    """Return commit counts keyed by the raw author string from git shortlog."""

    result = subprocess.run(
        ["git", "shortlog", "-sne", "HEAD"],
        capture_output=True,
        check=True,
        text=True,
    )

    commit_counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        commits, raw_name = line.split("\t", maxsplit=1)
        commit_counts[raw_name] = commit_counts.get(raw_name, 0) + int(commits.strip())

    return commit_counts


def parse_author(raw_name: str) -> dict[str, str] | None:
    """Parse a git author string into name parts and email, or return None."""

    parts = raw_name.split()

    if len(parts) < 3:
        print(f"Incomplete author name: {parts}")
        return None

    if len(parts) > 3:
        parts[1] = f"{parts[1]} {parts[2]}"
        del parts[2]

    return {
        "first_name": parts[0],
        "last_name": parts[1],
        "email": parts[2].strip("<>"),
    }


def find_duplicate_names(authors: list[dict[str, str | int]]) -> set[tuple[str, str]]:
    """Return author names that appear more than once in the author list."""

    counts: dict[tuple[str, str], int] = {}
    for author in authors:
        name = (str(author["first_name"]), str(author["last_name"]))
        counts[name] = counts.get(name, 0) + 1

    return {name for name, count in counts.items() if count > 1}


def build_authors() -> list[dict[str, str | int]]:
    """Build the de-duplicated author list ordered by commit count."""

    authors = []
    for raw_name, commits in get_commit_counts().items():
        parsed_author = parse_author(raw_name)
        if parsed_author is None:
            continue

        authors.append({**parsed_author, "commits": commits})

    authors = [author for author in authors if author["email"] not in CI_EMAILS]
    authors.sort(key=lambda author: int(author["commits"]), reverse=True)

    duplicate_names = find_duplicate_names(authors)
    for author in authors:
        name = (str(author["first_name"]), str(author["last_name"]))
        if name in duplicate_names:
            print(
                "Duplicated author: "
                f"{author['last_name']}, {author['first_name']} <{author['email']}>"
            )

    unique_authors = []
    seen_names = set()
    for author in authors:
        name = (str(author["first_name"]), str(author["last_name"]))
        if name in seen_names:
            continue

        seen_names.add(name)
        unique_authors.append(author)

    return unique_authors


def build_zenodo_creators() -> list[dict[str, str]]:
    """Build the Zenodo creators payload from git and ORCID metadata."""

    authors = build_authors()

    zenodo_authors = []
    for author in authors:
        zenodo_entry = {
            "name": f"{author['last_name']}, {author['first_name']}",
        }

        zenodo_authors.append(zenodo_entry)

    return zenodo_authors


def main() -> None:
    """Generate .zenodo.json and print the resulting metadata."""

    zenodo_json = {"creators": build_zenodo_creators()}

    with OUTPUT_PATH.open("w") as output_file:
        json.dump(zenodo_json, output_file, indent=2)

    print(OUTPUT_PATH.read_text())


if __name__ == "__main__":
    main()
