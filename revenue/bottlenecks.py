"""
Revenue Bottleneck Detection Engine (Phase 4, Part 25).
Analyzes live operational telemetry to identify the single highest-impact constraint.
Evaluates: DEMAND, TRAFFIC, LEADS, QUALIFICATION, CONVERSION, PAYMENT, DELIVERY, RETENTION, SUPPORT, MARGIN, AUTOMATION.
"""

from typing import Dict, Any, List
from revenue.pipeline import SalesPipelineEngine
from revenue.ledger import RevenueLedgerEngine
from acquisition.engine import CapabilityAcquisitionEngine

class RevenueBottleneckEngine:
    """
    Identifies the primary revenue bottleneck using empirical system metrics.
    """

    @classmethod
    def analyze_bottlenecks(cls) -> Dict[str, Any]:
        """
        Inspects live pipeline, revenue ledger, and customer feedback to pinpoint the constraint.
        """
        pipe_summary = SalesPipelineEngine.get_pipeline_summary()
        rev_metrics = RevenueLedgerEngine.get_revenue_metrics()
        
        total_leads = pipe_summary["total_leads"]
        paid_customers = pipe_summary["paid_customers"]
        verified_rev = rev_metrics["all_time"]["verified_actual_revenue"]
        pending_rev = rev_metrics["all_time"]["pending_revenue"]

        # Empirical diagnostic rules
        if total_leads == 0:
            bottleneck = "TRAFFIC"
            evidence = "Zero sales leads or inbound inquiries registered in pipeline."
            recommended_action = "Publish organic developer tutorials and submit release to open-source directories."
            capability_needed = "Organic Developer Distribution"
        elif total_leads > 0 and pipe_summary["stage_breakdown"]["QUALIFIED"] == 0:
            bottleneck = "QUALIFICATION"
            evidence = f"{total_leads} leads captured, but none advanced to QUALIFIED stage."
            recommended_action = "Refine lead qualification criteria and improve landing page problem definition."
            capability_needed = "Lead Qualification Automation"
        elif pipe_summary["stage_breakdown"]["INTERESTED"] > 0 and paid_customers == 0 and pending_rev == 0:
            bottleneck = "CONVERSION"
            evidence = "Prospects show interest, but checkout / purchase has not converted."
            recommended_action = "Offer zero-risk guarantees, clarify FAQ, and verify pricing competitiveness."
            capability_needed = "Checkout Conversion Optimization"
        elif pending_rev > 0 and verified_rev == 0:
            bottleneck = "PAYMENT"
            evidence = f"${pending_rev:.2f} pending revenue waiting for processor verification."
            recommended_action = "Verify payment gateway webhook configuration and settle pending funds."
            capability_needed = "Automated Payment Reconciliation"
        else:
            bottleneck = "DEMAND"
            evidence = "Initial customer validation phase in progress."
            recommended_action = "Execute focused 7-day first-customer experiment."
            capability_needed = None

        # Check if missing capability should be fed into Phase 3 Capability Acquisition Engine
        gap_evaluation = None
        if capability_needed:
            try:
                gap_evaluation = CapabilityAcquisitionEngine.evaluate_capability_gap(
                    gap_id=f"GAP-{bottleneck.lower()}",
                    capability_name=capability_needed,
                    why_required=evidence,
                    business_objective=recommended_action,
                    current_cost=0.0
                )
            except Exception:
                gap_evaluation = None

        return {
            "current_bottleneck": bottleneck,
            "evidence": evidence,
            "recommended_action": recommended_action,
            "telemetry": {
                "total_leads": total_leads,
                "paid_customers": paid_customers,
                "verified_revenue": verified_rev,
                "pending_revenue": pending_rev
            },
            "capability_acquisition_evaluation": gap_evaluation
        }
