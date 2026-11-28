# 前端组件、视觉与动效交接 v0.1

共享框架与总览页由框架分支提供。当前业务分支新增招商专员看板与D4评分；D1/D5及另两个业务看板仍待各自负责人开发。

## 1. 视觉规范

变量唯一入口：`frontend/src/styles/tokens.css`。禁止在不同看板创建第二套主题或修改全局 body 滚动。主色 `#5986FA`，hover `#298DFF`；页面 `#000000`、卡片 `#131518`、卡片 hover `#222529`、导航图标底 `#343940`，必须分清。纸白区 `#FFFFFF`，流程区 `#F4F5F7`。方角；细点分隔；不使用默认圆角卡片或紫色渐变。

字体为本地 npm 字体文件：Inter + Noto Sans SC，常规 400，少量 500。参考站是 TWK Everett，本项目没有该商业字体授权，未复制字体文件。中文不照搬英文极端负字距。网页用 CSS px，不用印刷 pt。

在 1280px 参考视口：正文16/22.4，导航14.222，卡片标题18.674，按钮12.444，CTA高度42.667。原站 hero 英文80/80；本项目使用随视口变化的英文标题。导航匿名图标约25px高；导航十字框23.104px，十字本体9px。不要为了填满卡片放大文字。

## 2. 组件 API

```vue
<UiButton label="保存设置" :loading="saving" :disabled="invalid" @click="save" />
<UiButton label="重置" variant="light" @click="reset" />
<RevealLink to="/specialist" text="进入看板" />
<RoleCard title="招商专员" english="For specialists"
  description="筛选目标企业，判断招商价值。"
  :details="['组合条件筛选','查看企业画像','比较适配评分']"
  to="/specialist" icon="target" />
```

`UiButton` 支持 primary/dark/light、loading/disabled、原生 type 和事件。`RevealLink` 是导航链接；`embedded` 只供外层已经是链接的 `RoleCard` 使用，避免嵌套链接。`FlipText` 给字符生成双层内容；可读名称保留，装饰字符对读屏隐藏。`UiIcon` 提供 cross/logo/arrow/target/document/star。`AnimatedIcon` 为原站 Lottie 包装，不在不同看板重复初始化全局动画。

已有 `.ui-field`、`.ui-tag`、`.ui-table`、`.state-panel` 等基础类；新增复杂组件先放 components，再在此记录用途。空值显示“暂无资料”，不得把缺失数据记作0分或编造企业信息。

## 3. 数据契约

使用 `request<T>('/path')`，它处理后端 `{code,message,data}`；特别注意业务错误可能仍是 HTTP200。不要只判断 HTTP 状态。内置10秒超时，支持 AbortSignal，离开页面应取消请求。原生路径已统一带 `/api/v1`。

```ts
import { getEnterprises } from '../api/client'
const page = await getEnterprises({ chain_segment: '先进封装', page: 1 })
```

接口参数遵循数据岗契约。D4接口契约见 `scoring-engine.md`，业务接口与画像保持独立，不把评分塞入数据岗画像接口。Workspace 骨架只读取 A3 导入状态用于显示真实连接结果。

## 4. 代码级参考与实现映射

来源： https://www.sui.io/ ，2026-11-25读取公开 DOM、计算样式及公开脚本：

- https://assets.slater.app/slater/17378/50007.js?v=924206 （global）
- https://assets.slater.app/slater/17378/50689.js?v=25606 （homepage）
- https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/css/sui-v2.shared.85e166a51.min.css

| 原站机制 | 本项目实现 | 范围 |
| --- | --- | --- |
| `initArrowReveal`：背景scaleX从0到1，原点0%50%，0.4s expo.out；文字y=-100%，stagger0.01s | `RevealLink` + `FlipText`，CSS等效缓动与逐字延迟；箭头保持原形，背景展开配合逐字翻转 | 鼠标、键盘焦点都可触发；整张卡片hover也展开CTA |
| `shuffleHover`：固定字符宽度后置换字符，避免文字抖动 | 导航使用固定宽度字符扰动与原始十字SVG旋转 | 按原站字符更新与错位节奏重建，最终恢复中文 |
| Lenis `lerp:.12`，GSAP ticker联动 | `useOverviewMotion` 同步ticker、ScrollTrigger | 仅总览页；路由销毁，不污染其他看板 |
| 首页暂停/播放/释放3D场景，非简单CSS scroll-snap | 仅保留连续平滑滚动、Hero视差和入场动画；按用户要求取消分区卡点 | 适配已确认的三段总览；没有复制原站无关3D视频和长剧情 |
| `lottieReveal` 图标进入时播放 | `AnimatedIcon` 进入可视区播放一次，hover重播 | 原站4个JSON本地托管；笔图标为原始SVG |
| 企业滚动条 DEFAULT_SPEED75，克隆轨道无缝循环 | 两组等宽企业条，线性无限循环 | hover 不暂停；不显示播放暂停文字；速度由CSS时长统一调整 |
| 卡片列表连接线clipPath展开 | GSAP逐项揭示L形连接线 | 与卡片入场配合 |

这是一套基于原站代码机制的重建和业务适配，不能宣称“原站所有动画逐帧一致”。导航不提供原站不需要的巨型菜单。没有把原站埋点、Cookie、第三方表单、翻译或API键复制进应用。

## 5. 滚动与降级

所有尺寸均为连续滚动，不拦截滚轮或 PageUp/PageDown，不锁定、吸附或固定分区。保留 Lenis 平滑滚动、Hero 视差、流程首次字符/底色闪现、图标及卡片入场。动效默认启用，不提供开关，不读取旧的浏览器动效设置。企业 Logo 滚动带持续滚动，悬停不暂停。所有 GSAP context、ticker、IntersectionObserver、Lottie 在卸载时清理。

## 6. 素材来源

导航cross、笔、CTA箭头、L形连接线来自原站公开SVG；check/research/shield/performance的JSON来自原站DOM `global-src`。文件位于 `frontend/public/reference-icons/`。保留这些来源信息；正式对外发布前由团队决定是否继续使用参考站素材或换成自有版本。

企业带已接入士兰微、杰华特、联芸科技的真实Logo图片，来源见 `frontend/public/enterprise-logos/SOURCES.md`。未取得素材的企业暂不显示；后续在 `data/overview.ts` 扩充。不用AI重绘或普通文字替代Logo，不声称这些企业是合作客户。没有边缘黑色渐隐或播放暂停文字。Hero 为CSS渐变。

## 7. 各同学接入步骤

1. 从团队约定的分支取得 frontend，`npm ci` 后运行。
2. 在 `src/pages/` 新建自己负责的页面，修改 router 中对应路由。
3. 复用 App、Header、Footer、tokens 和 api client；不要另搭HTML壳或数据库副本。
4. 使用 UiButton / RevealLink / 表单与表格基础样式，补齐loading/error/empty/disabled。
5. 验证路由直达、刷新、键盘焦点、手机窄屏、减少动态效果模式。
6. 提交时说明新组件、接口依赖、完成范围和验证结果；未完成内容如实标注。
