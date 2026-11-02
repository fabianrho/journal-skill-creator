#!/usr/bin/env python3
"""Create a standalone review dashboard and its annotated PDF from an assessment JSON file."""
import argparse
import base64
import json
import math
import re
import sys
import unicodedata
import zlib
from pathlib import Path

DIMS = 'CEJFL'
NAMES = {'C': 'Content', 'E': 'Evidence', 'J': 'Journal', 'F': 'Flow', 'L': 'Language'}
WEIGHTS = [25, 30, 20, 10, 15]
# Sentence-highlight scale shared with the HTML template: rating -> (hex, label).
HIGHLIGHT = {4: ('#b8e3a8', 'no material issue'), 3: ('#ddee99', 'minor'), 2: ('#ffd980', 'substantive'),
             1: ('#ffa873', 'major'), 0: ('#ff8080', 'fails'), 'U': ('#c7d4e6', 'unverified')}
CORE_CODES = {'A', 'K', 'I', 'M', 'R', 'D'}


def validate(d):
    def require(ok, message):
        if not ok:
            raise ValueError(message)

    def strings(obj, keys, where):
        require(isinstance(obj, dict), f'{where} must be an object')
        for key in keys.split():
            require(isinstance(obj.get(key), str) and obj[key].strip(), f'{where}.{key} needs explicit text')

    def number(value):
        return type(value) in (int, float) and float('-inf') < value < float('inf')

    strings(d, 'reviewId title journal articleType scope version reviewDate requirementsAccess', 'review')
    strings(d.get('editorial'), 'reason status', 'editorial')
    value = d['editorial'].get('score')
    require(value is None or number(value) and 0 <= value <= 10, 'editorial.score must be null or 0–10')
    strings(d.get('length'), 'limitStatus scope exclusions source method', 'length')
    length = d['length']
    require(length['limitStatus'] in ('verified', 'unverified', 'none'), 'Invalid limitStatus')
    require(length.get('count') is None or type(length['count']) is int and length['count'] >= 0, 'count must be null or a nonnegative integer')
    if length['limitStatus'] == 'verified':
        require(type(length.get('limit')) is int and length['limit'] > 0, 'Verified limit must be a positive integer')
    else:
        require(length.get('limit') is None, 'Unverified/inapplicable limits must be null')
    strings(d.get('focus'), 'action status workType', 'focus')
    require(isinstance(d['focus'].get('ids'), list), 'focus.ids must be a list')
    for key in ('paragraphs', 'actions', 'coverage', 'checks', 'sources'):
        require(isinstance(d.get(key), list), f'{key} must be a list')
    ids, codes = [], {}
    for u in d['paragraphs']:
        strings(u, 'id section sectionCode location opening purpose action workType evidenceNeeded improveWhen', 'paragraph')
        require(u['section'] != 'All paragraphs', 'All paragraphs is a reserved section label')
        code = u['sectionCode']
        require(re.fullmatch(r'[A-Z]{1,3}', code) and (len(code) > 1 or code in CORE_CODES), f'{u["id"]}: sectionCode must be a core letter (A K I M R D) or 2–3 capital initials')
        require(codes.setdefault(u['section'], code) == code, f'Section {u["section"]} has more than one sectionCode')
        require(re.fullmatch(re.escape(code) + r' P[1-9]\d*', u['id']), f'{u["id"]}: id must be sectionCode, a space, P and its paragraph number, e.g. {code} P1')
        ids.append(u['id'])
        r = u.get('r')
        require(isinstance(r, list) and len(r) == 5, 'Each paragraph needs five ratings in C/E/J/F/L order')
        require(all((type(v) is int and 0 <= v <= 4) or (isinstance(v, str) and v in ('U', 'N/A')) for v in r), 'Invalid rating')
        strings(u.get('reasons'), 'C E J F L', u['id'] + '.reasons')
        require(isinstance(u.get('blocker', ''), str) and isinstance(u.get('provisional', ''), str), 'blocker/provisional must be text')
        validate_segments(u, require)
    require(len(set(codes.values())) == len(codes), 'Each section needs its own sectionCode')
    require(len(ids) == len(set(ids)), 'Paragraph IDs must be unique')
    require(all(isinstance(i, str) and i in ids for i in d['focus']['ids']), 'focus.ids must reference assessed paragraph IDs')
    for a in d['actions']:
        strings(a, 'title location workType action completeWhen evidenceBoundary', 'action')
    for c in d['coverage']:
        require(isinstance(c, list) and len(c) == 2 and all(isinstance(v, str) and v.strip() for v in c), 'coverage requires label/text pairs')
    require(bool(d['coverage']), 'Declare review coverage and limitations')
    for c in d['checks']:
        strings(c, 'check observed status', 'check')
    for s in d['sources']:
        strings(s, 'id basis title location access limitations', 'source')
        require(s.get('url') is None or isinstance(s['url'], str) and s['url'].startswith(('https://', 'http://')), 'Source URL must be http(s) or null')
    require(bool(d['sources']), 'Include inspected source or explicit unavailable-source records')


