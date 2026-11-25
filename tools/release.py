"""Build GitHub Release assets from a checkout."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def build(output, repo):
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "nbeamer.tds.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        tex = ROOT / "tex"
        for file in [tex / "nbeamer.cls", *sorted(tex.glob("nbeamer-*.sty")), *sorted(tex.glob("nbeamer-*.def"))]:
            bundle.write(file, f"tex/latex/nbeamer/{file.name}")
        bundle.write(ROOT / "font-sources.toml", "doc/latex/nbeamer/font-sources.toml")
        bundle.write(ROOT / "fonts/OFL.txt", "doc/latex/nbeamer/OFL.txt")
        bundle.write(ROOT / "texlive-requirements.txt", "doc/latex/nbeamer/texlive-requirements.txt")
        bundle.write(ROOT / "LICENSE", "doc/latex/nbeamer/LICENSE")
        bundle.write(ROOT / "README.md", "doc/latex/nbeamer/README.md")
    (output / "nbeamer.sha256").write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "\n")
    cli = output / "nbeamer"
    cli.write_text((ROOT / "tools/nbeamer").read_text().replace('DEFAULT_REPO = ""', f'DEFAULT_REPO = {repo!r}'))
    cli.chmod(0o755)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".build/dist")
    parser.add_argument("--repo", default="", help="GitHub owner/repo embedded in the release CLI")
    args = parser.parse_args()
    build(args.output, args.repo)
