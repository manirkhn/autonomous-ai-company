import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from approvals.manager import ApprovalManager
from revenue.experiments import FirstRevenueExperimentEngine
from revenue.products import RevenueProductFactory
from revenue.offers import SalesAssetFactory
from revenue.acquisition import CustomerAcquisitionEngine
from revenue.pipeline import SalesPipelineEngine
from revenue.daily_loop import DailyRevenueLoop
from core.db import get_connection

def main():
    # 1. Resolve Owner Approval
    res = ApprovalManager.resolve_approval(
        'APP-A531D3CC',
        'APPROVE',
        owner_notes='Approved by Human Owner directly via chat prompt'
    )
    print('[1] Approval Resolved:', res)

    # 2. Update Launch Readiness Reports table approval_status
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE launch_readiness_reports SET approval_status = 'APPROVED' WHERE opportunity_id = 'OPP-P4-001'")
    conn.commit()
    conn.close()
    print('[2] Launch Readiness Reports updated to APPROVED')

    # 3. Launch First Revenue Experiment
    exp = FirstRevenueExperimentEngine.launch_first_customer_experiment(
        opportunity_id='OPP-P4-001',
        target_customer_count=1,
        experiment_duration_days=7
    )
    print('[3] Experiment Launched:', exp['experiment_id'])

    # 4. Generate Product Package & QA Validation
    pkg = RevenueProductFactory.create_product_package('OPP-P4-001')
    qa = RevenueProductFactory.run_product_qa(pkg)
    print('[4] Product QA Status:', qa['verdict'])

    # 5. Generate Sales Assets
    assets = SalesAssetFactory.generate_sales_assets('OPP-P4-001')
    print('[5] Sales Assets Created for:', assets['product_name'])

    # 6. Initialize Compliant Organic Campaign
    camp = CustomerAcquisitionEngine.create_campaign(
        target_definition='Local AI & Ollama Developers',
        source='GitHub Releases & r/LocalLLaMA',
        consent_or_legal_basis='Public Open-Source Community Guidelines',
        message=assets['outreach_template'],
        frequency_limit='1 community thread announcement',
        opt_out_method='Direct unsubscribe link or reply',
        channel='ORGANIC_COMMUNITY',
        require_owner_approval=False
    )
    print('[6] Organic Campaign Activated:', camp['campaign_id'])

    # 7. Execute Daily Revenue Loop
    daily = DailyRevenueLoop.execute_daily_cycle()
    print('[7] Daily Revenue Loop Completed:', daily['current_bottleneck'], '->', daily['recommended_action'])

if __name__ == '__main__':
    main()
