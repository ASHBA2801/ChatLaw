"""Offline unit tests for scenario understanding, domain routing, and concept expansion."""

from scenario.analyzer import analyze_scenario, extract_scenario_facts, is_direct_lookup, is_irrelevant_query, is_scenario_query
from scenario.concepts import extract_matching_concepts, get_synonyms_for_term
from scenario.domain import DOMAINS_REGISTRY, route_domain
from scenario.expansion import expand_query


def test_scenario_1_defective_phone_online_refund():
    query = "I bought a defective phone online and the seller refuses to refund me."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.is_legal_query is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    assert "Consumer Protection" in analysis.domain_routing.primary_domain_name
    
    # Check concept mappings
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "defective_goods" in concepts
    assert "refund_return_dispute" in concepts
    assert "ecommerce_transaction" in concepts
    
    # Check facts
    facts = analysis.facts
    assert facts.actor is not None and "Consumer" in facts.actor
    assert facts.channel is not None and "E-commerce" in facts.channel
    assert facts.problem is not None and "defective" in facts.problem.lower()
    assert facts.opposing_action is not None and "refused" in facts.opposing_action.lower()
    
    # Check expansion
    expanded = expand_query(query, analysis)
    assert expanded.is_scenario is True
    assert "defective goods" in expanded.expanded_query.lower() or "defect in goods" in expanded.expanded_query.lower()
    assert "consumer protection" in expanded.expanded_query.lower()
    assert "refund" in expanded.expanded_query.lower()


def test_scenario_2_different_product_no_replace():
    query = "The online shop sent me a completely different product and won't replace it."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "wrong_product_delivery" in concepts or "refund_return_dispute" in concepts or "ecommerce_transaction" in concepts


def test_scenario_3_paid_not_delivered():
    query = "I paid for a product but the seller never delivered it."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "non_delivery_goods" in concepts


def test_scenario_4_refuses_warranty():
    query = "The seller refuses to honour the warranty."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "warranty_guarantee_breach" in concepts


def test_scenario_5_charged_twice():
    query = "I was charged money twice for the same online order."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    # Can route to banking_finance or consumer_protection
    assert analysis.domain_routing.primary_domain in ("banking_finance", "consumer_protection")
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "double_charging_unauthorized_payment" in concepts or "ecommerce_transaction" in concepts


def test_scenario_6_misleading_ad():
    query = "The company advertised a product with features that it does not actually have."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "misleading_advertisement" in concepts


def test_scenario_7_arrived_damaged():
    query = "I bought something online and the seller refuses to return it even though it arrived damaged."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    assert analysis.domain_routing.primary_domain == "consumer_protection"
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "defective_goods" in concepts or "refund_return_dispute" in concepts


def test_scenario_8_cheated_online_money():
    query = "I was cheated by someone who took my money online."
    analysis = analyze_scenario(query)
    
    assert analysis.is_scenario is True
    # Must NOT be strictly forced to Consumer Protection only; should capture Criminal / Cyber
    assert analysis.domain_routing.primary_domain in ("cyber_law", "criminal_law") or "cyber_law" in analysis.domain_routing.secondary_domains or "criminal_law" in analysis.domain_routing.secondary_domains
    concepts = [m.concept_id for m in extract_matching_concepts(query)]
    assert "criminal_cheating_fraud" in concepts or "cyber_fraud_online_theft" in concepts


def test_scenario_9_direct_section_query():
    query = "What is Section 303 of BNS?"
    analysis = analyze_scenario(query)
    
    assert is_direct_lookup(query) is True
    assert analysis.is_scenario is False
    assert analysis.is_legal_query is True
    assert analysis.domain_routing.primary_domain == "criminal_law"
    
    expanded = expand_query(query, analysis)
    assert expanded.is_scenario is False
    assert expanded.expanded_query == query


def test_scenario_10_punishment_for_theft():
    query = "What is the punishment for theft?"
    analysis = analyze_scenario(query)
    
    assert is_direct_lookup(query) is True
    assert analysis.is_scenario is False
    assert analysis.domain_routing.primary_domain == "criminal_law"


def test_scenario_11_irrelevant_queries():
    for query in ["What is the capital of France?", "recipe for biryani", "how to bake a cake"]:
        assert is_irrelevant_query(query) is True
        analysis = analyze_scenario(query)
        assert analysis.is_legal_query is False


def test_all_16_domains_supported():
    required_domains = [
        "consumer_protection", "contract", "criminal_law", "property",
        "family_law", "labour_employment", "cyber_law", "motor_vehicle",
        "constitutional_law", "civil_procedure", "criminal_procedure",
        "company_commercial_law", "intellectual_property", "banking_finance",
        "tax", "general_legal",
    ]
    for domain_id in required_domains:
        assert domain_id in DOMAINS_REGISTRY
        assert DOMAINS_REGISTRY[domain_id].display_name
