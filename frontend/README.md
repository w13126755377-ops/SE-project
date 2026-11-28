# 共享前端

## 运行

需要 Node.js 22.12+（本次使用 22.19）和 npm。

```powershell
cd frontend
npm ci
npm run dev
```

访问终端显示的地址，通常为 http://127.0.0.1:5173 。后端另开终端在仓库根目录启动：

```powershell
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Vite 将 `/api` 转发到 8000，无须修改后端 CORS。正式部署时由同源反向代理处理 `/api`，开发代理不会包含在 dist 中。

```powershell
npm run build
npm test
```

## 交接入口

| 路由 | 文件/职责 |
| --- | --- |
| `/` | `src/pages/OverviewPage.vue`，总览与动效 |
| `/leadership` | `src/pages/leadership/index.vue`，领导看板 |
| `/specialist` | `src/pages/specialist/index.vue`，招商专员看板 |
| `/planning` | `src/pages/planning/index.vue`，规划专班看板 |

三个业务页面分别提供独立目录与入口。决策领导页已接入 D1 短板诊断和企业样本；招商专员已实现检索、评分排序、企业详情和规则说明。规划专班在共享前端中仍引用 `WorkspacePage.vue` 占位骨架，其独立原型位于 `../src/frontend/planning-dashboard/`。各角色在自己的 `index.vue` 中开发，局部组件放在同级 `components/`，无需改路由。公共导航与页脚由框架提供。路由可直接打开和刷新；生产服务器需要 history fallback 到 index.html。

## 目录

- `src/styles/tokens.css`：颜色、字体、字号、间距和动画时间。
- `src/components/`：所有看板可复用的交互组件。
- `src/api/client.ts`：统一响应信封、业务错误、超时、取消及筛选参数。
- `src/composables/useOverviewMotion.ts`：总览局部滚动与入场，离开路由时销毁。
- `src/data/overview.ts`：首页内容与角色入口；避免在组件中散写业务文案。
- `public/reference-icons/`：参考站 SVG/Lottie 图标，来源见设计文档。

完整组件约定、样式与动效来源见 `../docs/frontend-design-system.md`。

具体分工、接口边界和 PR 拆分见 [前端协作交接](../docs/frontend-handoff.md)。

## 招商专员看板

打开 `/specialist`，输入企业名称或选择环节，点击箭头或按回车检索。点击卡片右上角箭头查看企业画像、评分构成、投资事件与地域布局。规则说明从搜索框旁的按钮进入。

- 页面：`src/pages/specialist/index.vue`、`SpecialistDetail.vue`
- 请求与类型：`src/api/scoring.ts`
- 品牌映射：`src/data/enterpriseLogos.ts`；素材来源：`public/enterprise-logos/SOURCES.md`
- 评分接口与配置：[D4 规则引擎](../docs/scoring-engine.md)

前端请求同源 `/api/v1`。若出现连接错误，先确认 FastAPI 服务位于8000端口，再重新检索。
