# Inflation Dashboard 项目评估报告

**评估日期：** 2026-03-23
**评估范围：** 项目整体状态、数据时效性、自动化流程、扩展机会
**项目地址：** https://jing-ny.github.io/inflation-dashboard/
**代码仓库：** https://github.com/jing-ny/inflation-dashboard

---

## 总体评分：3.0 / 5

项目架构清晰、前端展示质量高、数据源选择合理。但数据已过期近 2 个月，自动化管道存在结构性缺陷导致数据无法自动更新，多个脚本存在 bug 或 placeholder 代码。项目处于「能跑但没在跑」的状态。

---

## 优先级 1：现有网页更新

### 1.1 网页当前状态

**网页可正常加载，但数据已过期。**

线上 `historical_cpi.json` 的 `last_updated` 为 **2026-02-02**，所有国家 CPI 数据停留在 **2025 年 12 月**。今天是 2026-03-23，意味着：

- 2026 年 1 月数据已发布（多数国家 2 月中旬前发布完毕）
- 2026 年 2 月数据已发布或即将发布（多数国家 3 月中旬前发布）
- 网页落后约 **2 个月**

Central Bank Forecast 数据（`cb_forecasts.json`）标注为 January 2026，同样有约 2 个月滞后。

| 数据类别 | 线上最新 | 应有最新 | 滞后 |
|----------|----------|----------|------|
| US CPI | 2025-12 (2.7%) | 2026-02 (~2.8%) | ~2 个月 |
| EA HICP | 2025-12 (1.9%) | 2026-02 | ~2 个月 |
| UK CPI | 2025-12 (3.4%) | 2026-02 | ~2 个月 |
| CB Forecasts | Jan 2026 | Mar 2026（多家央行已更新） | ~2 个月 |
| IMF WEO | Oct 2025 | Oct 2025（下次 Apr 2026） | 正常 |

### 1.2 数据过时的根因分析

根因不是 cron 没跑——**GitHub Actions 每周一都在正常执行**（最近一次 2026-03-23 成功运行）。问题在于：

**核心问题：FRED API 数据严重滞后，自动化流程依赖 FRED 作为唯一数据源。**

1. **FRED 滞后**：`fetch_historical_cpi.py` 主要从 FRED API 拉取数据。FRED 的 OECD 系列通常比各国统计局官方发布滞后 **1-6 个月**。脚本中已标注多个国家的 `lag_months`（UK: 2, CA: 2, ZA: 6, AU: 3）。
2. **无新数据 = 无提交**：`update-data.yml` 每周拉取 FRED，如果 `git diff --quiet docs/data/`（无变更），就不会 commit。FRED 没新数据 → 永远不会更新。
3. **手动更新工具存在但未使用**：项目提供了 `update_cpi.py` 和 `batch_update_cpi.py` 供手动录入，但需要人工查看各国官方源并手动输入。
4. **ECB API 是例外**：Euro Area 直接从 ECB API 获取，时效性较好，但其他 12 个国家都依赖 FRED。
5. **Monitor workflow 失败**：`Monitor & Update Data` 工作流在 "Commit and push" 步骤持续失败（最近两次 3/19 和 3/23 均失败），原因是 `monitor_updates.py` 使用 `continue-on-error: true` 后续步骤尝试 commit 不存在的变更。

### 1.3 让网页恢复最新的具体步骤

#### 短期修复（立即可做，~1-2 小时）

1. **手动更新 CPI 数据**：使用已有工具逐国更新
   ```bash
   # 查看各国官方源（URL 在 CPI_UPDATE_GUIDE.md 中）
   # 录入 2026-01 和 2026-02 的数据
   python3 update_cpi.py -c US -d 2026-01 -v <值>
   python3 update_cpi.py -c US -d 2026-02 -v <值>
   # 对所有 13 个国家重复
   ```

2. **更新 Central Bank Forecasts**：手动编辑 `docs/data/cb_forecasts.json`
   - 2026 年 1-3 月已有多家央行更新预测（Fed 3 月 FOMC、ECB 3 月会议、BoE 2 月 MPR 等）
   - 需逐一核实并更新

3. **提交并推送**
   ```bash
   git add docs/data/
   git commit -m "Update CPI and forecast data to Feb/Mar 2026"
   git push
   ```

#### 中期修复（建议优先做，防止再次过期）

详见优先级 2 的自动化改进建议。核心是：为 FRED 滞后的国家添加直接 API 源（各国统计局或 ECB/OECD 直接 API），减少对 FRED 的依赖。

### 1.4 改进项总结

