import argparse
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def parse_github_repo_path(repo_url: str) -> str:
    """
    Extract the "owner/repo" part from a GitHub URL.

    Examples
    --------
    - https://github.com/owner/repo -> owner/repo
    - https://github.com/owner/repo/ -> owner/repo
    - https://github.com/owner/repo.git -> owner/repo
    """
    parsed = urlparse(repo_url)
    if "github.com" not in parsed.netloc:
        raise ValueError(f"Not a GitHub URL: {repo_url}")

    # Drop leading and trailing slashes, then split
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path_parts) < 2:
        raise ValueError(f"Could not parse owner/repo from: {repo_url}")

    owner, repo = path_parts[0], path_parts[1]
    repo = re.sub(r"\.git$", "", repo)
    return f"{owner}/{repo}"


def build_github_archive_zip_url(repo_url: str, ref: str, ref_type: str = "tag") -> str:
    """
    Build the GitHub archive URL for a given repo and ref (tag or branch).

    GitHub convention:
    - Tag:    https://github.com/{owner}/{repo}/archive/refs/tags/{ref}.zip
    - Branch: https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.zip
    """
    owner_repo = parse_github_repo_path(repo_url)
    if ref_type == "branch":
        return f"https://github.com/{owner_repo}/archive/refs/heads/{ref}.zip"
    # default to tag
    return f"https://github.com/{owner_repo}/archive/refs/tags/{ref}.zip"


def download_zip(url: str, dest_path: Path) -> None:
    """Download a file from `url` to `dest_path` using stdlib only."""
    with urlopen(url) as resp, open(dest_path, "wb") as f:
        shutil.copyfileobj(resp, f)


def keep_only_rst_files(root_dir: Path) -> None:
    """
    In-place prune: keep only .rst files under `root_dir`.
    Remove all other files and any empty directories.
    """
    # Remove non-.rst files
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            file_path = Path(dirpath) / name
            if file_path.suffix.lower() != ".rst":
                file_path.unlink(missing_ok=True)

    # Remove empty directories (walk bottom-up)
    for dirpath, dirnames, _ in os.walk(root_dir, topdown=False):
        for d in dirnames:
            p = Path(dirpath) / d
            # If directory is empty after removals, delete it
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()


def extract_zip_only_rst(zip_path: Path, output_parent: Path) -> Path:
    """
    Extract the zip into a subfolder under `output_parent` and prune to .rst files.

    Returns the path to the extracted root directory.
    """
    output_parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Zip produced by GitHub usually has one top-level directory
        zf.extractall(output_parent)

    # Detect the top-level directory created by extraction
    extracted_items = [p for p in output_parent.iterdir() if p.is_dir()]
    if len(extracted_items) == 1:
        root_dir = extracted_items[0]
    else:
        # Fallback: use parent directly
        root_dir = output_parent

    keep_only_rst_files(root_dir)
    return root_dir


def download_github_repo_rst(
    repo_url: str,
    ref: str,
    ref_type: str = "tag",
    output_dir: Path | None = None,
) -> Path:
    """
    Download a GitHub repo at a given tag or branch, extract it, and keep only .rst files.

    This is the main function intended to be imported and called from other scripts.

    Parameters
    ----------
    repo_url:
        GitHub repository URL (e.g. "https://github.com/owner/repo").
    ref:
        Tag or branch name (e.g. "v1.0.0" or "main").
    ref_type:
        Either "tag" or "branch". Defaults to "tag".
    output_dir:
        Base directory where the repo will be extracted. If None, uses CWD/"downloads".

    Returns
    -------
    Path
        Path to the extracted root directory that contains only .rst files.
    """
    if output_dir is None:
        output_dir = Path.cwd() / "downloads"

    zip_url = build_github_archive_zip_url(repo_url, ref, ref_type)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip_path = Path(tmpdir) / "repo.zip"
        download_zip(zip_url, tmp_zip_path)
        extracted_root = extract_zip_only_rst(tmp_zip_path, output_dir)

    return extracted_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download a GitHub repo at a given tag or branch as a zip, "
            "extract it into a subfolder, and keep only .rst files."
        )
    )
    parser.add_argument(
        "repo_url",
        help="GitHub repository URL (e.g. https://github.com/owner/repo)",
    )
    parser.add_argument("ref", help="Tag or branch name to download (e.g. v1.0.0 or main)")
    parser.add_argument(
        "--ref-type",
        choices=["tag", "branch"],
        default="tag",
        help="Whether the ref is a tag or a branch (default: tag).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd() / "downloads",
        help="Directory where the repo will be extracted (default: ./downloads)",
    )

    args = parser.parse_args()

    extracted_root = download_github_repo_rst(
        repo_url=args.repo_url,
        ref=args.ref,
        ref_type=args.ref_type,
        output_dir=args.output_dir,
    )

    print(f"Done. .rst files available under: {extracted_root}")


if __name__ == "__main__":
    main()


