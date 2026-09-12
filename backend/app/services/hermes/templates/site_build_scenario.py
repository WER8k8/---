"""Site Build and Distribution Scenario Template.
Defines the standard TaskGraph for taking product specs and generating a multi-language site.
"""
from typing import Dict, Any
from app.schemas.hermes_orchestration import TaskGraph, TaskNode, GraphPolicies

def build_site_generation_graph(plan_id: str, event_id: str, product_data: Dict[str, Any]) -> TaskGraph:
    """
    Constructs the deterministic TaskGraph for Site Building and Multi-channel Distribution.
    This graph is executed by the L2/L3 orchestration layer.
    """
    return TaskGraph(
        plan_id=plan_id,
        event_id=event_id,
        strategy="standard",
        policies=GraphPolicies(max_parallel=5, degradation="skip"),
        nodes=[
            TaskNode(
                id="extract_seo_keywords",
                executor="seo_matrix",
                capability="keyword.extract",
                depends_on=[],
                input={"product_context": product_data, "target_markets": ["Global"]},
                sop_ref="geo-rank-strategist.keyword_extraction_v2" # From ECC
            ),
            TaskNode(
                id="generate_site_content_i18n",
                executor="ai_engine",
                capability="site.generate.i18n",
                depends_on=["extract_seo_keywords"],
                input={"languages": ["en", "es", "ar", "fr"]},
                input_from={"primary_keywords": "extract_seo_keywords.output.keywords"},
                sop_ref="insulation-backend-developer.site_structure" # From ECC
            ),
            TaskNode(
                id="publish_to_seo_matrix",
                executor="bullmq_seo_backend", # The external Node.js satellite system
                capability="site.publish",
                depends_on=["generate_site_content_i18n"],
                input_from={"site_payload": "generate_site_content_i18n.output.site_data"}
            ),
            TaskNode(
                id="notify_customer_n8n",
                executor="n8n_webhook",
                capability="notification.send",
                depends_on=["publish_to_seo_matrix"],
                input={"channel": "whatsapp", "message_template": "Your global site is live!"},
                input_from={"urls": "publish_to_seo_matrix.output.published_urls"}
            )
        ]
    )