def validate_segments(u, require):
    where = u['id'] + '.segments'
    segs = u.get('segments')
    require(isinstance(segs, list) and segs, f'{where} must list the paragraph text in highlighted spans')
    for i, s in enumerate(segs):
        require(isinstance(s, dict) and isinstance(s.get('text'), str) and s['text'].strip(), f'{where}[{i}].text needs paragraph text')
        rating, dims = s.get('rating'), s.get('dims')
        require((type(rating) is int and 0 <= rating <= 4) or rating == 'U', f'{where}[{i}].rating must be 0–4 or "U"')
        require(isinstance(dims, list) and len(set(dims)) == len(dims) and all(x in DIMS for x in dims), f'{where}[{i}].dims must list distinct C/E/J/F/L letters')
        require(bool(dims) == (rating != 4), f'{where}[{i}]: rating 4 has no dims; every other rating names its dims')
        require(isinstance(s.get('comment'), str) and s['comment'].strip(), f'{where}[{i}].comment needs explicit text')
        require(isinstance(s.get('suggestion', ''), str), f'{where}[{i}].suggestion must be text')
        cited = [u['r'][DIMS.index(x)] for x in dims]
        require('N/A' not in cited, f'{where}[{i}] cites a dimension rated N/A')
        numeric = [v for v in cited if type(v) is int]
        require(rating == 'U' or not numeric or rating >= min(numeric), f'{where}[{i}] is rated below its paragraph dimension ratings')
    for i, v in enumerate(u['r']):
        dim = DIMS[i]
        if type(v) is int and v < 4:
            require(any(dim in s['dims'] and s['rating'] != 'U' for s in segs), f'{where}: {dim}={v} needs a highlighted span that names {dim}')
        if v == 'U':
            require(any(dim in s['dims'] and s['rating'] == 'U' for s in segs), f'{where}: {dim}=U needs a U span that names {dim}')
    text = ' '.join(''.join(s['text'] for s in segs).split())
    opening = ' '.join(u['opening'].rstrip('…. ').split())
    require(text.startswith(opening), f'{where} must reproduce the paragraph verbatim, starting with its opening')


def calc(u):
    earned = unknown = applicable = 0
    for v, w in zip(u['r'], WEIGHTS):
        if v == 'N/A':
            continue
        applicable += w
        if v == 'U':
            unknown += w
        else:
            earned += w * v / 4
    assessed = applicable - unknown
    rnd = lambda x: math.floor(x + 0.5) / 10
    return {'low': rnd(100 * earned / applicable) if assessed else None, 'high': rnd(100 * (earned + unknown) / applicable) if assessed else None,
            'coverage': math.floor(100 * assessed / applicable + 0.5) if applicable else 0, 'unknown': unknown, 'assessed': assessed}


