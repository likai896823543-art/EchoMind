# EchoMind 场景扩展指南

这份指南整理了 EchoMind 当前架构中无需修改即可复用的能力，以及把系统扩展到新场景（电商、政务、企业内部答疑等）时需要调整的部分，供参考。使用中遇到问题或有新的扩展想法，欢迎在 GitHub Issues 讨论。

## **当前架构可复用能力总览**

在考虑扩展之前，先明确哪些部分是**无需修改即可复用**的：

扩展一个新场景，核心工作是：

1. **定义新意图类别**（`IntentCategory`）

2. **编写对应的 Agent 类和 Skill**

3. **导入领域知识库文档**

4. **在路由表和打分函数里注册新 Agent**

## **场景一：医疗健康咨询助手**

### **场景描述**

医院、诊所、健康平台的在线问诊分流、用药咨询、挂号引导、报告解读预处理。

### **需要新增的 Agent**

### **需要新增的意图**

```Python
IntentCategory.SYMPTOM_QUERY      # 症状咨询
IntentCategory.MEDICATION_QUERY   # 用药问题
IntentCategory.APPOINTMENT        # 预约挂号
IntentCategory.REPORT_QUERY       # 检查报告查询
IntentCategory.EMERGENCY          # 急症识别（触发 CRITICAL 紧急度）
```

### **关键扩展点**

- **紧急度升级**：识别到急症关键词（胸痛、呼吸困难、意识丧失）时，`UrgencyLevel.CRITICAL` 直接路由到 `EscalationAgent` 并提示拨打急救电话

- **知识库内容**：药品说明书、科室介绍、常见病问答、挂号流程

- **合规约束**：在 Skill 里明确写入"不替代医生诊断"的输出限制

### **Skill 片段示例**

```Markdown
# 医疗健康咨询规范
## 核心原则
- 只提供信息参考，不做诊断结论，不开处方
- 涉及急症症状（胸痛/呼吸困难/高烧超过39.5℃）必须建议立即就医或拨打120
- 不评论其他医院或医生的诊疗方案
```

---

## **场景二：企业内部 IT 支持台（Helpdesk）**

### **场景描述**

替代传统工单系统的第一道分流，处理员工的设备故障、系统权限申请、办公软件问题、网络故障上报。

### **需要新增的 Agent**

### **需要新增的意图**

```Python
IntentCategory.DEVICE_FAILURE    # 设备故障
IntentCategory.PERMISSION_REQUEST # 权限申请
IntentCategory.NETWORK_ISSUE     # 网络问题
IntentCategory.SOFTWARE_INSTALL  # 软件安装/更新
IntentCategory.IT_ESCALATION     # 转 IT 工单
```

### **关键扩展点**

- **工具扩展**：在 `tools.py` 里接入 IT 资产管理系统 API（`lookup_asset`）和工单系统（`create_ticket`）

- **实体扩展**：提取设备编号、工号、操作系统版本作为新的 entity

- **知识库内容**：IT 操作手册、VPN 安装教程、常见系统错误解决方案、权限申请 SOP

### **与现有代码的复用关系**

现有的 `lookup_error_code` 工具和 `build_diagnostic_plan` 工具可以**直接复用**，只需补充 IT 场景特有的错误码映射（如 Active Directory 错误码）。

---

## **场景三：金融理财客服**

### **场景描述**

银行、券商、基金平台的产品咨询、账户查询引导、风险提示、投诉处理。

### **需要新增的 Agent**

### **需要新增的意图**

```Python
IntentCategory.PRODUCT_QUERY      # 产品咨询
IntentCategory.RISK_DISCLOSURE    # 风险说明
IntentCategory.COMPLIANCE_COMPLAINT # 合规投诉
IntentCategory.FUND_REDEMPTION    # 赎回/转出
IntentCategory.ACCOUNT_FREEZE     # 账户冻结
```

### **关键扩展点**

- **强制合规输出**：在 Skill 里注入"过往收益不代表未来收益"等合规话术，无法被 Agent 绕过

- **高风险操作拦截**：金额超过阈值、赎回全部资产等操作，路由到 `EscalationAgent` 要求人工核验

- **双重记忆用途**：用户画像记录风险偏好等级，后续对话根据画像调整产品推荐口径

---

## **场景四：教育培训辅助**

### **场景描述**

在线教育平台的学习辅导、课程答疑、学习计划制定、考试咨询。

### **需要新增的 Agent**

### **需要新增的意图**

```Python
IntentCategory.KNOWLEDGE_QUERY    # 知识点提问
IntentCategory.HOMEWORK_HELP      # 作业辅导
IntentCategory.STUDY_PLAN         # 学习计划
IntentCategory.EXAM_INFO          # 考试信息
IntentCategory.COURSE_RECOMMEND   # 课程推荐
```

