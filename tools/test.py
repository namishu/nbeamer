"""Run PDF, installation and layout regressions with Python 3.11+ and PyMuPDF."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pymupdf as pdf
from release import ROOT, build

CASES = ROOT / "tests"


def run(command, cwd, env, expected=0):
    result = subprocess.run(command, cwd=cwd, env=env, text=True, errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != expected:
        raise RuntimeError(f"{command} returned {result.returncode} in {cwd}\n{result.stdout[-4000:]}")
    return result.stdout


def compile_case(source, work, env, expected=0, passes=2):
    if source != work / source.name:
        shutil.copyfile(source, work / source.name)
    command = ["xelatex", "-halt-on-error", "-interaction=nonstopmode", source.name]
    output = run(command, work, env, expected)
    if expected == 0:
        for _ in range(1, passes):
            output = run(command, work, env)
    return output


def test_asset(path, width, height):
    with pdf.open() as doc:
        page = doc.new_page(width=width, height=height)
        page.draw_rect(page.rect, color=(0, 0, 0), fill=(.7, .7, .7), width=3)
        page.draw_line((0, 0), (width, height), width=2)
        page.draw_circle((width / 2, height / 2), 5, fill=(1, 1, 1))
        page.get_pixmap().save(path)


def check_layout(work, env, *, code=False):
    """Compare first and subsequent elements across top-aligned containers."""
    table = r"\toprule Marker\\\bottomrule"
    elements = {
        "text": "Marker",
        "verbatim": "\\begin{verbatim}\nMarker\n\\end{verbatim}",
        "itemize": r"\begin{itemize}\item Marker\end{itemize}",
        "enumerate": r"\begin{enumerate}\item Marker\end{enumerate}",
        "block": r"\begin{block}{Marker}Body\end{block}",
        "figure": r"\begin{figure}\includegraphics[width=20mm]{wide.png}\end{figure}",
        "tabular": rf"\begin{{table}}\begin{{tabular}}{{l}}{table}\end{{tabular}}\end{{table}}",
        "tabular*": rf"\begin{{table}}\begin{{tabular*}}{{40mm}}{{l}}{table}\end{{tabular*}}\end{{table}}",
    }
    packages = []
    if code:
        elements = {
            "ncode": "\\begin{ncode}\nMarker\n\\end{ncode}",
        }
        packages.append(r"\usepackage{nbeamer-code}")
    containers = [
        ("", ""),
        (r"\begin{columns}\begin{column}{\linewidth}", r"\end{column}\end{columns}"),
        (r"\begin{minipage}[t]{\linewidth}", r"\end{minipage}"),
    ]
    frames = []
    cases = []
    for kind, content in elements.items():
        for intro in ("", r"Intro\par"):
            for start, end in containers:
                frames.append("\n".join([r"\begin{frame}[fragile]{Layout}", start, intro,
                                         content, end, r"\end{frame}"]))
                cases.append((kind, intro))

    source = work / ("code-layout.tex" if code else "layout.tex")
    source.write_text("\n".join([r"\documentclass[fontset=fandol]{nbeamer}",
                                 *packages, r"\begin{document}",
                                 *frames, r"\end{document}"]))
    compile_case(source, work, env)
    with pdf.open(source.with_suffix(".pdf")) as doc:
        positions = {}
        for page, case in zip(doc, cases, strict=True):
            kind, intro = case
            grid = page.rect.width / 32
            if kind == "figure":
                image, = page.get_image_info()
                y = image["bbox"][1]
            elif kind.startswith("tabular"):
                y = min(path["rect"].y0 - path["width"] / 2 for path in page.get_drawings()
                        if path["rect"].height < .01 and path["rect"].width > grid)
            else:
                y = next(span["origin"][1] for block in page.get_text("dict")["blocks"]
                         for line in block.get("lines", []) for span in line["spans"]
                         if "Marker" in span["text"])
            offset = y - 4 * grid
            if not intro:
                target = 0 if kind in ("figure", "tabular", "tabular*") else .75 * grid
                assert abs(offset - target) < .05, (case, offset, target)
            elif kind in ("text", "ncode", "itemize", "enumerate", "block"):
                assert abs(offset - 2.75 * grid) < .05, (case, offset)
            else:
                assert offset > 1.5 * grid, (case, offset)
            if case in positions:
                assert abs(offset - positions[case]) < .05, (case, offset, positions[case])
            else:
                positions[case] = offset


def check_image_heights(work, env):
    source = work / "image-heights.tex"
    cases = [(4, 8, 8), (4, 4, 6.25), (4, 7, 7), (4, 12, 12),
             (4, 20, 12), (2, 8, 12)]
    frames = []
    for columns, requested, actual in cases:
        frames.append("\n".join([
            r"\begin{frame}{Height}",
            rf"\begin{{nimagegrid}}[rows=1,columns={columns},height={requested}]",
            r"\nimage{wide.png}" * columns, r"\end{nimagegrid}",
            "After" if actual < 12 else "", r"\end{frame}"]))
    def document(body):
        return "\n".join([r"\documentclass[fontset=fandol]{nbeamer}",
                          r"\usepackage{nbeamer-images}", r"\begin{document}",
                          body, r"\end{document}"])
    source.write_text(document("\n".join(frames)))
    log = compile_case(source, work, env)
    for warning in ("height=4 raised", "height=20 limited", "height=8 ignored"):
        assert log.count(warning) == 1, warning
    assert log.count("rows=1, columns=4: valid height=7..12") == 2
    assert "rows=1, columns=2: omit height" in log
    with pdf.open(source.with_suffix(".pdf")) as doc:
        for page, (columns, _, actual) in zip(doc, cases, strict=True):
            grid = page.rect.width / 32
            cells = [d["scissor"] for d in page.get_drawings(extended=True)
                     if d["type"] == "clip" and d["scissor"].width < 14 * grid]
            assert len(cells) == columns
            assert all(abs(cell.y0 / grid - 4) < .005 and
                       abs(cell.height / grid - actual) < .005 for cell in cells)
            if actual < 12:
                after, = page.search_for("After")
                assert cells[0].y1 <= after.y0 < 16 * grid
    for option in ("rows=1", "columns=4"):
        source.write_text(document(frames[0].replace(option + ",", "")))
        assert "Missing required option " + option.split("=")[0] in compile_case(
            source, work, env, expected=1)
    for key, old, invalid in (("height", 8, "1.5"), ("columns", 4, "2.5"), ("rows", 1, "abc")):
        source.write_text(document(frames[0].replace(f"{key}={old}", f"{key}={invalid}")))
        assert f"positive integer for {key}" in compile_case(source, work, env, expected=1)



def check_code(work, env):
    compile_case(CASES / "code/code.tex", work, env)
    with pdf.open(work / "code.pdf") as doc:
        assert len(doc) == 3
        def body_lines(page):
            # The fixture uses one titled frame per page. Exclude its heading.
            grid = page.rect.width / 32
            return [line for block in page.get_text("dict")["blocks"]
                    for line in block.get("lines", []) if line["bbox"][1] >= 4 * grid]

        def line_text(line):
            return "".join(span["text"] for span in line["spans"])

        def check_row(line, row, grid):
            for span in line["spans"]:
                assert abs(span["origin"][1] - row * grid) < .05, (span["text"], row)

        page = doc[0]
        grid = page.rect.width / 32
        lines = body_lines(page)
        assert [line_text(line) for line in lines] == [r"Before \alpha{X} { after.", "First", "Last", "After"]
        for line, row in zip(lines, (4.75, 6.75, 8.75, 10.75), strict=True):
            check_row(line, row, grid)

        page = doc[1]
        grid = page.rect.width / 32
        marker, *wrapped, after = body_lines(page)
        assert line_text(marker) == "Marker" and line_text(after) == "After"
        check_row(marker, 4.75, grid)
        assert len(wrapped) > 1
        assert " ".join(map(line_text, wrapped)) == "First word word word word Last"
        # The six-grid column ends at the right body margin, two grids from the edge.
        right = page.rect.width - 2 * grid
        for index, line in enumerate(wrapped):
            check_row(line, 4.75 + index, grid)
            assert right - 6 * grid - .05 <= line["bbox"][0] < line["bbox"][2] <= right + .05, line
        check_row(after, 4.75 + len(wrapped) + 1, grid)

        page = doc[2]
        grid = page.rect.width / 32
        definition, statement = body_lines(page)
        assert line_text(definition) == "def twice(x):" and line_text(statement) == "return 2 * x"
        check_row(definition, 4.75, grid)
        check_row(statement, 5.75, grid)
        keyword = definition["spans"][0]
        function = definition["spans"][-1]
        assert function["color"] == 0xff0000, function
        returned = statement["spans"][0]
        for span, token in ((keyword, "def"), (returned, "return")):
            assert span["text"] == token and span["flags"] & pdf.TEXT_FONT_BOLD, span
        assert function["text"] == "twice(x):" and not function["flags"] & pdf.TEXT_FONT_BOLD, function
        advance = (function["bbox"][2] - function["bbox"][0]) / len(function["text"])
        indent = returned["origin"][0] - keyword["origin"][0]
        assert abs(indent - 4 * advance) < .05, (indent, advance)


def check_rhythm(work, env):
    compile_case(CASES / "core/rhythm.tex", work, env)
    with pdf.open(work / "rhythm.pdf") as doc:
        for page, columns in zip(doc, (1, 2, 1, 2, 1), strict=True):
            grid = page.rect.width / 32
            spans = [span for block in page.get_text("dict")["blocks"]
                     for line in block.get("lines", []) for span in line["spans"]]
            rows = [sorted(span["origin"] for span in spans if span["text"] == word)
                    for word in ("Item", "Alpha", "Beta", "Gamma")]
            assert all(len(row) == columns for row in rows)
            for (_, item), (_, first), (_, wrapped), (_, paragraph) in zip(*rows):
                assert abs(item - 4.75 * grid) < .05, page.number
                assert abs(first - item - 2 * grid) < .05, page.number
                assert abs(wrapped - first - grid) < .05, page.number
                assert abs(paragraph - wrapped - 2 * grid) < .05, page.number


def check_boundaries(work, env):
    compile_case(CASES / "core/boundaries.tex", work, env)
    with pdf.open(work / "boundaries.pdf") as doc:
        assert len(doc) == 16
        for page in doc:
            grid = page.rect.width / 32
            y = {span["text"].strip(): span["origin"][1] for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", []) for span in line["spans"]}
            if 4 <= page.number < 10:  # Named block, alertblock and exampleblock, each in two positions.
                assert abs(y["Title."] - y["First"]) < .05, (page.number, y)
            pairs = [("Inside", "Outside")]
            if 4 <= page.number < 14:  # Blocks and proofs contain an explicit first paragraph.
                pairs.append(("First", "Inside"))
            if page.number >= 14:  # Nested lists must retain both items.
                pairs.extend([("Outer", "Inner"), ("Inner", "Inside")])
            for above, below in pairs:
                gap = (y[below] - y[above]) / grid
                assert abs(gap - 2) < .005, (page.number + 1, above, below, gap)


def check_container_exits(work, env):
    compile_case(CASES / "core/container-exits.tex", work, env)
    with pdf.open(work / "container-exits.pdf") as doc:
        for page, expected in zip(doc, [2]*9 + [3] + [2]*5, strict=True):
            grid = page.rect.width / 32
            spans = [span for block in page.get_text("dict")["blocks"]
                     for line in block["lines"] for span in line["spans"]]
            def baseline(word):
                return next(s["origin"][1] for s in spans if word in s["text"])
            gap = (baseline("Next") - baseline("Last")) / grid
            assert abs(gap - expected) < .005, (page.number + 1, gap)


def check_container_heights(work, env):
    compile_case(CASES / "core/container-heights.tex", work, env)
    with pdf.open(work / "container-heights.pdf") as doc:
        assert len(doc) == 11
        rows = []
        for page in doc:
            grid = page.rect.width / 32
            rows.append({span["text"].strip(): span["origin"][1] / grid
                         for block in page.get_text("dict")["blocks"]
                         for line in block["lines"] for span in line["spans"]})
        # A changed fixed height, or a taller picture, moves the following
        # paragraph by precisely that amount, including fractional grid units.
        for first, increase in ((0, 1.5), (2, 1.5), (4, .75)):
            assert abs(rows[first+1]["Next"] - rows[first]["Next"] - increase) < .005
        for row in rows[4:6]:
            assert abs(row["Next"] - row["Caption"] - 2) < .005
        assert abs(rows[6]["Side"] - rows[6]["Middle"]) < .02
        assert abs(rows[7]["Side"] - rows[7]["Last"]) < .005
        for row in rows[8:]:
            assert abs(row["Beside"] - row["First"]) < .005
        for row in rows[9:]:
            assert abs(row["Next"] - rows[8]["Next"]) < .005


def check_pages(work, env):
    # The populated contents page changes subsequent PGF picture IDs on pass two.
    compile_case(CASES / "core/pages.tex", work, env, passes=3)
    with pdf.open(work / "pages.pdf") as doc:
        assert len(doc) == 4
        cover = doc[0]
        grid = cover.rect.width / 32
        # The cover diagram in docs/design places each field in a grid band.
        for marker, top, bottom in (("TitleMarker", 3, 7), ("SecondaryMarker", 7, 9),
                                    ("AuthorMarker", 11, 13), ("InstituteMarker", 13, 14)):
            box, = cover.search_for(marker)
            assert abs(box.x0 - 3 * grid) < .05, (marker, box)
            assert top * grid <= box.y0 < box.y1 <= bottom * grid, (marker, box)
        date, = [pdf.Rect(word[:4]) for word in cover.get_text("words")
                 if word[4].replace("‑", "-") == "2026-11-25"]
        assert abs(date.x1 - 29 * grid) < .05 and 15 * grid <= date.y0 < date.y1 <= 16 * grid, date
        contents, section = doc[1], doc[2]
        heading, first = sorted(contents.search_for("Section1"), key=lambda box: box.x0)
        section_heading, = section.search_for("Section1")
        assert max(abs(a-b) for a, b in zip(heading, section_heading)) < .05
        # Text boxes can have different glyph heights. Compare baseline origins.
        entries = [span for block in contents.get_text("dict")["blocks"]
                   for line in block["lines"] for span in line["spans"]
                   if span["origin"][0] >= first.x0 - .05]
        entries.sort(key=lambda span: span["origin"][1])
        assert [span["text"] for span in entries] == ["Section1", "Section2", "Section3", "Section4", "Section5"]
        assert not contents.search_for("Section6")
        for previous, current in zip(entries, entries[1:]):
            assert abs(current["origin"][1] - previous["origin"][1] - 2 * grid) < .1


def check_navigation_width(work, env):
    log = compile_case(CASES / "core/navigation-width.tex", work, env, passes=3)
    for field in ("Contents heading", "Contents entry", "Section heading"):
        assert log.count(field + " exceeds its line width") == 1, field
    with pdf.open(work / "navigation-width.pdf") as doc:
        for page, bounds in zip(doc, (((3, 12), (15, 29)), ((3, 29),)), strict=True):
            grid = page.rect.width / 32
            clips = [path["scissor"] for path in page.get_drawings(extended=True)
                     if path["type"] == "clip"]
            for left, right in bounds:
                assert any(abs(box.x0 - left * grid) < .05 and abs(box.x1 - right * grid) < .05
                           for box in clips), (bounds, clips)


def check_geometry(work, env):
    compile_case(CASES / "core/geometry.tex", work, env)
    with pdf.open(work / "geometry.pdf") as doc:
        assert len(doc) == 4
        for page in doc:
            grid = page.rect.width / 32
            assert abs(page.rect.height - 18 * grid) < .05
            top = (2 if page.number == 0 else 4) * grid
            coords = doc.xref_get_key(page.xref, "NBeamerBody")[1]
            bounds = tuple(map(float, coords.strip("[]").split()))
            for actual, expected in zip(bounds, (2*grid, 2*grid, 30*grid, page.rect.height-top), strict=True):
                assert abs(actual - expected) < .05
            marker, = [span for block in page.get_text("dict")["blocks"]
                       for line in block.get("lines", []) for span in line["spans"]
                       if span["text"] == "Marker"]
            assert abs(marker["origin"][1] - top - .75*grid) < .05

        image, = doc[2].get_image_info()
        left, top = image["bbox"][:2]
        assert abs(left - 2*grid) < .05 and abs(top - 4*grid) < .05
        rules = [path["rect"] for path in doc[3].get_drawings()
                 if path["rect"].height < .01 and path["rect"].width > grid]
        assert len(rules) == 3
        column_width = .30 * (doc[3].rect.width - 4*grid)
        caption, = doc[3].search_for("Caption")
        for rule in rules:
            assert abs(rule.x0 - left) < .05 and abs(rule.width - column_width) < .05
            assert abs((caption.x0 + caption.x1 - rule.x0 - rule.x1) / 2) < .05


def check_margins(work, env):
    compile_case(CASES / "core/margins.tex", work, env, passes=3)
    with pdf.open(work / "margins.pdf") as doc:
        assert len(doc) == 7
        baselines = []
        for page in doc.pages(0, 6):
            grid = page.rect.width / 32
            has_grid = any(path["rect"].width > 31 * grid and
                           abs((path["width"] or 0) - .2) < .02 for path in page.get_drawings())
            assert has_grid == (page.number != 1), page.number
            top = (4 if page.number < 3 else 2) * grid
            left, right = grid, page.rect.width - 4 * grid
            coords = doc.xref_get_key(page.xref, "NBeamerBody")[1]
            for actual, expected in zip(map(float, coords.strip("[]").split()),
                                        (left, 2*grid, right, page.rect.height-top), strict=True):
                assert abs(actual - expected) < .05, (page.number, actual, expected)
            bounds = pdf.Rect(left, top, right, page.rect.height-2*grid)
            assert any(max(abs(a-b) for a, b in zip(path["rect"], bounds)) < .05
                       for path in page.get_drawings()), page.number
            spans = {span["text"].strip(): span for block in page.get_text("dict")["blocks"]
                     for line in block["lines"] for span in line["spans"]}
            assert abs(spans["Left"]["origin"][0] - left) < .05
            assert abs(spans["Right"]["bbox"][2] - right) < .5
            if page.number < 3:
                title, = page.search_for("Alignment")
                assert abs(title.x0 - left) < .05, (page.number, title, left)
            if page.number == 1:
                clips = [path["scissor"] for path in page.get_drawings(extended=True)
                         if path["type"] == "clip" and path["scissor"].y1 < top]
                assert any(abs(box.x0 - left) < .05 and abs(box.x1 - right) < .05 for box in clips), clips
            baselines.append(spans["Left"]["origin"][1])
        for group, top in ((baselines[:3], 4*grid), (baselines[3:], 2*grid)):
            first, center, bottom = group
            assert abs(first - top - .75*grid) < .05
            assert first + 2*grid < center < bottom - 2*grid

        # Four internal dividers end one grid inside the effective right edge.
        dividers = [path["rect"] for path in doc[6].get_drawings()
                    if path["rect"].height < .01 and path["rect"].width > grid]
        assert len(dividers) == 4
        for divider in dividers:
            assert abs(divider.x0 - (left + 12*grid)) < .05
            assert abs(divider.x1 - (right - grid)) < .05


def check_truncation(work, env):
    for fixture, warnings, widths in (
        ("core/title-width.tex", {"Cover title": 1, "Frame title": 1}, (26, 28)),
        ("images/caption-width.tex", {"Image caption 1": 2}, (12.5, 5)),
    ):
        source = CASES / fixture
        log = compile_case(source, work, env)
        assert log.count("exceeds its line width") == sum(warnings.values()), log
        if fixture.startswith("core/"):
            assert log.count("Frame subtitle ignored") == 2
        for field, count in warnings.items():
            assert log.count(field + " exceeds its line width") == count, field
        with pdf.open(work / source.with_suffix(".pdf").name) as doc:
            for index, units in enumerate(widths):
                page = doc[index]
                grid = page.rect.width / 32
                vertical = fixture.startswith("images/") and index == 1
                clips = [d["scissor"] for d in page.get_drawings(extended=True)
                         if d["type"] == "clip"]
                field, = [r for r in clips if abs((r.height if vertical else r.width) - units * grid) < .05
                          and (r.width if vertical else r.height) < 2 * grid]
                # Read just the visible field. Its prefix fits on one line and its suffix is clipped.
                lines = [line for block in page.get_text("dict", clip=field + (-.1, -.1, .1, .1))["blocks"]
                         for line in block.get("lines", [])]
                line, = lines
                visible = "".join(span["text"] for span in line["spans"])
                assert visible.startswith("Start WWWW"), visible
                # Inspect the whole rendered page: restricting extraction to the field
                # alone could hide an overflowing suffix from the test itself.
                pixels = page.get_pixmap(matrix=pdf.Matrix(2, 2), colorspace=pdf.csRGB).samples
                assert not any(r > g + 64 for r, g in zip(pixels[0::3], pixels[1::3])), (fixture, index)
            assert len(doc) == (2 if fixture.startswith("images/") else 4)
            if fixture.startswith("core/"):
                assert "Hidden" not in doc[3].get_text()
            short_pages = doc if fixture.startswith("images/") else doc.pages(2, 4)
            for page in short_pages:
                assert page.search_for("Short"), page.number


def check_image_grids(work, env, check):
    compile_case(CASES / "images/grids.tex", work, env)
    run([*check, "grids.pdf"], work, env)
    with pdf.open(work / "grids.pdf") as doc:
        for page, (rows, columns) in zip(doc, ((1, 2), (2, 2), (2, 4), (2, 3)), strict=True):
            images = page.get_image_info()
            assert len(images) == rows * columns
            body = doc.xref_get_key(page.xref, "NBeamerBody")[1]
            coords = list(map(float, body.strip("[]").split()))
            grid = page.rect.width / 32
            expected = [2*grid, 2*grid, 30*grid, page.rect.height-(2 if page.number == 2 else 4)*grid]
            assert all(abs(a-b) < .03 for a, b in zip(coords, expected, strict=True))
            # An auto-height grid spans the body. Cells are uniform, ordered
            # left-to-right and top-to-bottom, with space between neighbours.
            cells = [path["scissor"] for path in page.get_drawings(extended=True)
                     if path["type"] == "clip" and path["scissor"].width < 28 * grid - .05]
            assert len(cells) == len(images)
            body_top = (2 if page.number == 2 else 4) * grid
            gap = (1 if columns == 4 else 2) * grid
            width = (28 * grid - (columns - 1) * gap) / columns
            height = (page.rect.height - 2 * grid - body_top - (rows - 1) * grid) / rows
            dx, dy = width + gap, height + grid
            for i, (cell, image) in enumerate(zip(cells, images, strict=True)):
                row, col = divmod(i, columns)
                x, y = 2 * grid + col * dx, body_top + row * dy
                target = (x, y, x + width, y + height)
                assert max(abs(a-b) for a, b in zip(cell, target)) < .05, (i, cell, target)
                # The alternating wide and tall inputs must cover their own cell.
                iw, ih = (120, 30) if i % 2 == 0 else (30, 120)
                assert (image["width"], image["height"]) == (iw, ih)
                scale = max(width / iw, height / ih)
                box = pdf.Rect(image["bbox"])
                assert abs(box.width - iw * scale) < .05 and abs(box.height - ih * scale) < .05
                assert abs((box.x0 + box.x1 - cell.x0 - cell.x1) / 2) < .1
                assert abs((box.y0 + box.y1 - cell.y0 - cell.y1) / 2) < .1
        captions = [span for block in doc[3].get_text("dict")["blocks"]
                    for line in block.get("lines", []) for span in line["spans"]
                    if span["text"] in ("Wide", "Tall")]
        captions.sort(key=lambda span: span["bbox"][0])
        assert [span["text"] for span in captions] == ["Wide", "Tall"]
        labels = [d["rect"] for d in doc[3].get_drawings()
                  if abs((d.get("fill_opacity") or 0) - .8) < .001]
        assert len(labels) == 2
        for col, (label, caption) in enumerate(zip(sorted(labels, key=lambda r: r.x0), captions, strict=True)):
            # The first two cells are eight grids wide with a two-grid gutter.
            assert abs((label.x0 + label.x1) / 2 - (6 + 10 * col) * grid) < .05
            assert label.contains(pdf.Rect(caption["bbox"])), (caption["text"], label)
            assert abs((label.y0 + label.y1) / 2 - 8.5 * grid) < .05
            assert label.y0 >= 4 * grid and label.y1 <= 9.5 * grid
    assert "capacity exceeded" in compile_case(CASES / "images/capacity.tex", work, env, expected=1)


def test(work):
    tree = work / "texmf"
    dist = work / "dist"
    build(dist, "test/nbeamer")
    env = dict(os.environ, TEXMFHOME=str(tree), TEXINPUTS="")
    cli = [sys.executable, str(dist / "nbeamer")]
    options = ["--from-dir", str(dist), "--texmfhome", str(tree)]
    run(cli + ["install", "--no-deps", "--no-fonts", *options], work, env)
    assert Path(run(["kpsewhich", "nbeamer.cls"], work, env).strip()).is_relative_to(tree)
    test_asset(work / "wide.png", 120, 30)
    test_asset(work / "tall.png", 30, 120)
    check_truncation(work, env)
    check_image_heights(work, env)
    check_code(work, env)
    check_layout(work, env, code=True)
    check_rhythm(work, env)
    check_boundaries(work, env)
    check_container_exits(work, env)
    check_container_heights(work, env)
    check_layout(work, env)
    check = [sys.executable, str(ROOT / "tools/check_bounds.py"), "--strict"]
    run([*check, "code.pdf"], work, env)
    check_image_grids(work, env, check)
    compile_case(CASES / "core/overlay.tex", work, env)
    with pdf.open(work / "overlay.pdf") as doc:
        assert len(doc) == 2
        first, = doc[1].search_for("First line.")
        second, = doc[1].search_for("Second line.")
        def pixels(page, box):
            return page.get_pixmap(matrix=pdf.Matrix(3, 3), colorspace=pdf.csGRAY, clip=box).samples
        before, after = (pixels(page, first) for page in doc)
        assert min(before) < 128 and before == after, "First line moved or disappeared"
        assert min(pixels(doc[0], second)) == 255 and min(pixels(doc[1], second)) < 128, "Reveal failed"
    # Identical out-of-bounds ink is hidden on step one and visible on step two.
    overlay_log = run([*check, "overlay.pdf"], work, env, expected=1)
    overflow, = [line for line in overlay_log.splitlines() if "body clipped:" in line]
    assert "page 2, frame 1" in overflow and "body clipped: right" in overflow, overflow
    compile_case(CASES / "core/overflow.tex", work, env)
    assert "body clipped: right" in run([*check, "overflow.pdf"], work, env, expected=1)

    # Test font selection in a project unrelated to the source or install tree.
    fontdir = ROOT / "fonts"
    names = ["LXGWWenKai-Light.ttf", "LXGWWenKai-Medium.ttf"]
    paths = []
    for name in names:
        local = fontdir / name
        paths.append(local if local.exists() else Path(subprocess.check_output(["kpsewhich", name], text=True).strip()))
    local_fonts = work / "fonts"
    local_fonts.mkdir()
    shutil.copy(paths[0], local_fonts)
    sample = r"""\documentclass{nbeamer}