def score(u):
    s = calc(u)
    return 'Not assessed' if not s['assessed'] else f'{s["low"]:.1f}–{s["high"]:.1f}' if s['unknown'] else f'{s["low"]:.1f}'


def verdict(u):
    s = calc(u)
    incomplete = bool(s['unknown'] or u.get('provisional'))
    if u.get('blocker'):
        return 'Blocked; assessment incomplete' if incomplete else 'Blocked'
    if not s['assessed']:
        return 'Not assessed'
    if incomplete:
        return 'Provisional'
    low = s['low']
    return 'Ready within assessed scope' if low >= 9 else 'Minor revision' if low >= 7.5 else 'Substantive revision' if low >= 5 else 'Major revision'


# ---- Annotated PDF (standard 14 fonts, WinAnsi text, Symbol for Greek and maths) ----

HELV = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
        1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
        333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584, 278,
        556, 0, 222, 556, 333, 1000, 556, 556, 333, 1000, 667, 333, 1000, 0, 611, 0, 0, 222, 222, 333, 333, 350, 556, 1000, 333, 1000, 500, 333, 944, 0, 500, 667,
        278, 333, 556, 556, 556, 556, 260, 556, 333, 737, 370, 556, 584, 333, 737, 333, 400, 584, 333, 333, 333, 556, 537, 278, 333, 333, 365, 556, 834, 834, 834, 611,
        667, 667, 667, 667, 667, 667, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278, 722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
        556, 556, 556, 556, 556, 556, 889, 500, 556, 556, 556, 556, 278, 278, 278, 278, 556, 556, 556, 556, 556, 556, 556, 584, 611, 556, 556, 556, 556, 500, 556, 500]
HELV_BOLD = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
             975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
             333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584, 278,
             556, 0, 278, 556, 500, 1000, 556, 556, 333, 1000, 667, 333, 1000, 0, 611, 0, 0, 278, 278, 500, 500, 350, 556, 1000, 333, 1000, 556, 333, 944, 0, 500, 667,
             278, 333, 556, 556, 556, 556, 280, 556, 333, 737, 370, 556, 584, 333, 737, 333, 400, 584, 333, 333, 333, 611, 556, 278, 333, 333, 365, 556, 834, 834, 834, 611,
             722, 722, 722, 722, 722, 722, 1000, 722, 667, 667, 667, 667, 278, 278, 278, 278, 722, 722, 778, 778, 778, 778, 778, 584, 778, 722, 722, 722, 722, 667, 667, 611,
             556, 556, 556, 556, 556, 556, 889, 556, 556, 556, 556, 556, 278, 278, 278, 278, 611, 611, 611, 611, 611, 611, 611, 584, 611, 611, 611, 611, 611, 556, 611, 556]
SYMBOL = {'α': (0x61, 631), 'β': (0x62, 549), 'χ': (0x63, 549), 'δ': (0x64, 494), 'ε': (0x65, 439), 'φ': (0x66, 521), 'γ': (0x67, 411), 'η': (0x68, 603),
          'ι': (0x69, 329), 'κ': (0x6B, 549), 'λ': (0x6C, 549), 'μ': (0x6D, 576), 'ν': (0x6E, 521), 'ο': (0x6F, 549), 'π': (0x70, 549), 'θ': (0x71, 521),
          'ρ': (0x72, 549), 'σ': (0x73, 603), 'τ': (0x74, 439), 'υ': (0x75, 576), 'ω': (0x77, 686), 'ξ': (0x78, 493), 'ψ': (0x79, 686), 'ζ': (0x7A, 494),
          'Γ': (0x47, 603), 'Δ': (0x44, 612), 'Θ': (0x51, 741), 'Λ': (0x4C, 686), 'Ξ': (0x58, 645), 'Π': (0x50, 768), 'Σ': (0x53, 592), 'Φ': (0x46, 763),
          'Ψ': (0x59, 795), 'Ω': (0x57, 768), '≤': (0xA3, 549), '≥': (0xB3, 549), '≠': (0xB9, 549), '≈': (0xBB, 549), '→': (0xAE, 987), '←': (0xAC, 987),
          '↔': (0xAB, 1042), '−': (0x2D, 549), '∞': (0xA5, 713), '∼': (0x7E, 549), '∝': (0xB5, 713), '∂': (0xB6, 494), '∑': (0xE5, 713), '√': (0xD6, 549),
          '∈': (0xCE, 713), '′': (0xA2, 247), '″': (0xB2, 411)}
