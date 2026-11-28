import sqlite3
import threading
from datetime import date

from fastapi import FastAPI, Query

from src.bootstrap import ensure_database
from src.import_service import import_enterprises, import_policies, import_status
from src.leadership_service import diagnose_shortages
from src.query_service import enterprise_profile, list_enterprises, match_policies, segment_coverage
from src.schemas import EnterpriseImportRequest, PolicyImportRequest
from src.scoring.engine import rules as scoring_rules
from src.scoring.service import rank_enterprises, score_one

app = FastAPI(title="链式智能招商推荐系统 数据服务")

_import_lock = threading.Lock()


@app.on_event("startup")
def on_startup():
    ensure_database()


def _busy():
    return {"code": 409, "message": "已有导入任务在执行", "data": None}


def _ok(data):
    return {"code": 0, "message": "ok", "data": data}


@app.get("/api/v1/health")
def health():
    return _ok({"status": "up"})


@app.get('/api/v1/scoring/rules')
def score_rules():
    return _ok(scoring_rules())


@app.get('/api/v1/scoring/rankings')
def rankings(target_segment: str = Query(..., min_length=1), keyword: str = Query(None),
             page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
             as_of: date = Query(None)):
    try:
        return _ok(rank_enterprises(target_segment, keyword, page, page_size, as_of))
    except ValueError as error:
        return {'code': 400, 'message': str(error), 'data': None}


@app.get('/api/v1/enterprises/{enterprise_id}/score')
def enterprise_score(enterprise_id: int, target_segment: str = Query(..., min_length=1),
                     as_of: date = Query(None)):
    try:
        data = score_one(enterprise_id, target_segment, as_of)
    except ValueError as error:
        return {'code': 400, 'message': str(error), 'data': None}
    if data is None:
        return {'code': 404, 'message': '企业不存在', 'data': None}
    return _ok(data)


@app.post("/api/v1/data/enterprises/import")
def enterprise_import(req: EnterpriseImportRequest):
    if not _import_lock.acquire(blocking=False):
        return _busy()
    try:
        return _ok(import_enterprises(req.records, req.dry_run))
    except sqlite3.Error as e:
        return {"code": 500, "message": str(e), "data": None}
    finally:
        _import_lock.release()


@app.post("/api/v1/data/policies/import")
def policy_import(req: PolicyImportRequest):
    if not _import_lock.acquire(blocking=False):
        return _busy()
    try:
        return _ok(import_policies(req.records, req.dry_run))
    except sqlite3.Error as e:
        return {"code": 500, "message": str(e), "data": None}
    finally:
        _import_lock.release()


@app.get("/api/v1/data/import/status")
def status():
    return _ok(import_status())


@app.get("/api/v1/enterprises")
def enterprises(
    industry_code: str = Query(None, description="行业代码，多个逗号分隔"),
    chain_segment: str = Query(None, description="产业链环节，多个逗号分隔"),
    employee_scale: str = Query(None, description="员工规模区间"),
    region: str = Query(None, description="注册地"),
    keyword: str = Query(None, description="企业名称或行业关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    include_subregions: bool = Query(False, description="按完整地域名称前缀包含下辖区域"),
):
    return _ok(list_enterprises(
        industry_codes=industry_code,
        segments=chain_segment,
        employee_scale=employee_scale,
        region=region,
        keyword=keyword,
        page=page,
        page_size=page_size,
        include_subregions=include_subregions,
    ))


@app.get("/api/v1/enterprises/{enterprise_id}/profile")
def profile(enterprise_id: int):
    data = enterprise_profile(enterprise_id)
    if data is None:
        return {"code": 404, "message": "企业不存在", "data": None}
    return _ok(data)


@app.get("/api/v1/data/segments/coverage")
def coverage(region: str = Query(None, description="可选，按地域统计")):
    return _ok(segment_coverage(region))


@app.get("/api/v1/leadership/shortages")
def leadership_shortages(
    region: str = Query(None, description="按完整地域名称筛选"),
    include_subregions: bool = Query(False, description="包含下辖区域"),
):
    return _ok(diagnose_shortages(region, include_subregions))


@app.get("/api/v1/policies/match")
def policy_match(
    enterprise_id: int = Query(None, description="按企业匹配"),
    industry: str = Query(None, description="按行业匹配"),
    region: str = Query(None, description="按地域匹配"),
):
    data = match_policies(enterprise_id, industry, region)
    if data is None:
        return {"code": 404, "message": "企业不存在", "data": None}
    return _ok(data)
