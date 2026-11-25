<h1 align="center">nbeamer</h1>

<p align="center">适合中英文演讲的黑白幻灯片模板。</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="安装器需要 Python 3.11 或更高版本">
  <img src="https://img.shields.io/badge/TeX_Live-2026-008080?style=flat" alt="TeX Live 2026">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22A06B?style=flat" alt="MIT License"></a>
</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

<p align="center">
  <a href="#文档">文档</a> · <a href="#安装">安装</a> ·
  <a href="#查询安装位置">查询安装位置</a> · <a href="#卸载">卸载</a>
</p>

---

## 文档

- [使用手册（PDF）](docs/nbeamer/nbeamer.pdf)
- [代码排版手册（PDF）](docs/nbeamer-code/nbeamer-code.pdf)
- [图片网格手册（PDF）](docs/nbeamer-images/nbeamer-images.pdf)
- [版面设计说明（PDF）](docs/design/design.pdf)

## 安装

安装器需要 **Python 3.11 或更高版本**。讲稿使用 **XeLaTeX** 编译。TeX 环境需包含 `latexmk`、Beamer、xeCJK、TikZ、listings、Latin Modern 和 Fandol。

从项目的 GitHub Releases 下载名为 **`nbeamer`** 的安装器。在下载目录中执行对应命令，即可把核心模板、两个扩展和霞鹜文楷的 Light、Medium 字重装到当前用户的 TeX 目录。

| 平台 | 安装命令 |
|---|---|
| macOS 或 Linux | `python3 nbeamer install` |
| Windows（PowerShell） | `py -3 nbeamer install` |

安装器先检查 [TeX Live 依赖](texlive-requirements.txt)，从当前配置的仓库补齐缺少的包；依赖失败时停止安装。霞鹜文楷按所选发布版指定的版本校验，字体安装失败时会给出警告，模板仍可使用 Fandol。完成后会显示实际安装路径。

只用 TeX 自带字体时加 `--no-fonts`。如果已用系统包管理器配好 TeX 依赖，可加 `--no-deps`。Windows 用户可将下文的 `python3` 换成 `py -3`。

**离线安装。** 下载安装器，在所在目录运行以下命令即可安装模板和扩展。

```sh
python3 nbeamer install --no-deps --no-fonts
```

## 编译讲稿

手册源文件也是一份可编译的示例。从仓库根目录运行：生成的 `docs/nbeamer/nbeamer.pdf` 就在源文件旁边。

```sh
latexmk -xelatex docs/nbeamer/nbeamer.tex
```

编译自己的讲稿时，进入主文件所在目录，运行 `latexmk -xelatex main.tex`。如果希望保存后自动重新编译并预览，使用 `latexmk -xelatex -pvc main.tex`。

## 查询安装位置

以下命令适用于各平台的 TeX Live。第一条显示个人 TeX 根目录，后两条分别查询模板和可选的霞鹜文楷字体。在讲稿目录中执行，就能看到这份讲稿实际使用的文件路径。

```sh
kpsewhich -var-value=TEXMFHOME
kpsewhich nbeamer.cls
kpsewhich LXGWWenKai-Light.ttf
```

安装根目录下，`tex/latex/nbeamer/` 存放核心模板和扩展，`fonts/truetype/nbeamer/` 存放可选字体，`doc/latex/nbeamer/` 存放使用说明、字体清单和字体许可证。

## 更新

在安装器所在目录执行对应命令。

| 用途 | 命令 |
|---|---|
| 更新模板和扩展，保留已安装的字体 | `python3 nbeamer update` |
| 同时检查字体，按需下载 | `python3 nbeamer update --fonts` |
| 安装指定版本（将 `vX.Y.Z` 换成发布标签） | `python3 nbeamer install --version vX.Y.Z` |

## 卸载

```sh
python3 nbeamer uninstall
```

这会移除个人 TeX 目录中的 nbeamer 模板、扩展、说明文件和霞鹜文楷。你的讲稿和 PDF 会留在原处。共享的 TeX Live 宏包会保留。如果安装时指定过 `--texmfhome DIR`，更新和卸载时也传入相同路径。卸载后可以直接删除下载的安装器和压缩包。
