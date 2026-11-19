"""Check staged, image-bearing engineering PDFs with an installed PyMuPDF reader."""
import argparse
import json


def check(document, required, min_images):
    if not len(document) or document.needs_pass:
        raise ValueError('empty or password-protected PDF')
    text = []
    image_count = 0
    for number, page in enumerate(document, 1):
        body = page.get_text()
        if not body.strip():
            raise ValueError(f'page {number} has no searchable text')
        text.append(body)
        # Inspect actual traced glyph/image geometry; clipped glyphs may be
        # filtered out of the ordinary text extractor.
        left, top, right, bottom = page.rect * page.derotation_matrix
        for kind, (x0, y0, x1, y1) in page.get_bboxlog():
            if kind not in {'fill-text', 'stroke-text', 'fill-image'}:
                continue
            image_count += kind == 'fill-image'
            if x0 < left - 1 or y0 < top - 1 or x1 > right + 1 or y1 > bottom + 1:
                raise ValueError(f'{kind} extends beyond page {number}')
    joined = ' '.join(' '.join(text).split())
    for phrase in required:
        if ' '.join(phrase.split()) not in joined:
            raise ValueError(f'missing searchable phrase: {phrase}')
    if image_count < min_images:
        raise ValueError(f'expected at least {min_images} figures, found {image_count} image placements')
    return {'pages': len(text), 'image_placements': image_count, 'visual_review': 'REQUIRED'}


if __name__ == '__main__':
    import pymupdf

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('--min-images', type=int, default=1)
    args = parser.parse_args()
    with pymupdf.open(args.pdf) as pdf:
        print(json.dumps(check(pdf, args.require, args.min_images)))
