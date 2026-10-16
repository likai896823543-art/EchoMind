# EchoMind — 多 Agent 客服编排运行时

面向金融理财与会员权益场景的多 Agent 智能客服系统。EchoMind 不是单轮问答机器人，而是把**意图识别 → 路由 → 多 Agent 编排 → 知识检索 → 分层记忆 → 在线评测**串成闭环的 LLM 应用运行时。

## 功能特性

- **多 Agent 编排**：8 类领域 Agent 池化并发执行，主辅 Agent 并行协作与结果合成；每个 Agent 通过"角色契约 + 工具白名单"限定可用工具，实现权限隔离，可无缝升级人工坐席。
- **三路融合意图识别**：LLM / Embedding / 规则三路加权投票（0.7 / 0.2 / 0.1），组级聚合 + 组内细化，覆盖 **28 类细粒度业务意图**（基金赎回、账户冻结、合规投诉、会员权益等）与 4 级紧急度；约 500 条评测用例下准确率 **91.3%**、宏平均 **F1 0.89**。
- **高风险操作拦截**：路由层解析金额实体，赎回超 5 万元 / 账户冻结 / 全额赎回直接转人工核验；理财产品输出强制合规披露；会员积分涉钱场景由 BillingAgent 协作兜底。
- **分层记忆**：Redis 24h 工作记忆 + ChromaDB 情景记忆与用户画像，15 条消息自动压缩；知识检索由 Agent 工具循环按需触发，查询改写 + 多路并行召回 + 重排，回答准确率 **88.7%**、检索召回率 **91.2%**。
- **动态 Skills**：8 类 Skills 热加载（计费、投诉、会员、售前、产品咨询、风险告警、技术支持、通用客服），按意图动态注入。
- **可观测与评测闭环**：请求级工具轨迹可观测（request_id 串联 + /trace/tool 接口）；Monitor 在线监控 + 单实例降权回退；LLM-as-Judge 四维评测闭环（5 组端到端、0.75 通过线、指标退化 5% 自动标记回归）；工具层 300s 缓存、30s 超时、熔断降级。

## 架构总览

```
用户消息
   │
   ▼
意图识别（LLM 0.7 / Embedding 0.2 / 规则 0.1 加权投票）
   │
   ▼
路由层（28 类意图 × 4 级紧急度 → 高风险拦截 → 人工坐席升级）
   │
   ▼
Agent 池（8 类领域 Agent，角色契约 + 工具白名单）
   │  ├── 分层记忆（Redis 工作记忆 / ChromaDB 情景记忆）
   │  ├── RAG 工具（按需触发，多路召回 + 重排）
   │  └── Skills 热加载
   │
   ▼
结果合成 → 合规披露 → 响应
```

## 技术栈

Python / FastAPI / Anthropic Claude / DeepSeek / Redis / ChromaDB / Docker / Prometheus / Vue 3 (前端)

## 目录结构

```
EchoMind-github/
├── backend/                  # 后端服务
│   ├── agents/               # Agent 编排（orchestrator + 工具）
│   ├── api/                  # FastAPI 入口（含 /trace/tool 观测接口）
│   ├── core/                 # 意图识别、LLM 工具、Skill 加载
│   ├── config/               # Prometheus、Nginx 配置
│   ├── data/                 # 示例知识库与评测样例
│   ├── evaluation/           # LLM-as-Judge 评测闭环
│   ├── mcp/                  # 知识库 / 工具管理器
│   ├── memory/               # 分层记忆
│   ├── monitor/              # 在线监控与降权
│   ├── skills/               # 8 类 Skills（SKILL.md）
│   ├── tests/                # 单元与端到端测试
│   └── wiki/                 # 项目文档
├── frontend/                 # Vue 3 前端
└── README.md
```

## 快速开始

### 1. 准备

- Docker + Docker Compose
- Anthropic 协议兼容的模型 API Key（支持 Claude 或 DeepSeek 等兼容服务）

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Key
```

### 3. 启动

```bash
cd backend
docker compose up -d
```

服务启动后：

- API 文档：`http://localhost:8000/docs`
- 工具轨迹观测：`GET /trace/tool`
- 监控指标：`http://localhost:9090`

### 4. 运行测试与评测

```bash
cd backend
pytest tests/

# 运行评测（需服务已启动）；首次运行后自动生成 data/eval/baseline.json 作为基线
curl -X POST http://localhost:8000/eval/run
```

## 评测

- 意图识别：约 500 条自建评测用例，准确率 91.3%，宏平均 F1 0.89（首次运行 `POST /eval/run` 后自动生成基线文件）
- RAG 问答：回答准确率 88.7%，检索召回率 91.2%
- LLM-as-Judge 四维评测：5 组端到端用例，0.75 通过线，指标退化 5% 自动标记回归

## License

MIT
