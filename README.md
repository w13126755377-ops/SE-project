# 链式智能招商推荐系统

以杭州集成电路产业为演示场景，提供企业筛选、画像查询与考察优先级评价。

## 当前实现

- 数据服务：50家企业、10条政策、5个产业环节；支持筛选、画像与来源查询。
- 共享前端：项目总览、公共导航、组件与设计变量。
- 招商专员看板：关键词与环节检索、评分排序、企业详情、规则说明；Logo覆盖34家。
- D4规则引擎：四项加权评分、分项依据、缺失处理与版本配置。
- 决策领导、规划专班：保留页面入口，具体业务待开发。

## 本地启动

需要 Python 3.10+、Node.js 22.12+。

仓库根目录启动后端：

```powershell
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

另开终端启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

打开终端输出的地址并进入「招商专员」。数据库首次启动时自动创建并填充，无须提交本地数据库。前端通过Vite代理访问后端。

## 验证

```powershell
python -m unittest discover -s tests -v
npm test --prefix frontend
npm run build --prefix frontend
```

## 开发文档

- [前端运行与目录](frontend/README.md)
- [协作分工与交接](docs/frontend-handoff.md)
- [组件与动效规范](docs/frontend-design-system.md)
- [评分规则与接口](docs/scoring-engine.md)
- [Logo覆盖情况](docs/enterprise-logo-status.md)
- [Logo素材来源](frontend/public/enterprise-logos/SOURCES.md)
- [数据岗接口契约](数据岗接口契约_v1.0.md)

评分配置位于 `src/scoring/rules.json`。展示数据与评分证据分别处理；资料缺失会保留待补充状态。当前候选库以本地企业为主，详细业务边界见评分文档。
