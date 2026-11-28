"""Deterministic weighted sum. Scores describe evidence, not investment probability."""
import json
import math
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RULE_PATH = Path(__file__).with_name('rules.json')


def rules():
    return json.loads(RULE_PATH.read_text(encoding='utf-8'))


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def parse(value, expected):
    if isinstance(value, expected):
        return value
    try:
        result = json.loads(value)
        return result if isinstance(result, expected) else None
    except (ValueError, TypeError):
        return None


def evaluate(enterprise, target_segment, as_of=None, weights=None):
    config = rules()
    as_of = as_of or date.today()
    weights = dict(config['weights'] if weights is None else weights)
    if (set(weights) != set(config['weights']) or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in weights.values()) or
            not math.isclose(sum(weights.values()), 1, abs_tol=1e-9)):
        raise ValueError('权重必须包含全部四项、非负且合计为 1')
    if not target_segment:
        raise ValueError('必须指定目标产业环节')
    dimensions = []
    warnings = []

    def add(key, label, score, evidence, reason):
        dimensions.append(dict(key=key, label=label, score=score, weight=weights[key],
            contribution=None if score is None else rounded(score * weights[key]),
            status='missing' if score is None else 'available', evidence=evidence,
            reason=reason, source_url=enterprise.get('source_url'), source=enterprise.get('source')))

    segment = enterprise.get('chain_segment')
    add('segment', '目标环节匹配', None if not segment else (100 if segment == target_segment else 0),
        {'chain_segment': segment, 'target_segment': target_segment}, '精确匹配目标环节为100，否则为0；不推断上下游关系')

    employee = enterprise.get('employee_scale') or ''
    # Use the lower bound consistently for both intervals and open-ended bands.
    match = re.fullmatch(r'\s*(\d+)\s*(?:-\s*\d+)?\s*人\s*(?:以上)?\s*', employee)
    scale = None
    if match:
        lower = int(match.group(1))
        scale = next((score for upper, score in config['employee_bands'] if lower <= upper), None)
    add('scale', '员工规模', scale, {'employee_scale': employee or None}, '按员工区间下界分档；规模只代表组织基础，不代表落地意愿')

    tech = parse(enterprise.get('tech_qualifications'), dict)
    qualifications = tech.get('资质') if tech else None
    known = []
    if isinstance(qualifications, list):
        known = [score for text in qualifications if isinstance(text, str)
                 for keyword, score in config['qualification_rules'] if keyword in text]
    add('qualification', '已收录技术资质', max(known) if known else None,
        {'tech_qualifications': tech}, '取识别到的最高资质档位，不叠加；无可识别资质为待补充，专利数不直接用于评分')

    events = parse(enterprise.get('investment_events'), list)
    ages = []
    for event in events or []:
        if not isinstance(event, dict):
            continue
        raw = str(event.get('时间', ''))
        # A month is an observation bucket. Day precision is checked when supplied.
        if not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?', raw):
            warnings.append('投资事件日期缺失或无法识别')
            continue
        try:
            event_date = date.fromisoformat(raw if len(raw) == 10 else raw + '-01')
        except ValueError:
            warnings.append('投资事件日期无效')
            continue
        if event_date > as_of:
            warnings.append('未来日期投资事件未参与评分：' + raw)
            continue
        ages.append((as_of.year - event_date.year) * 12 + as_of.month - event_date.month)
    activity = next((score for upper, score in config['activity_month_bands'] if min(ages) <= upper), None) if ages else None
    add('activity', '已收录投资事件时效', activity, {'investment_events': events, 'latest_age_months': min(ages) if ages else None},
        '按最近有效事件距评估日的月份分档；仅描述已收录活动，不推断未来扩张或迁入意愿')

    missing = [d['key'] for d in dimensions if d['score'] is None]
    total = sum(d['score'] * d['weight'] for d in dimensions if d['score'] is not None)
    coverage = sum(d['weight'] for d in dimensions if d['score'] is not None)
    return dict(enterprise_id=enterprise.get('id'), name=enterprise.get('name'),
        rule_version=config['version'], target_segment=target_segment, as_of=as_of.isoformat(),
        total_score=rounded(total), score_upper_bound=rounded(total + (1 - coverage) * 100),
        score_kind='complete' if not missing else 'evidence_lower_bound',
        coverage=rounded(coverage), missing_dimensions=missing, dimensions=dimensions,
        warnings=sorted(set(warnings)), label=config['label'])
