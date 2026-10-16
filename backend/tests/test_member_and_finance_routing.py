"""E5 积分会员 Agent 与场景三金融路由的专项测试。

覆盖三个关键行为：
  1. 会员/积分意图路由到 MemberAgent（主 Agent）
  2. 积分涉钱时由 BillingAgent 协作兜底（E5 边界）
  3. 高风险赎回/账户冻结直接升级人工（阈值拦截）
"""

from agents.agent_orchestrator import (
    AgentOrchestrator,
    AgentType,
    BillingAgent,
    ComplaintAgent,
    EscalationAgent,
    GeneralAgent,
    MemberAgent,
    ProductConsultAgent,
    Request,
    RiskAlertAgent,
)
from core.intent_recognizer import IntentCategory, UrgencyLevel


class FakeClient:
    def __init__(self):
        self.calls = []


def make_orchestrator():
    """绕过 __init__ 手工装配 Agent 池（沿用项目既有测试写法）。"""
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    client = FakeClient()
    orchestrator._pool = {
        AgentType.GENERAL: [GeneralAgent(client, "test-model")],
        AgentType.TECHNICAL: [__import__(
            "agents.agent_orchestrator", fromlist=["TechnicalAgent"]
        ).TechnicalAgent(client, "test-model")],
        AgentType.BILLING: [BillingAgent(client, "test-model")],
        AgentType.ESCALATION: [EscalationAgent(client, "test-model")],
        AgentType.MEMBER: [MemberAgent(client, "test-model")],
        AgentType.PRODUCT: [ProductConsultAgent(client, "test-model")],
        AgentType.RISK: [RiskAlertAgent(client, "test-model")],
        AgentType.COMPLAINT: [ComplaintAgent(client, "test-model")],
    }
    return orchestrator


def make_request(**kwargs):
    values = {
        "message": "我的积分还有多少？",
        "user_id": "u1",
        "conv_id": "c1",
        "intent": IntentCategory.POINTS_INQUIRY,
        "intent_group": "query",
        "urgency": UrgencyLevel.LOW,
        "intent_confidence": 0.9,
        "entities": {},
    }
    values.update(kwargs)
    return Request(**values)


def test_member_intent_routes_to_member_agent():
    decision = make_orchestrator()._route_decision(make_request())

    assert decision.primary_agent is AgentType.MEMBER
    assert "intent=points_inquiry" in decision.reason


def test_member_agent_profile_is_distinct_from_billing():
    assert MemberAgent.profile.role != BillingAgent.profile.role
    assert MemberAgent.profile.temperature != BillingAgent.profile.temperature
    # E5 边界必须写进升级条件，而不是只写在文档里
    assert any("BillingAgent" in c for c in MemberAgent.profile.handoff_conditions)


def test_points_with_money_pulls_billing_as_supporting_agent():
    """积分抵扣出现金额问题时，BillingAgent 作为辅助 Agent 协作（E5 边界）。"""
    decision = make_orchestrator()._route_decision(make_request(
        message="积分兑换的优惠券申请退款了，积分会退回吗？",
        entities={"amount": ["50 元"]},
    ))

    assert decision.primary_agent is AgentType.MEMBER
    assert AgentType.BILLING in decision.supporting_agents


def test_member_level_intent_uses_member_agent_not_general():
    decision = make_orchestrator()._route_decision(make_request(
        message="我现在是什么会员等级，怎么升级金卡？",
        intent=IntentCategory.MEMBER_LEVEL,
    ))

    assert decision.primary_agent is AgentType.MEMBER


def test_high_risk_redemption_escalates_to_human():
    """赎回金额超阈值（默认 50000）必须直接升级，不经过任何业务 Agent。"""
    decision = make_orchestrator()._route_decision(make_request(
        message="我要赎回 8 万元的基金",
        intent=IntentCategory.FUND_REDEMPTION,
        intent_group="billing",
        entities={"amount": ["80000 元"]},
    ))

    assert decision.primary_agent is AgentType.ESCALATION
    assert "高风险操作拦截" in decision.reason


def test_account_freeze_always_escalates_to_human():
    decision = make_orchestrator()._route_decision(make_request(
        message="我的账户被冻结了，怎么解冻？",
        intent=IntentCategory.ACCOUNT_FREEZE,
        intent_group="account",
    ))

    assert decision.primary_agent is AgentType.ESCALATION
    assert "高风险操作拦截" in decision.reason


def test_small_redemption_still_goes_to_risk_agent():
    """未超阈值且非全额赎回时走 RiskAlertAgent，只提示不升级。"""
    decision = make_orchestrator()._route_decision(make_request(
        message="我想赎回 2000 元基金",
        intent=IntentCategory.FUND_REDEMPTION,
        intent_group="billing",
        entities={"amount": ["2000 元"]},
    ))

    assert decision.primary_agent is AgentType.RISK


def test_escalation_agent_body_restored():
    """回归防护：EscalationAgent 曾因类体被误粘进 ComplaintAgent 而只剩 docstring。"""
    assert EscalationAgent.agent_type is AgentType.ESCALATION
    assert ComplaintAgent.agent_type is AgentType.COMPLAINT
    assert EscalationAgent.profile.max_tokens == 500
    assert ComplaintAgent.profile.max_tokens == 700