| 改进项 | 工作量 | 影响 |
|--------|--------|------|
| 手动更新全部 13 国 CPI 到最新 | 1-2 小时 | 高——立即恢复数据时效 |
| 手动更新 CB Forecasts | 1-2 小时 | 高——恢复央行预测时效 |
| 为 US 添加 BLS 直接 API 源 | 2-3 小时 | 高——US 是最重要的国家 |
| 为 UK/CA/AU 等添加直接源 | 每国 1-2 小时 | 中——减少 FRED 依赖 |
| 修复 Monitor workflow 的 commit 逻辑 | 30 分钟 | 中——消除虚假失败 |

---

## 优先级 2：项目整体健康度

### 2.1 项目结构

```
inflation-dashboard/
├── docs/                      # GitHub Pages 部署目录
│   ├── index.html             # 主页（动态加载 JSON）
│   ├── {country}.html         # 13 个国家详情页
│   ├── country.js             # 国家页共享逻辑
│   ├── styles.css             # 全局样式
│   └── data/                  # 数据（单一数据源）
│       ├── historical_cpi.json
│       ├── cb_forecasts.json
│       ├── imf_forecasts.json
│       └── ...
├── scripts/                   # Python 数据脚本
│   ├── fetch_historical_cpi.py
│   ├── monitor_updates.py
│   ├── auto_scrape_cb_forecasts.py
│   └── ...
├── .github/workflows/         # CI/CD
│   ├── update-data.yml
│   ├── monitor-updates.yml
│   ├── weekly-alert.yml
│   └── auto-scrape-cb-forecasts.yml
├── update_cpi.py              # 手动更新工具
├── batch_update_cpi.py        # 批量更新工具
└── 文档 (README, METHODOLOGY, CPI_UPDATE_GUIDE 等)
```

**架构评价：** 结构清晰合理。`docs/data/` 作为单一数据源的决策是正确的。前端纯静态 HTML/JS + GitHub Pages 的方案对于这个规模的项目是最优选择——零运维成本、零托管费用。

### 2.2 正常工作的部分

| 组件 | 状态 | 说明 |
|------|------|------|
| 前端页面渲染 | ✅ 正常 | 数据表格、图表、国家详情页均可正常加载 |
| GitHub Pages 部署 | ✅ 正常 | 自动部署，提交即上线 |
| `update-data.yml` | ✅ 运行中 | 每周一执行，但因 FRED 滞后无新数据 |
| `weekly-alert.yml` | ✅ 运行中 | 每周一执行 |
| `auto-scrape-cb-forecasts.yml` | ✅ 运行中 | 每周一/四执行 |
| 手动更新工具 | ✅ 可用 | `update_cpi.py`、`batch_update_cpi.py` |
| 13 国数据覆盖 | ✅ 完整 | 包含主要经济体 + 新兴市场 |
| Substack Newsletter 嵌入 | ✅ 正常 | 已嵌入订阅表单 |
| 国家详情页 Chart.js 图表 | ✅ 正常 | 10 年历史数据可视化 |

### 2.3 问题和 Bug

#### 严重问题

1. **数据过期（已在优先级 1 详述）**

2. **`styles.css` 中 CSS 规则重复 5 次（约 840 行冗余）**
   `docs/styles.css` 共 1279 行，其中 `.policy-change-*` 和 `.target-new-badge` 等样式块被完整复制了 5 次。原始样式约 170 行，冗余约 680 行。不影响功能但增加页面加载大小，表明代码是通过多次 append 而非替换方式修改的。

3. **`index.html` 末尾有测试文本**
   `docs/index.html` 第 397 行有一个裸露的 `test` 文本，在页面底部可能可见。

4. **`monitor_updates.py` 和 `fetch_historical_cpi.py` 使用不同的 FRED 系列**
   | 国家 | fetch_historical_cpi.py | monitor_updates.py |
   |------|------------------------|-------------------|
   | US | CPIAUCNS（NSA index） | CPIAUCSL（SA） |
   | EA | ECB API | CP0000EZ19M086NEST（FRED） |
   | JP | JPNCPIALLMINMEI | FPCPITOTLZGJPN |

   两个脚本对同一国家使用不同系列，可能导致数值不一致。

5. **`send_weekly_alert.py` 使用错误的数据路径**
   第 47-48 行：`CURRENT_DATA_FILE = os.path.join(DATA_DIR, "historical_cpi.json")`，其中 `DATA_DIR = "data"`。正确路径应为 `docs/data/historical_cpi.json`。第 194 行的 `create_current_snapshot` 使用 `data.get("countries", {})` 但 JSON 的顶层 key 是国家代码，不是 `countries`。这意味着 **weekly alert 功能完全不工作**。

