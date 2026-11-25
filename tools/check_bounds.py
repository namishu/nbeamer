"""Report ink outside nbeamer body rectangles without modifying the PDF on disk."""
# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.25,<2"]
# ///
import math
import os
import shutil
import re
import sys

try:
    import pymupdf as pdf
except ModuleNotFoundError:
    if shutil.which("uv"):
        os.execvp("uv", ["uv", "run", "--script", __file__, *sys.argv[1:]])
    sys.exit("nbeamer: PDF bounds checking requires PyMuPDF (python3 -m pip install pymupdf) or uv.")


NUMBER = rb"(-?[\d.]+)"
BODY_START = re.compile(rb"/NBeamerBody\s+BMC\s+" + rb"\s+".join([NUMBER] * 4) + rb"\s+re\s+W\s+n\b")
BODY_END = re.compile(rb"\bEMC\s+Q\s+/NBeamerBodyEnd\s+MP\b")
# Inspect at eight samples per PDF point; allow one sample for edge antialiasing.
SCALE = 8
TILE = 64


def ink_bounds(pixmap):
    """Bounding box of painted pixels, including white ink on transparency."""
    alpha = pixmap.samples[1::2]  # DeviceGray + alpha
    if not alpha.strip(b"\0"):
        return None
    w = pixmap.width
    left, top, right, bottom = w, pixmap.height, 0, 0
    for y in range(pixmap.height):
        row = alpha[y*w:(y+1)*w]
        end = len(row.rstrip(b"\0"))
        if end:
            left = min(left, w-len(row.lstrip(b"\0")))
            right = max(right, end)
            top, bottom = min(top, y), y+1
    return pdf.Rect((pixmap.x+left)/SCALE, (pixmap.y+top)/SCALE,
                    (pixmap.x+right)/SCALE, (pixmap.y+bottom)/SCALE)


def body_overflow(page, bounds):
    doc = page.parent
    stream = page.read_contents()
    start = BODY_START.search(stream)
    end = BODY_END.search(stream, start.end()) if start else None
    if not end:
        raise ValueError(f"missing body boundary on page {page.number+1}")
    x, y, _, _ = map(float, start.groups())
    # Replay only the body in its original DVI coordinate system, retaining
    # internal image transforms, nested clipping, transparency and font resources.
    origin = f"q 1 0 0 1 {bounds.x0-x:.6f} {bounds.y0-y:.6f} cm\n".encode()
    ref = doc.get_new_xref()
    doc.update_object(ref, "<<>>")
    body = stream[start.end():end.start()]
    body = body.replace(b"/NBeamerHidden BMC", b"q 0 0 0 0 re W n")
    body = body.replace(b"EMC /NBeamerHiddenEnd MP", b"Q")
    doc.update_stream(ref, origin + body + b"\nQ")
    page.set_contents(ref)
    # Include off-paper marks as well. TeX dimensions are bounded by 16384 pt.
    page.set_mediabox(pdf.Rect(-32768, -32768, 32768, 32768))
    limit = bounds * page.transformation_matrix
    display = page.get_displaylist(annots=False)
    tiles = set()
    # The fast PDF bounds are conservative. Rasterize only suspect tiles,
    # so an internal clip or a glyph's loose bounding box cannot cause a warning.
    for kind, box in page.get_bboxlog():
        rect = pdf.Rect(box) & page.rect
        if kind == "ignore-text" or rect.is_empty or limit.contains(rect):
            continue
        for ty in range(math.floor(rect.y0/TILE), math.ceil(rect.y1/TILE)):
            for tx in range(math.floor(rect.x0/TILE), math.ceil(rect.x1/TILE)):
                tiles.add((tx, ty))
    distances = [0.] * 4
    for tx, ty in tiles:
        tile = pdf.Rect(tx*TILE, ty*TILE, (tx+1)*TILE, (ty+1)*TILE)
        if limit.contains(tile):
            continue
        pix = display.get_pixmap(matrix=pdf.Matrix(SCALE, SCALE), colorspace=pdf.csGRAY,
                                 alpha=True, clip=tile)
        box = ink_bounds(pix)
        if box:
            for i, distance in enumerate((limit.x0-box.x0, box.x1-limit.x1,
                                          limit.y0-box.y0, box.y1-limit.y1)):
                distances[i] = max(distances[i], distance)
    return [(side, delta) for side, delta in zip(("left", "right", "top", "bottom"), distances)
            if delta > 1/SCALE]


def main(path):
    clipped = False
    with pdf.open(path) as doc:
        for page in doc:
            kind, value = doc.xref_get_key(page.xref, "NBeamerBody")
            if kind != "array":
                continue
            bounds = pdf.Rect(*map(float, value.strip("[]").split()))
            frame = doc.xref_get_key(page.xref, "NBeamerFrame")[1]
            title = doc.xref_get_key(page.xref, "NBeamerTitle")[1]
            excess = body_overflow(page, bounds)
            if excess:
                clipped = True
                detail = ", ".join(f"{side} {d*25.4/72:.2f} mm" for side, d in excess)
                print(f"Class nbeamer Warning: page {page.number+1}, frame {frame} "
                      f"({title or 'untitled'}): body clipped: {detail}", file=sys.stderr)

    return clipped


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    sys.exit(int(main(args.pdf) and args.strict))
