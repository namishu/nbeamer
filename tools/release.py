"""Build GitHub Release assets from a checkout."""
import argparse
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def build(output, repo):
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output, delete=False) as temp:
        temp.write(b"#!/usr/bin/env python3\n")
        installer = Path(temp.name)
    with ZipFile(installer, "a", ZIP_DEFLATED) as bundle:
        main = (ROOT / "tools/nbeamer").read_text().replace('DEFAULT_REPO = ""', f'DEFAULT_REPO = {repo!r}')
        bundle.writestr("__main__.py", main)
        tex = ROOT / "tex"
        for file in [tex / "nbeamer.cls", *sorted(tex.glob("nbeamer-*.sty")), *sorted(tex.glob("nbeamer-*.def"))]:
            bundle.write(file, f"tex/latex/nbeamer/{file.name}")
        bundle.write(ROOT / "font-sources.toml", "doc/latex/nbeamer/font-sources.toml")
        bundle.write(ROOT / "fonts/OFL.txt", "doc/latex/nbeamer/OFL.txt")
        bundle.write(ROOT / "texlive-requirements.txt", "doc/latex/nbeamer/texlive-requirements.txt")
        bundle.write(ROOT / "LICENSE", "doc/latex/nbeamer/LICENSE")
        bundle.write(ROOT / "README.md", "doc/latex/nbeamer/README.md")
    installer.chmod(0o755)
    installer.replace(output / "nbeamer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".build/dist")
    parser.add_argument("--repo", default="", help="GitHub owner/repo embedded in the release CLI")
    args = parser.parse_args()
    build(args.output, args.repo)
