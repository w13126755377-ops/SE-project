from datetime import date
from contextlib import closing
from src.db import connect
from src.scoring.engine import evaluate, rules


def valid_segment(segment):
    with closing(connect()) as conn:
        valid = conn.execute('SELECT 1 FROM chain_segment WHERE name = ?', (segment,)).fetchone()
    if not valid:
        raise ValueError('目标产业环节不在环节字典中')


def score_one(enterprise_id, target_segment, as_of=None):
    valid_segment(target_segment)
    with closing(connect()) as conn:
        row = conn.execute('SELECT * FROM enterprise WHERE id = ?', (enterprise_id,)).fetchone()
    return evaluate(dict(row), target_segment, as_of) if row else None


def rank_enterprises(target_segment, keyword=None, page=1, page_size=20, as_of=None):
    valid_segment(target_segment)
    # Rank the entire filtered set before pagination. Never rank a B1 page only.
    with closing(connect()) as conn:
        rows = conn.execute('SELECT * FROM enterprise WHERE chain_segment = ?', (target_segment,)).fetchall()
    items = [evaluate(dict(row), target_segment, as_of) for row in rows
             if not keyword or keyword.casefold() in (row['name'] + row['industry_name']).casefold()]
    items.sort(key=lambda item: (-item['total_score'], -item['coverage'], item['enterprise_id']))
    for rank, item in enumerate(items, 1):
        item['rank'] = rank
    return dict(total=len(items), page=page, page_size=page_size,
        items=items[(page - 1) * page_size:page * page_size], rule_version=rules()['version'],
        as_of=(as_of or date.today()).isoformat(), target_segment=target_segment,
        sort='total_score_desc,coverage_desc,enterprise_id_asc')
