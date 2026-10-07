#!/usr/bin/env python3
"""Create a standalone review dashboard from an assessment JSON file."""
import argparse
import json
from pathlib import Path


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

    strings(d, 'reviewId title journal articleType scope version reviewDate', 'review')
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
    ids = []
    for u in d['paragraphs']:
        strings(u, 'id section location opening purpose action workType evidenceNeeded improveWhen', 'paragraph')
        require(u['section'] != 'All paragraphs', 'All paragraphs is a reserved section label')
        ids.append(u['id'])
        r = u.get('r')
        require(isinstance(r, list) and len(r) == 5, 'Each paragraph needs five ratings in C/E/J/F/L order')
        require(all((type(v) is int and 0 <= v <= 4) or (isinstance(v, str) and v in ('U', 'N/A')) for v in r), 'Invalid rating')
        strings(u.get('reasons'), 'C E J F L', u['id'] + '.reasons')
        require(isinstance(u.get('blocker', ''), str) and isinstance(u.get('provisional', ''), str), 'blocker/provisional must be text')
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assessment', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.assessment.read_text())
    validate(data)
    template = Path(__file__).resolve().parent.parent / 'assets/review/dashboard-template.html'
    html = template.read_text()
    token = '__REVIEW_DATA_JSON__'
    if html.count(token) != 1:
        raise ValueError('Expected one assessment insertion marker')
    encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    html = html.replace(token, encoded)
    if len(html.encode()) >= 1000000:
        raise ValueError('Dashboard exceeds the inline size limit; shorten assessment text')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)
    print(args.output)


if __name__ == '__main__':
    main()