### **关键扩展点**

- **知识库结构化**：按学科/章节/难度分类导入，利用 `KnowledgeBase.add_documents()` 批量导入教材内容

- **用户画像增强**：在 `MemoryManager` 的用户画像里记录学科、年级、薄弱章节，实现个性化辅导

- **`search_with_rewrite`**** 的价值**：学生的提问往往不准确（"这个不会"），查询改写能显著提升知识检索召回率

---

## **场景五：SaaS 产品用户支持**

### **场景描述**

B2B SaaS 产品的功能咨询、API 对接支持、订阅/账单管理、企业账户管理。

### **需要新增的 Agent**

### **需要新增的意图**

```Python
IntentCategory.API_INTEGRATION    # API 对接问题
IntentCategory.FEATURE_INQUIRY    # 功能咨询
IntentCategory.ONBOARDING         # 新用户引导
IntentCategory.ENTERPRISE_MGMT   # 企业账户管理
IntentCategory.SUBSCRIPTION       # 订阅管理
```

### **关键扩展点**

- **与现有代码高度重合**：现有的 `TechnicalAgent` 和 `BillingAgent` 可以直接作为基础，扩展 Skill 内容即可

- **知识库**：API 文档（可直接导入 OpenAPI Spec）、功能发布日志、常见集成问题

- **工具扩展**：`lookup_error_code` 直接复用，补充 SaaS 特有的业务错误码

---

---

## **电商场景内部扩展**

当前电商场景已有四个 Agent（General / Technical / Billing / Escalation），但电商业务远比这复杂。以下是在**不改变整体场景、只做纵向细化**的情况下值得拆分的子 Agent。

---

### **扩展 E1：售前导购 Agent（PreSaleAgent）**

**痛点**：当前 GeneralAgent 混合处理售前咨询，但"帮我选一款适合的产品"和"我的订单在哪"是完全不同的诉求，混在一个 Agent 里会导致回复质量下降。

**职责**：商品对比、规格解释、适用场景推荐、礼品建议、选购引导。

**需要新增的意图**

```Python
IntentCategory.PRODUCT_COMPARE     # 商品对比（A 和 B 哪个好？）
IntentCategory.PRODUCT_RECOMMEND   # 导购推荐（给女朋友送什么？）
IntentCategory.SPEC_INQUIRY        # 规格参数（这款支持XX功能吗？）
IntentCategory.AVAILABILITY        # 库存/发货时效（现货吗？几天能到？）
```

**关键扩展点**

- **知识库内容**：商品 FAQ、规格参数表、选购指南、同类商品对比文档

- **工具扩展**：`search_product_catalog`（接入商品搜索 API）

- **用户画像利用**：从 `MemoryManager` 读取历史购买记录，做个性化推荐口径

- **温度设置**：建议 0\.5\-0\.7（比 BillingAgent 高，允许更自然的推荐表达）

**Skill 关键约束**

```Markdown
- 不伪造库存状态（"有货""最后一件"等），只说"请在商品页确认"
- 不承诺配送时效，转引物流政策
- 超过 3 个商品的复杂对比，引导用户到比价页面
```

---

### **扩展 E2：物流纠纷专项 Agent（LogisticsAgent）**

**痛点**：当前物流意图（`LOGISTICS`）路由到 GeneralAgent，但丢件/破损/签收异议是高风险场景，GeneralAgent 的处理边界不够清晰，容易误承诺。

**职责**：物流轨迹说明、异常件处理流程引导、丢件/破损/拒签的举证指引、与快递公司理赔流程说明。

**需要新增的意图**

```Python
IntentCategory.LOGISTICS_LOST      # 疑似丢件（超时未更新轨迹）
IntentCategory.LOGISTICS_DAMAGED   # 破损/错发
IntentCategory.LOGISTICS_DISPUTE   # 签收异议（签了但没收到/被代签）
IntentCategory.LOGISTICS_DELAY     # 延误（承诺时效未到）
IntentCategory.LOGISTICS_ADDRESS   # 地址修改（未发货/已发货）
```

**关键扩展点**

- **实体扩展**：在 `_extract_entities()` 里提取快递单号（`tracking_no`）

- **工具扩展**：`query_logistics`（对接快递查询 API，如顺丰、菜鸟）

- **紧急度升级规则**：丢件超过 7 天 \+ 用户高频催促 → `CRITICAL` → `EscalationAgent`

- **知识库内容**：各快递公司理赔政策、举证材料清单、不同场景的处理时效

**与现有代码区别**