6. **`auto_scrape_cb_forecasts.py` 缺少 CLI 参数**
   工作流传入 `--force`、`--country`、`--dry-run` 参数，但 `main()` 函数没有使用 `argparse`，这些参数会被忽略。scraper 总是运行所有国家，无法控制。

7. **`monitor_updates.py` 的 `update_forecast_history()` 是 placeholder**
   函数体只有 `pass`，forecast 历史追踪功能从未实现。

#### 中等问题

8. **CB Forecast scraper 使用硬编码 URL**
   `auto_scrape_cb_forecasts.py` 中 ECB、BoE、RBA 等的 fallback URL 硬编码为 2024 年的页面（如 `november-2024`），虽然有动态发现逻辑，但 fallback 已过期。

9. **`auto_scrape_cb_forecasts.py` 禁用了 SSL 验证**
   第 27-28 行：`ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE`。安全风险。

10. **日本和韩国 FRED 系列已停更**
    脚本注释中已标注 `JPNCPIALLMINMEI`（COICOP 1999）和 `KORCPIALLMINMEI`（discontinued Nov 2023），这两个国家的自动更新本质上已失效。

11. **`inflation_data.js` 是冗余文件**
    `docs/data/inflation_data.js` 是 `historical_cpi.json` 的 JS 变量版本，前端已改为直接 fetch JSON，但 JS 文件仍被生成（`fetch_historical_cpi.py` 第 602 行之前的旧逻辑）。可能造成混淆。

#### 轻微问题

12. **API 密钥曾被提交到 git 历史**
    commit `c681654` 的消息是 "removed hardcoded API keys"，表明 FRED API key 等曾存在于代码或配置文件中。虽然当前 `.env.local` 在 `.gitignore` 中，但密钥可能仍存在于 git 历史。`.env.local` 当前包含 Supabase、FRED、Resend 的 API key。

13. **存在未使用的脚本**
    `scripts/fetch_us.py`, `scripts/fetch_uk.py`, `scripts/fetch_nz.py`, `scripts/fetch_de.py` 等单国脚本看起来是被 `fetch_historical_cpi.py` 整合后遗留的。

14. **`load_us_to_supabase.py` 看起来是实验性的**
    存在 Supabase 集成脚本但似乎未在生产流程中使用。

### 2.4 改进项总结

| 改进项 | 工作量 | 影响 |
|--------|--------|------|
| 清理 styles.css 重复代码 | 15 分钟 | 低——减少约 680 行冗余 |
| 删除 index.html 末尾 `test` 文本 | 1 分钟 | 低——消除页面瑕疵 |
| 统一 monitor 和 fetch 的 FRED 系列 | 30 分钟 | 中——消除数据不一致风险 |
| 修复 send_weekly_alert.py 数据路径 | 15 分钟 | 中——让 weekly alert 能工作 |
| 给 auto_scrape 添加 argparse | 30 分钟 | 中——让 workflow 参数生效 |
| 实现 forecast history 追踪 | 1-2 小时 | 中——可追踪预测修订 |
| 轮换曾泄露的 API 密钥 | 15 分钟 | 高——安全最佳实践 |
| 清理遗留的单国 fetch 脚本 | 15 分钟 | 低——减少混淆 |

---

## 优先级 3：Newsletter 自动化

### 3.1 设计方案

**目标：** 每当有新的 CPI 数据发布或显著变动时，自动生成英文 newsletter draft，供人工审阅后通过 Substack 发布。

#### 架构

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Data Update  │────▶│ Change Detection│────▶│ Claude API Draft │
│ (fetch/manual)│     │ (diff + rules)  │     │ Generation       │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                       │
                                              ┌────────▼─────────┐
                                              │ Draft Output     │
                                              │ (MD + preview)   │
                                              └────────┬─────────┘
                                                       │
                                              ┌────────▼─────────┐
                                              │ Human Review     │
                                              │ → Substack Post  │
                                              └──────────────────┘
```

#### 流程详细设计

**Step 1：变动检测** (`scripts/detect_changes.py`)
- 比较当前 `historical_cpi.json` 与上次快照
- 分类变动级别：
  - **Material**：≥0.3pp 变化，或方向反转（升→降/降→升）
  - **Notable**：新国家数据发布，或央行预测更新
  - **Minor**：<0.3pp 的常规变化
- 只在有 Material 或 Notable 变动时触发 draft 生成

**Step 2：Claude API 生成 Draft** (`scripts/generate_newsletter.py`)
- 输入：变动数据 + 上次 newsletter 摘要 + 央行日历
- 通过 Claude API（anthropic Python SDK）生成结构化 draft
- Newsletter 内容模板：

```
## Inflation Update — [Week/Month of YYYY-MM-DD]

