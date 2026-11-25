<h1 align="center">nbeamer</h1>

<p align="center">Black-and-white slides for talks in Chinese and English.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="Installer: Python 3.11+">
  <img src="https://img.shields.io/badge/TeX_Live-2026-008080?style=flat" alt="TeX Live 2026">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22A06B?style=flat" alt="MIT License"></a>
</p>

<p align="center"><strong>English</strong> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center">
  <a href="#documentation">Documentation</a> · <a href="#install">Install</a> ·
  <a href="#locate-installed-files">Locate files</a> · <a href="#uninstall">Uninstall</a>
</p>

---

## Documentation

- [User guide (PDF)](docs/nbeamer/nbeamer.pdf)
- [Code listings (PDF)](docs/nbeamer-code/nbeamer-code.pdf)
- [Image grids (PDF)](docs/nbeamer-images/nbeamer-images.pdf)
- [Layout design (PDF)](docs/design/design.pdf)

## Install

The installer requires **Python 3.11 or later**. Compile slides with **XeLaTeX**. Your TeX installation should include `latexmk`, Beamer, xeCJK, TikZ, listings, Latin Modern, and Fandol.

Download the **`nbeamer` installer** from this project's GitHub Releases. In the download folder, run the command for your platform. It installs the class, both extensions, and the Light and Medium weights of LXGW WenKai into your personal TeX tree.

| Platform | Command |
|---|---|
| macOS or Linux | `python3 nbeamer install` |
| Windows (PowerShell) | `py -3 nbeamer install` |

The installer checks the [TeX Live dependencies](texlive-requirements.txt) and installs missing packages from your configured repository. If this fails, installation stops. It also checks WenKai against the version specified by the release. If the fonts cannot be installed, the template remains available with Fandol. The installer prints the installed paths.

Use `--no-fonts` to skip WenKai. If your system package manager supplies the TeX dependencies, use `--no-deps`. On Windows, replace `python3` below with `py -3`.

**Offline installation.** Download the installer and run this command in its folder:

```sh
python3 nbeamer install --no-deps --no-fonts
```

## Compile slides

To compile the guide from its editable source, run this command at the repository root. The result is `docs/nbeamer/nbeamer.pdf`, alongside its source.

```sh
latexmk -xelatex docs/nbeamer/nbeamer.tex
```

For your own presentation, run `latexmk -xelatex main.tex` in the folder containing your slides. To preview changes as you save, use `latexmk -xelatex -pvc main.tex`.

## Locate installed files

These commands work across TeX Live platforms. The first prints your personal TeX root. The others print the full paths of the class and optional WenKai font that TeX finds. Run them from your presentation folder to see which copy it will use.

```sh
kpsewhich -var-value=TEXMFHOME
kpsewhich nbeamer.cls
kpsewhich LXGWWenKai-Light.ttf
```

Under the installation root, `tex/latex/nbeamer/` holds the class and extensions, `fonts/truetype/nbeamer/` holds the optional fonts, and `doc/latex/nbeamer/` holds the README, font manifest, and font license.

## Update

Run these commands from the folder containing the installer.

| Goal | Command |
|---|---|
| Update the template and extensions; keep installed fonts | `python3 nbeamer update` |
| Also check the fonts and download them if needed | `python3 nbeamer update --fonts` |
| Install a specific release (replace `vX.Y.Z` with its tag) | `python3 nbeamer install --version vX.Y.Z` |

## Uninstall

```sh
python3 nbeamer uninstall
```

This removes nbeamer's class, extensions, documentation, and WenKai fonts from the personal TeX tree. Your presentations and PDFs stay in their folders. Shared TeX Live packages stay installed. If you installed with `--texmfhome DIR`, supply the same option when updating or uninstalling. You can then delete the downloaded installer and archives.