GeneralAgent 只做"物流查询引导"，LogisticsAgent 专门处理"物流纠纷举证和理赔"，边界更清晰。

---

### **扩展 E3：换货与维修 Agent（AftersaleAgent）**

**痛点**：当前 BillingAgent 处理退款，但换货/维修是完全不同的业务流程（不涉及资金，涉及实物返回），混在 BillingAgent 里会导致流程说明不准确。

**职责**：换货申请流程、维修寄送指引、配件申请、质保说明、二次验货要求。

**需要新增的意图**

```Python
IntentCategory.EXCHANGE_REQUEST    # 申请换货
IntentCategory.REPAIR_REQUEST      # 申请维修
IntentCategory.WARRANTY_INQUIRY    # 质保查询
IntentCategory.PARTS_REQUEST       # 配件申请
IntentCategory.QUALITY_COMPLAINT   # 商品质量投诉（需举证）
```

**关键扩展点**

- **举证引导**：质量投诉需要图片/视频证据，在 Skill 里写清楚"需要提供XX图片"

- **工具扩展**：`create_aftersale_ticket`（创建售后工单，区别于退款工单）

- **与 BillingAgent 协作**：换货被拒后降级退款，应触发 `BillingAgent` 协作路由

- **知识库内容**：各品类质保政策、换货时效、寄回地址查询流程

---

### **扩展 E4：促销活动咨询 Agent（PromotionAgent）**

**痛点**：大促期间（双11、618）促销规则复杂，用户大量咨询优惠券叠加规则、满减计算、预售定金等，这类问题规则密集但高度重复，非常适合知识库 RAG \+ 专属 Agent。

**职责**：优惠券规则解释、满减计算引导、预售/尾款说明、限时抢购规则、红包叠加逻辑。

**需要新增的意图**

```Python
IntentCategory.COUPON_INQUIRY      # 优惠券使用规则
IntentCategory.PROMOTION_RULE      # 活动规则（满减/折扣/买赠）
IntentCategory.PRESALE_INQUIRY     # 预售/定金/尾款
IntentCategory.FLASH_SALE          # 限时抢购/秒杀
IntentCategory.PRICE_PROTECTION    # 保价申请
```

**关键扩展点**

- **知识库动态更新**：每次大促前通过 `/knowledge/add` API 批量导入活动规则文档，无需修改代码

- **工具扩展**：`calculate_discount`（按用户提供的商品金额 \+ 优惠条件做算术，类似现有的 `compare_amounts`）

- **时效性管理**：活动过期后旧知识库内容要及时清理，避免给出过期规则

**知识库内容示例**

```Plain Text
{"title": "双11满减规则", "content": "每满300减40，不与其他优惠叠加，仅限官方旗舰店..."}
{"title": "优惠券叠加规则", "content": "店铺券与平台券可叠加，但与满减活动不可同时使用..."}
```

---

### **扩展 E5：积分与会员权益 Agent（MemberAgent）**

**痛点**：积分查询、会员升级、权益使用频率很高，但逻辑独立（不涉及退款，不是技术问题），当前全压在 GeneralAgent 里，导致 GeneralAgent 的知识库检索范围过宽、回复精度下降。

**职责**：积分余额查询引导、积分兑换流程、会员等级规则、专属权益说明、生日礼/成长值说明。

**需要新增的意图**

```Python
IntentCategory.POINTS_INQUIRY      # 积分查询/兑换
IntentCategory.MEMBER_LEVEL        # 会员等级/升级条件
IntentCategory.MEMBER_BENEFITS     # 会员权益咨询
IntentCategory.GROWTH_VALUE        # 成长值规则
```

**关键扩展点**

- **用户画像利用**：从 `MemoryManager` 读取用户画像里的会员等级字段，提供个性化权益说明

- **与 BillingAgent 的边界**：积分抵扣出现金额问题时，转 BillingAgent；会员费退款转 BillingAgent

---

### **扩展 E6：跨境购 Agent（CrossBorderAgent）**

**痛点**：跨境电商的海关、税费、禁限品、国际物流、进口商品保税等问题和国内电商完全不同，且合规要求高，不能用同一套 GeneralAgent 话术处理。

**职责**：清关说明、税费估算引导、禁限品查询、保税仓说明、国际退换货政策。

**需要新增的意图**

```Python
IntentCategory.CUSTOMS_INQUIRY     # 清关/报关问题
IntentCategory.TAX_INQUIRY         # 税费问题
IntentCategory.PROHIBITED_GOODS    # 禁限品咨询
IntentCategory.BONDED_WAREHOUSE    # 保税仓商品咨询
IntentCategory.INTL_RETURN         # 国际退换货
```