### Key Changes This Period
- [Country]: X.X% → Y.Y% (±Z.Zpp) — [brief context]

### Trend Direction
[2-3 sentences on whether global inflation is broadly rising,
falling, or diverging across regions]

### Central Bank Implications
[What the data means for upcoming policy decisions.
Which banks are under pressure to act?]

### Looking Ahead
- Next major release: [Country] on [date]
- Upcoming CB meetings: [list]

---
Data as of [date]. All figures from official government statistics.
Full dashboard: https://jing-ny.github.io/inflation-dashboard/
```

- Prompt 设计要点：
  - 要求纯事实陈述，不做预测
  - 限制在 300-500 词
  - 引用具体数字和来源
  - 语气专业但可读

**Step 3：输出与审核**
- Draft 保存为 `drafts/newsletter_YYYY-MM-DD.md`
- 可选：通过 GitHub Actions 创建 PR 或发送 email 通知
- 人工审阅后，复制到 Substack 编辑器发布

#### 发送频率

建议 **事件驱动 + 月度兜底**：
- 当有 Material 变动时立即生成 draft
- 若连续 30 天无 Material 变动，也生成一期 "no significant changes" 的简短更新
- 预计每月 1-2 期，全年 12-20 期

### 3.2 技术实现

```python
# scripts/generate_newsletter.py 核心结构
import anthropic
import json