\begin{document}
\begin{frame}
字体
\end{frame}
\end{document}
"""
    source = work / "font.tex"
    source.write_text(sample)
    command = ["xelatex", "-halt-on-error", "-interaction=batchmode", source.name]
    def check_font(expected):
        run(command, work, env)
        with pdf.open(source.with_suffix(".pdf")) as doc:
            spans = [s for block in doc[0].get_text("dict")["blocks"]
                     for line in block["lines"] for s in line["spans"] if "字体" in s["text"]]
            span, = spans
            assert expected in span["font"], (expected, span)

    check_font("FandolHei")
    installed = tree / "fonts/truetype/nbeamer"
    installed.mkdir(parents=True)
    for path in paths:
        shutil.copy(path, installed)
    shutil.rmtree(local_fonts)
    stamps = {p.name: p.stat().st_mtime_ns for p in installed.iterdir()}
    run(cli + ["update", *options], work, env)
    assert stamps == {p.name: p.stat().st_mtime_ns for p in installed.iterdir()}
    check_font("WenKai")
    # A corrupt update must fail before publishing any files.
    package = tree / "tex/latex/nbeamer"
    # Distinguish the installed copy from the archive so an early overwrite is observable.
    cls = package / "nbeamer.cls"
    cls.write_bytes(cls.read_bytes() + b"\n% local test marker\n")
    before_update = {p.relative_to(tree): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    checksum = dist / "nbeamer.sha256"
    checksum.write_text("0" * 64)
    assert "Checksum mismatch" in run(cli + ["update", *options], work, env, expected=1)
    assert before_update == {p.relative_to(tree): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    source.write_text(sample.replace("{nbeamer}", "[fontset=custom]{nbeamer}\n"
        r"\setCJKsansfont{FandolSong-Regular.otf}"))
    check_font("FandolSong")
    shutil.copytree(ROOT / "docs/nbeamer/figures", work / "figures")
    core_example = ROOT / "docs/nbeamer/nbeamer.tex"
    compile_case(core_example, work, env)
    run([*check, "nbeamer.pdf"], work, env)
    check_pages(work, env)
    check_navigation_width(work, env)
    check_geometry(work, env)
    compile_case(CASES / "core/column-widths.tex", work, env)
    check_margins(work, env)

    remove = cli + ["uninstall", "--texmfhome", str(tree)]
    run(remove + ["--fonts-only"], work, env)
    assert not installed.exists()
    assert cls.is_file()
    extra = package / "my-theme.sty"
    extra.write_text("% user file")
    installed.mkdir()
    for path in paths:
        shutil.copy(path, installed)
    run(remove, work, env)
    run(remove, work, env)
    assert list(package.iterdir()) == [extra]
    assert not installed.exists() and not (tree / "doc/latex/nbeamer").exists()
    assert extra.read_text() == "% user file"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if not __debug__:
        parser.error("The regression suite requires Python assertions. Disable optimized mode.")
    parent = ROOT / ".build/tests"
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=parent))
    test(work)
    print(f"Passed. test artifacts: {work}")
