#!/usr/bin/env python3
"""Pair manual-duplex ADF scans, preserving originals and producing one PDF."""
import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader, PdfWriter

BASE = Path('/data')
FRONT = BASE / 'front'
BACK = BASE / 'back'
OUTPUT = BASE / 'output'
ARCHIVE = BASE / 'archive'
ERROR = BASE / 'error'
INTERVAL = int(os.getenv('POLL_SECONDS', '5'))
STABLE = int(os.getenv('MIN_AGE_SECONDS', '15'))
REVERSE_BACK = os.getenv('REVERSE_BACK', 'true').lower() == 'true'
LOG = logging.getLogger('duplex-merge')


def candidates(folder):
    now = time.time()
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.pdf'
                   and now - p.stat().st_mtime >= STABLE),
                  key=lambda p: (p.stat().st_mtime, p.name))


def merge(front_path, back_path):
    reader_front = PdfReader(str(front_path), strict=False)
    reader_back = PdfReader(str(back_path), strict=False)
    a, b = len(reader_front.pages), len(reader_back.pages)
    if a != b or a == 0:
        raise ValueError(f'Unequal/empty page counts: front={a}, back={b}')
    result = PdfWriter()
    backs = list(reader_back.pages)
    if REVERSE_BACK:
        backs.reverse()
    for p1, p2 in zip(reader_front.pages, backs):
        result.add_page(p1)
        result.add_page(p2)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    unique = uuid.uuid4().hex[:8]
    output_name = f'duplex-{stamp}-{unique}.pdf'
    temp = OUTPUT / ('.' + output_name + '.tmp')
    final = OUTPUT / output_name
    try:
        with temp.open('wb') as f:
            result.write(f)
            f.flush()
            os.fsync(f.fileno())
        # Validate before making the output visible to Paperless.
        if len(PdfReader(str(temp)).pages) != a + b:
            raise RuntimeError('Output validation failed; input PDFs remain untouched')
        os.replace(temp, final)
    finally:
        temp.unlink(missing_ok=True)
    folder = ARCHIVE / (stamp + '-' + unique)
    folder.mkdir(parents=True, exist_ok=False)
    shutil.move(str(front_path), str(folder / ('front-' + front_path.name)))
    shutil.move(str(back_path), str(folder / ('back-' + back_path.name)))
    LOG.info('Created %s (%d pages); originals in %s', final.name, a + b, folder)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    for folder in (FRONT, BACK, OUTPUT, ARCHIVE, ERROR):
        folder.mkdir(parents=True, exist_ok=True)
    LOG.info('Started. Reverse back pages: %s. Only one document at a time!', REVERSE_BACK)
    while True:
        try:
            fronts, backs = candidates(FRONT), candidates(BACK)
            if fronts and backs:
                a, b = fronts[0], backs[0]
                try:
                    merge(a, b)
                except Exception:
                    LOG.exception('Could not merge %s and %s. Inputs kept for manual review.', a.name, b.name)
                    # Avoid tight retry loops: leave files in place and sleep longer.
                    time.sleep(60)
        except Exception:
            LOG.exception('Error scanning folders')
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