def generate_draft(changes, current_data, cb_calendar):
    client = anthropic.Anthropic()  # 从环境变量读取 API key

    prompt = f"""You are a financial data analyst writing a brief inflation
    update newsletter. Write factually, cite specific numbers, no predictions.

    Current data: {json.dumps(current_data, indent=2)}
    Changes since last update: {json.dumps(changes, indent=2)}
    Upcoming CB meetings: {json.dumps(cb_calendar, indent=2)}

    Write the newsletter in the following structure:
    1. Key Changes (bullet points with numbers)
    2. Trend Direction (2-3 sentences)
    3. Central Bank Implications (2-3 sentences)
    4. Looking Ahead (upcoming releases and meetings)

    Keep it under 500 words. English only."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

**GitHub Actions 集成** (`newsletter-draft.yml`)：
- 触发条件：`historical_cpi.json` 变更时 或 手动触发
- 生成 draft → 保存为 artifact → 发 email 通知审阅

### 3.3 实现路线图

| 阶段 | 内容 | 工作量 | 前置条件 |
|------|------|--------|----------|
| Phase 1 | 变动检测脚本 | 2-3 小时 | 无 |
| Phase 2 | Claude API 集成 + draft 生成 | 3-4 小时 | Anthropic API key |
| Phase 3 | GitHub Actions 自动化 | 1-2 小时 | Phase 1+2 |
| Phase 4 | Draft → email 通知 | 1 小时 | Phase 3 + Resend 已配置 |
| Phase 5 | 模板迭代和质量调优 | 持续 | Phase 4 |

**总工作量：** 约 8-12 小时开发 + 持续调优
**按每周几小时投入：** 约 2-3 周完成基础版本

### 3.4 成本估算

- Claude API：每次 draft 约 ~2K input tokens + ~1K output tokens ≈ $0.01/次
- 每月 2 次 ≈ $0.02/月（可忽略不计）
- Resend：免费额度 100 emails/天，完全够用

### 3.5 改进项总结

| 改进项 | 工作量 | 影响 |
|--------|--------|------|
| 实现变动检测（已有 send_weekly_alert.py 可复用） | 2-3 小时 | 高——newsletter 基础 |
| Claude API draft 生成 | 3-4 小时 | 高——核心功能 |
| GitHub Actions 集成 | 1-2 小时 | 中——自动化 |
| Email 通知审阅 | 1 小时 | 中——提高响应速度 |
| Substack API 直接发布（可选） | 2-3 小时 | 低——手动复制也可 |

---

## 优先级 4：扩展机会

### 4.1 可追踪的高价值通胀指标

| 指标 | 说明 | 数据源 | 可行性 |
|------|------|--------|--------|
| **Core CPI（核心 CPI）** | 剔除食品和能源，更能反映通胀趋势 | FRED、各国统计局 | 高——多数国家有 FRED 系列 |
| **PCE Price Index（美国）** | Fed 实际盯住的指标，比 CPI 更重要 | FRED (PCEPI) | 高——直接加即可 |
| **PPI（生产者价格指数）** | 通胀的领先指标 | FRED | 中——数据量大，需选择性展示 |
| **实际利率** | 政策利率 - 通胀率 | 可计算 | 高——已有两个数据源 |
| **通胀预期** | 市场隐含通胀预期（TIPS 利差等） | FRED (T5YIE, T10YIE) | 中——仅美国和少数国家有 |
| **食品通胀** | 社会影响最大的分项 | 各国统计局 | 中——数据格式不统一 |
| **住房/房租通胀** | 美国 CPI 最大权重分项 | FRED (CUSR0000SEHA) | 中——仅部分国家 |

**建议优先添加**：Core CPI 和 US PCE，工作量小（2-3 小时），对专业用户价值很高。

### 4.2 国家扩展

当前覆盖 13 个经济体。可考虑：

| 优先级 | 国家/地区 | 理由 | 数据源可行性 |
|--------|-----------|------|-------------|
| 高 | 🇧🇷 巴西 | 拉美最大经济体，通胀波动大 | FRED 有系列 |
| 高 | 🇲🇽 墨西哥 | 北美贸易伙伴，USMCA 关注 | FRED 有系列 |
| 中 | 🇮🇩 印尼 | 东南亚最大经济体 | FRED 有系列 |
| 中 | 🇹🇷 土耳其 | 极端通胀案例（>60%）| FRED 有系列 |
| 中 | 🇵🇱 波兰 | 2025 加入欧元区，转型案例 | ECB API |
| 低 | 🇹🇭 泰国 | ASEAN 经济体 | FRED 有系列 |
| 低 | 🇳🇬 尼日利亚 | 非洲最大经济体 | 数据质量不稳定 |

**建议**：优先加巴西和墨西哥（每国 1-2 小时），可复用现有 FRED 管道。

### 4.3 功能扩展

| 功能 | 说明 | 工作量 |
|------|------|--------|
| 通胀排名/排序 | 主页表格支持点击排序 | 1-2 小时 |
| 历史对比 | 选择两个国家叠加图表 | 3-4 小时 |
| RSS Feed | 自动生成 RSS 供订阅 | 2 小时 |
| 数据导出 | 下载 CSV/JSON | 1 小时 |
| 暗色模式 | 用户体验 | 1-2 小时 |

### 4.4 改进项总结

| 改进项 | 工作量 | 影响 |
|--------|--------|------|
| 添加 Core CPI + US PCE | 2-3 小时 | 高——专业用户核心需求 |
| 添加实际利率计算 | 1 小时 | 中——无需新数据源 |
| 扩展巴西、墨西哥 | 每国 1-2 小时 | 中——增加覆盖面 |
| 表格排序 | 1-2 小时 | 低——用户体验提升 |
| 历史对比图表 | 3-4 小时 | 中——差异化功能 |

---

## 附录：各国官方数据源 URL

用于手动更新时的快速参考。

| 国家 | 统计局 | CPI 发布页 | 央行预测页 |
|------|--------|-----------|-----------|
| US | BLS | https://www.bls.gov/cpi/ | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm |
| EA | Eurostat | https://ec.europa.eu/eurostat/ | https://www.ecb.europa.eu/press/projections/html/index.en.html |
| UK | ONS | https://www.ons.gov.uk/economy/inflationandpriceindices | https://www.bankofengland.co.uk/monetary-policy-report |
| CA | StatCan | https://www150.statcan.gc.ca/n1/daily-quotidien/index-eng.htm | https://www.bankofcanada.ca/publications/mpr/ |
| AU | ABS | https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/ | https://www.rba.gov.au/publications/smp/ |
| NZ | Stats NZ | https://www.stats.govt.nz/indicators/consumers-price-index-cpi/ | https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement |
| ZA | Stats SA | https://www.statssa.gov.za/ | https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements |
| JP | MIC | https://www.stat.go.jp/english/data/cpi/ | https://www.boj.or.jp/en/mopo/outlook/ |
| CN | NBS | https://www.stats.gov.cn/english/ | （PBOC 不发布通胀预测，使用 IMF WEO） |
| IN | MOSPI | https://www.mospi.gov.in/ | https://www.rbi.org.in/Scripts/PublicationsView.aspx |
| KR | KOSTAT | https://kostat.go.kr/en/ | https://www.bok.or.kr/eng/main/main.do |
| SG | SingStat | https://www.singstat.gov.sg/ | https://www.mas.gov.sg/monetary-policy |
| VE | BCV | https://www.bcv.org.ve/ | （使用 IMF WEO） |

---

*报告生成于 2026-03-23。本报告仅评估项目状态，未修改任何代码。*