SUBSTITUTE = {'‐': '-', '‑': '-', 'μ': 'µ'}
PAGE_W, PAGE_H, MARGIN, TOP, BOTTOM = 595.28, 841.89, 56, 64, 56
BODY, LEADING = 10.5, 15.5


def glyphs(text, bold, missing):
    """Map text to (font, code, width/1000) glyphs drawable with the standard fonts."""
    out = []
    for ch in text:
        ch = ' ' if ch.isspace() else SUBSTITUTE.get(ch, ch)
        try:
            code = ch.encode('cp1252')[0] if len(ch.encode('cp1252')) == 1 else None
        except UnicodeEncodeError:
            code = None
        if code is not None and code >= 32 and HELV[code - 32]:
            out.append(('F2' if bold else 'F1', code, (HELV_BOLD if bold else HELV)[code - 32]))
        elif ch in SYMBOL:
            out.append(('F3', *SYMBOL[ch]))
        else:
            decomposed = ''.join(c for c in unicodedata.normalize('NFKD', ch) if not unicodedata.combining(c))
            if decomposed and decomposed != ch:
                out.extend(glyphs(decomposed, bold, missing))
            else:
                missing.add(ch)
                out.append(('F2' if bold else 'F1', 63, 556 if not bold else 611))
    return out


def wrap(items, width, size):
    """Greedy line breaking of (font, code, w, tag) glyphs at spaces; returns lines of placed glyphs."""
    words, word = [], []
    for g in items:
        if g[1] == 32:
            if word:
                words.append(word)
            word = []
        else:
            word.append(g)
    if word:
        words.append(word)
    lines, line, x = [], [], 0.0
    for word in words:
        ww = sum(g[2] for g in word) * size / 1000
        space = 278 * size / 1000 if line else 0
        if line and x + space + ww > width:
            lines.append(line)
            line, x, space = [], 0.0, 0
        if space:
            line.append(('F1', 32, 278, line[-1][3], x))
            x += space
        for g in word:
            gw = g[2] * size / 1000
            if line and x + gw > width:
                lines.append(line)
                line, x = [], 0.0
            line.append((*g, x))
            x += gw
    if line:
        lines.append(line)
    return lines


def pdf_text(s):
    return '<FEFF' + s.encode('utf-16-be').hex().upper() + '>'