**关键扩展点**

- **合规约束**：禁止给出"包税""保证不查验"等无法承诺的表达，写入 Skill

- **实体扩展**：提取国家/地区代码、HS 编码、商品类目作为实体

- **知识库内容**：主要目的地国关税政策、个人物品免税额度、禁限品目录

---

### **扩展 E7：商家/卖家支持 Agent（SellerAgent）**

**痛点**：平台型电商（类淘宝/京东）有大量入驻商家的咨询，和 C 端买家问题完全不同（开店流程、规则违规申诉、商品上架问题、运营活动报名）。

**职责**：入驻流程引导、商品上架规范、违规申诉流程、运营活动报名、店铺数据查询引导。

**需要新增的意图**

```Python
IntentCategory.SELLER_ONBOARD      # 商家入驻
IntentCategory.PRODUCT_LISTING     # 商品上架/下架
IntentCategory.VIOLATION_APPEAL    # 违规申诉
IntentCategory.SELLER_ACTIVITY     # 运营活动报名
IntentCategory.SHOP_DATA           # 店铺数据查询
```

**关键扩展点**

- **用户身份区分**：通过 `req.entities` 或请求头区分 C 端买家和 B 端商家，路由到不同 Agent

- **知识库内容**：商家入驻协议、商品发布规范、违禁词检测规则、活动招商条件

- **与 EscalationAgent 的协作**：违规申诉处理时间长、结果不确定，大量情况需要转专属商家客服

---

### **电商子场景扩展全景**

```Plain Text
电商平台
├── 售前
│   ├── E1 售前导购（PreSaleAgent）     ← 新增
│   └── E5 积分会员（MemberAgent）      ← 从 GeneralAgent 拆分
│
├── 交易中
│   └── E4 促销活动（PromotionAgent）   ← 新增
│
├── 售后
│   ├── BillingAgent（已有）           退款/发票/扣款
│   ├── E2 物流纠纷（LogisticsAgent）   ← 从 GeneralAgent 拆分
│   └── E3 换货维修（AftersaleAgent）   ← 从 BillingAgent 拆分
│
├── 特殊场景
│   └── E6 跨境购（CrossBorderAgent）  ← 新增
│
└── B 端
    └── E7 商家支持（SellerAgent）      ← 新增
```

---

## **扩展步骤总结**

无论扩展到哪个场景，操作步骤是一致的：

### **Step 1：定义意图**

在 `core/intent_recognizer.py` 的 `IntentCategory` 枚举里添加新意图，同时在 `_TEMPLATES` 里补充 few\-shot 示例。

```Python
# 添加意图
IntentCategory.YOUR_NEW_INTENT = "your_new_intent"

# 添加模板（用于 LLM few-shot 和 Embedding 匹配）
_TEMPLATES[IntentCategory.YOUR_NEW_INTENT] = [
    "示例句子1", "示例句子2", "示例句子3"
]
```

### **Step 2：创建 Agent 类**

在 `agents/agent_orchestrator.py` 里仿照 `TechnicalAgent` 写新 Agent 类，主要配置 `AgentProfile`（角色 Prompt、工具白名单、温度）。

```Python
class YourNewAgent(BaseAgent):
    agent_type = AgentType.YOUR_NEW_TYPE
    profile = AgentProfile(
        role="你的角色定位描述",
        tool_scope=("search_knowledge_base", "your_custom_tool"),
        temperature=0.3,
        handoff_conditions=("需要人工的场景描述",),
    )
```

### **Step 3：编写 Skill 文件**

在 `skills/` 下新建目录，添加 `SKILL.md`，定义角色规范、回复约束和禁止事项。

```Plain Text
skills/
  your_scenario/
    SKILL.md
```

Skill 会在每次请求时动态注入 system prompt，**无需重启服务**即可生效。

### **Step 4：导入知识库**

调用 `/knowledge/add` API 或直接使用 `KnowledgeBase.add_documents()` 导入领域文档。ChromaDB 会自动生成向量索引。

```Python
kb.add_documents([
    {"title": "文档标题", "content": "文档内容..."},
    ...
])
```

### **Step 5：注册路由**

在 `_INTENT_ROUTING` 映射表和 `_domain_scores()` 打分函数里注册新 Agent：

```Python
# 路由表
_INTENT_ROUTING[IntentCategory.YOUR_NEW_INTENT] = AgentType.YOUR_NEW_TYPE

# 打分函数：补充意图分和关键词分
if req.intent in (IntentCategory.YOUR_NEW_INTENT,):
    scores[AgentType.YOUR_NEW_TYPE] += 0.75
```

---

## **不同场景的共性改造建议**



