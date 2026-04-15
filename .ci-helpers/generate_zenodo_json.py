"""Generate .zenodo.json for the current repository."""

import csv
import json
import subprocess
from pathlib import Path

import orcid


ORCID_PATH = Path("../.orcid.csv")
OUTPUT_PATH = Path("../.zenodo.json")
KEY_SECRET_PATH = Path("../key_secret.json")
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


def load_orcid_map() -> dict[str, str]:
    """Load ORCID identifiers indexed by author email from .orcid.csv."""

    with ORCID_PATH.open(newline="") as orcid_file:
        reader = csv.DictReader(orcid_file)
        return {
            row["email"]: row["orcid"].strip()
            for row in reader
            if row.get("email") and row.get("orcid") and row["orcid"].strip()
        }


def create_orcid_api() -> tuple[orcid.PublicAPI, str] | None:
    """Create the ORCID API client and fetch a search token if configured."""

    if not KEY_SECRET_PATH.exists():
        print(f"Skipping ORCID API lookup: {KEY_SECRET_PATH} not found.")
        return None

    with KEY_SECRET_PATH.open() as key_secret_file:
        keys = json.load(key_secret_file)

    api = orcid.PublicAPI(keys["key"], keys["secret"])
    token = api.get_search_token_from_orcid()
    return api, token


def get_affiliation(api: orcid.PublicAPI, token: str, orcid_id: str) -> str | None:
    """Return the first public employment affiliation for an ORCID record."""

    author_orcid = api.read_record_public(orcid_id, "record", token)

    try:
        return author_orcid["activities-summary"]["employments"]["employment-summary"][
            0
        ]["organization"]["name"]
    except IndexError:
        return None


def build_zenodo_creators() -> list[dict[str, str]]:
    """Build the Zenodo creators payload from git and ORCID metadata."""

    authors = build_authors()
    orcid_map = load_orcid_map()
    orcid_api = create_orcid_api()

    zenodo_authors = []
    for author in authors:
        zenodo_entry = {
            "name": f"{author['last_name']}, {author['first_name']}",
        }
        orcid_id = orcid_map.get(str(author["email"]))

        if orcid_id:
            zenodo_entry["orcid"] = orcid_id
            if orcid_api is not None:
                api, token = orcid_api
                affiliation = get_affiliation(api, token, orcid_id)
                if affiliation:
                    zenodo_entry["affiliation"] = affiliation
                    print(author["last_name"], affiliation)

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