def rgb(hexcolor):
    return [int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def fmt(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


class Pdf:
    def __init__(self):
        self.objects = []

    def add(self, body):
        self.objects.append(body)
        return len(self.objects)

    def stream(self, head, data):
        packed = zlib.compress(data, 9)
        return self.add(f'<< {head} /Filter /FlateDecode /Length {len(packed)} >>\nstream\n'.encode('latin-1') + packed + b'\nendstream')

    def output(self, root, info):
        out = bytearray(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3\n')
        offsets = []
        for i, body in enumerate(self.objects, 1):
            offsets.append(len(out))
            out += f'{i} 0 obj\n'.encode() + (body if isinstance(body, bytes) else body.encode('latin-1')) + b'\nendobj\n'
        xref = len(out)
        out += f'xref\n0 {len(self.objects) + 1}\n0000000000 65535 f \n'.encode()
        out += b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets)
        out += f'trailer\n<< /Size {len(self.objects) + 1} /Root {root} 0 R /Info {info} 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
        return bytes(out)


def render_pdf(d):
    """Lay out every paragraph with one highlight annotation per segment and one note per paragraph."""
    missing, pages = set(), []
    width = PAGE_W - 2 * MARGIN
    page = None

    def new_page():
        nonlocal page
        page = {'ops': [], 'annots': [], 'y': PAGE_H - TOP}
        pages.append(page)

    def text_line(line, x0, y, size, color='0 g'):
        ops, font = [f'BT {color} {fmt(x0)} {fmt(y)} Td'], None
        for g in line:
            if g[0] != font:
                ops.append(f'/{g[0]} {fmt(size)} Tf')
                font = g[0]
            byte = g[1]
            ch = chr(byte)
            ops.append('(' + (('\\' + ch) if ch in '\\()' else ch if 32 <= byte < 127 else f'\\{byte:03o}') + ') Tj')
        ops.append('ET')
        page['ops'].append(' '.join(ops))

    def block(text, size, bold=False, color='0 g', gap=0):
        lines = wrap([(*g, None) for g in glyphs(text, bold, missing)], width, size)
        for line in lines:
            if page['y'] - size < BOTTOM:
                new_page()
            page['y'] -= size * 1.35
            text_line(line, MARGIN, page['y'], size, color)
        page['y'] -= gap

    new_page()
    block(d['title'], 15, bold=True, gap=4)
    block(' · '.join(d[k] for k in ('journal', 'articleType', 'scope', 'version', 'reviewDate', 'requirementsAccess')), 8.5, color='0.35 g', gap=8)
    x, y = MARGIN, page['y'] - 12
    for key in (4, 3, 2, 1, 0, 'U'):
        label = f'{key} {HIGHLIGHT[key][1]}'
        lw = sum(g[2] for g in glyphs(label, False, missing)) * 8.5 / 1000
        if x + 14 + lw > MARGIN + width:
            x, y = MARGIN, y - 14
        page['ops'].append(f'{" ".join(fmt(c) for c in rgb(HIGHLIGHT[key][0]))} rg {fmt(x)} {fmt(y - 2)} 10 10 re f')
        text_line([(*g[:3], None, 0) for g in glyphs(label, False, missing)], x + 14, y, 8.5)
        x += 14 + lw + 16
    page['y'] = y - 6
    block('Each highlight carries a comment: the paragraph ID, its 0–4 rating on the rubric anchors, the dimensions concerned and the reason. '
          'The margin note beside each paragraph gives its dashboard score, verdict and next action. Open the comments panel of your PDF viewer to read them all. '
          'Highlights explain the paragraph scores; they do not change them.', 8.5, color='0.35 g', gap=6)
    section, annot_no = None, 0
    for u in d['paragraphs']:
        if u['section'] != section:
            section = u['section']
            if page['y'] - 60 < BOTTOM:
                new_page()
            page['y'] -= 10
            block(f'{u["sectionCode"]} · {section}', 12.5, bold=True, gap=2)
        label = f'{u["id"]} · {u["purpose"]} · {score(u)}{"" if score(u) == "Not assessed" else "/10"} · {verdict(u)}'
        label_lines = wrap([(*g, None) for g in glyphs(label, False, missing)], width, 8.5)
        chars = []
        for i, s in enumerate(u['segments']):
            chars.extend((c, i) for c in s['text'])
        flat = []
        for c, i in chars:
            if c.isspace() and (not flat or flat[-1][0] == ' '):
                continue
            flat.append((' ' if c.isspace() else c, i))
        while flat and flat[-1][0] == ' ':
            flat.pop()
        items = []
        for c, i in flat:
            items.extend((*g, i) for g in glyphs(c, False, missing))
        lines = wrap(items, width, BODY)
        if page['y'] - 8.5 * 1.35 * len(label_lines) - LEADING * min(2, len(lines)) < BOTTOM:
            new_page()
        page['y'] -= 6
        for n, line in enumerate(label_lines):
            page['y'] -= 8.5 * 1.35
            text_line(line, MARGIN, page['y'], 8.5, '0.35 g')
            if n == 0:
                note = [f'{u["id"]} · {u["section"]} · {u["purpose"]}', f'Score: {score(u)}{"" if score(u) == "Not assessed" else "/10"} · {verdict(u)} · {calc(u)["coverage"]}% assessed weight']
                note += [f'Blocker: {u["blocker"]}'] if u.get('blocker') else []
                note += [f'Assessment limitation: {u["provisional"]}'] if u.get('provisional') else []
                note += [f'Next action: {u["action"]}', f'Score can improve: {u["improveWhen"]}']
                annot_no += 1
                page['annots'].append({'kind': 'note', 'rect': [MARGIN - 36, page['y'] - 6, MARGIN - 16, page['y'] + 14], 'text': '\n'.join(note), 'name': f'{u["id"]}-note'})
        page['y'] -= 2
        boxes = {}
        for line in lines:
            if page['y'] - LEADING < BOTTOM:
                new_page()
            page['y'] -= LEADING
            text_line(line, MARGIN, page['y'], BODY)
            spans = {}
            for g in line:
                if g[1] != 32:
                    lo, hi = spans.get(g[3], (g[4], g[4] + g[2] * BODY / 1000))
                    spans[g[3]] = (min(lo, g[4]), max(hi, g[4] + g[2] * BODY / 1000))
            for i, (lo, hi) in spans.items():
                boxes.setdefault((i, len(pages)), []).append((MARGIN + lo - 0.5, page['y'] - 3.2, MARGIN + hi + 0.5, page['y'] + 10.3))
        for (i, page_no), rects in boxes.items():
            s = u['segments'][i]
            rating = s['rating']
            head = f'{u["id"]} · {rating}{"/4" if rating != "U" else ""} {HIGHLIGHT[rating][1]}'
            head += ' · ' + ', '.join(f'{x} {NAMES[x]}' for x in s['dims']) if s['dims'] else ''
            body = head + '\n' + s['comment'].strip() + (f'\nSuggested wording: {s["suggestion"].strip()}' if s.get('suggestion', '').strip() else '')
            pages[page_no - 1]['annots'].append({'kind': 'highlight', 'rects': rects, 'color': HIGHLIGHT[rating][0], 'text': body,
                                                  'subject': f'Rating {rating}{"/4" if rating != "U" else ""}', 'name': f'{u["id"]}-s{i + 1}-p{page_no}'})
        page['y'] -= 4

    pdf = Pdf()
    author = pdf_text(f'{d["journal"]} review')
    date = 'D:' + re.sub(r'\D', '', d['reviewDate'])[:8]
    pdf.add('')  # catalog placeholder
    pdf.add('')  # pages placeholder
    fonts = {'F1': pdf.add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>'),
             'F2': pdf.add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>'),
             'F3': pdf.add('<< /Type /Font /Subtype /Type1 /BaseFont /Symbol >>')}
    multiply = pdf.add('<< /Type /ExtGState /BM /Multiply /CA 1 /ca 1 >>')
    kids = []
    for n, page in enumerate(pages, 1):
        footer = [(*g[:3], None, 0) for g in glyphs(f'Annotated review · {d["reviewId"]} · Page {n} of {len(pages)}', False, missing)]
        page['y'] = BOTTOM - 26
        text_line(footer, MARGIN, page['y'], 8, '0.45 g')
        content = pdf.stream('', '\n'.join(page['ops']).encode('latin-1'))
        page_obj = len(pdf.objects) + 1 + 2 * sum(a['kind'] == 'highlight' for a in page['annots']) + sum(a['kind'] == 'note' for a in page['annots'])
        annots = []
        for a in page['annots']:
            common = f'/Contents {pdf_text(a["text"])} /T {author} /NM {pdf_text(a["name"])} /M ({date}) /F 4 /P {page_obj} 0 R'
            if a['kind'] == 'note':
                annots.append(pdf.add(f'<< /Type /Annot /Subtype /Text /Rect [{" ".join(fmt(v) for v in a["rect"])}] /Name /Comment /C [0.15 0.46 0.42] /Open false {common} >>'))
                continue
            x1, y1 = min(r[0] for r in a['rects']), min(r[1] for r in a['rects'])
            x2, y2 = max(r[2] for r in a['rects']), max(r[3] for r in a['rects'])
            color = ' '.join(fmt(c) for c in rgb(a['color']))
            ap = pdf.stream(f'/Type /XObject /Subtype /Form /BBox [{fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)}] /Resources << /ExtGState << /G0 {multiply} 0 R >> >>',
                            (f'/G0 gs {color} rg ' + ' '.join(f'{fmt(r[0])} {fmt(r[1])} {fmt(r[2] - r[0])} {fmt(r[3] - r[1])} re' for r in a['rects']) + ' f').encode())
            quads = ' '.join(f'{fmt(r[0])} {fmt(r[3])} {fmt(r[2])} {fmt(r[3])} {fmt(r[0])} {fmt(r[1])} {fmt(r[2])} {fmt(r[1])}' for r in a['rects'])
            annots.append(pdf.add(f'<< /Type /Annot /Subtype /Highlight /Rect [{fmt(x1)} {fmt(y1)} {fmt(x2)} {fmt(y2)}] /QuadPoints [{quads}] /C [{color}] '
                                  f'/CA 1 /Subj {pdf_text(a["subject"])} {common} /AP << /N {ap} 0 R >> >>'))
        font_res = ' '.join(f'/{k} {v} 0 R' for k, v in fonts.items())
        kids.append(pdf.add(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {fmt(PAGE_W)} {fmt(PAGE_H)}] /Resources << /Font << {font_res} >> >> '
                            f'/Contents {content} 0 R /Annots [{" ".join(f"{a} 0 R" for a in annots)}] >>'))
        assert kids[-1] == page_obj, 'page object number mismatch'
    pdf.objects[0] = '<< /Type /Catalog /Pages 2 0 R /PageMode /UseNone >>'
    pdf.objects[1] = f'<< /Type /Pages /Kids [{" ".join(f"{k} 0 R" for k in kids)}] /Count {len(kids)} >>'
    info = pdf.add(f'<< /Title {pdf_text(d["title"])} /Subject {pdf_text("Annotated manuscript review")} /Author {author} '
                   f'/Creator (render_review_dashboard.py) /CreationDate ({date}) >>')
    return pdf.output(1, info), missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assessment', type=Path)
    parser.add_argument('output', type=Path, help='dashboard HTML; the annotated PDF is written beside it as <name>-annotated.pdf')
    args = parser.parse_args()
    data = json.loads(args.assessment.read_text())
    validate(data)
    pdf, missing = render_pdf(data)
    if missing:
        print('Warning: drawn as "?" in the PDF (comments keep the original): ' + ' '.join(sorted(missing)), file=sys.stderr)
    template = Path(__file__).resolve().parent.parent / 'assets/review/dashboard-template.html'
    html = template.read_text()
    for token in ('__REVIEW_DATA_JSON__', '__REVIEW_PDF_BASE64__'):
        if html.count(token) != 1:
            raise ValueError(f'Expected one {token} insertion marker')
    encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    html = html.replace('__REVIEW_DATA_JSON__', encoded).replace('__REVIEW_PDF_BASE64__', base64.b64encode(pdf).decode())
    if len(html.encode()) >= 1000000:
        raise ValueError('Dashboard exceeds the inline size limit; shorten assessment text')
    pdf_path = args.output.with_name(args.output.stem + '-annotated.pdf')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)
    pdf_path.write_bytes(pdf)
    print(args.output)
    print(pdf_path)


if __name__ == '__main__':
    main()
