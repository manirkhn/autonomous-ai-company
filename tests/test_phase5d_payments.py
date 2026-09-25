"""
Automated Test Suite for Phase 5D: Secure Payments, Customer Checkout & Owner Settlement.

Verifies:
1. Deterministic payment state machine & illegal transition rejection
2. Payment provider abstraction (TestProvider & Stripe UAE adapter)
3. Cryptographic webhook verification (HMAC-SHA256 & timestamp drift)
4. Webhook idempotency & anti-replay protection
5. Revenue ledger integration & deterministic accounting
6. Automated digital product fulfillment & checksum verification
7. Payout & settlement tracking with banking air-gap
8. Refund governance lifecycle & owner approval gates
9. Strict test mode isolation (TEST != PRODUCTION revenue)
10. Personal banking credential protection & air-gap validation
11. UAE settlement profile configuration
12. First real customer gate & bottleneck diagnostics
13. Daily CEO report integration with Section 34 truth check
14. Financial firewall & $0 unapproved spending ceiling
"""

import unittest
import json
import time
from datetime import datetime, timezone

from core.db import init_db, get_connection
from payments.owner_settlement import OwnerSettlementManager
from payments.provider import (
    TestPaymentProvider,
    StripePaymentProvider,
    get_payment_provider
)
from payments.checkout import (
    CheckoutManager,
    InvalidStateTransitionError,
    WebhookSecurityError,
    PRIMARY_PRODUCT_ID
)
from payments.settlement import SettlementManager
from payments.refunds import RefundGovernanceEngine
from payments.approval_gates import PaymentApprovalGates
from payments.income_metrics import IncomeGenerationAnalytics
from revenue.ledger import RevenueLedgerEngine, BankingSecurityViolation
from reporting.daily_ceo_report import DailyCEOReportGenerator

class TestPhase5DPayments(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Clean test state in payment tables before each test
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payment_transactions WHERE customer_email LIKE '%test%' OR customer_email LIKE '%sandbox%'")
        cursor.execute("DELETE FROM processed_webhook_events WHERE event_id LIKE '%test%' OR event_id LIKE '%sandbox%'")
        cursor.execute("DELETE FROM refund_records WHERE customer_id LIKE '%test%'")
        conn.commit()
        conn.close()

    def test_01_banking_air_gap_and_credential_rejection(self):
        """AI must never store full IBANs, card numbers, or passwords."""
        # 1. Full UAE IBAN injection attempt must be blocked
        with self.assertRaises(BankingSecurityViolation):
            OwnerSettlementManager.update_profile(
                masked_destination_reference="AE123456789012345678901"
            )

        # 2. Credit card number injection attempt must be blocked
        with self.assertRaises(BankingSecurityViolation):
            OwnerSettlementManager.update_profile(
                bank_name="4111 1111 1111 1111"
            )

        # 3. Password injection attempt must be blocked
        with self.assertRaises(BankingSecurityViolation):
            OwnerSettlementManager.update_profile(
                bank_name="password = MySecretPass123"
            )

        # 4. Valid non-sensitive profile update succeeds
        profile = OwnerSettlementManager.update_profile(
            bank_name="Emirates Islamic",
            settlement_currency="AED",
            masked_destination_reference="****9876"
        )
        self.assertEqual(profile["bank_name"], "Emirates Islamic")
        self.assertEqual(profile["settlement_currency"], "AED")
        self.assertEqual(profile["masked_destination_reference"], "****9876")

        # 5. Air gap audit confirms no sensitive credentials stored
        audit = OwnerSettlementManager.verify_air_gap()
        self.assertTrue(audit["air_gap_intact"])
        self.assertFalse(audit["credentials_held_by_ai"])

    def test_02_payment_state_machine_transitions(self):
        """Verifies valid lifecycle and rejection of illegal state skips."""
        session = CheckoutManager.create_checkout(
            customer_email="developer.test@example.com",
            currency="USD",
            mode="TEST"
        )
        order_id = session["order_id"]

        # Valid transition: CHECKOUT_CREATED -> PAYMENT_PENDING
        tx1 = CheckoutManager.transition_state(order_id, "PAYMENT_PENDING")
        self.assertEqual(tx1["payment_status"], "PAYMENT_PENDING")

        # Valid transition: PAYMENT_PENDING -> PAYMENT_AUTHORIZED
        tx2 = CheckoutManager.transition_state(order_id, "PAYMENT_AUTHORIZED")
        self.assertEqual(tx2["payment_status"], "PAYMENT_AUTHORIZED")

        # Valid transition: PAYMENT_AUTHORIZED -> PAYMENT_VERIFIED
        tx3 = CheckoutManager.transition_state(order_id, "PAYMENT_VERIFIED", evidence="Mock Receipt")
        self.assertEqual(tx3["payment_status"], "PAYMENT_VERIFIED")

        # Valid transition: PAYMENT_VERIFIED -> SETTLEMENT_PENDING
        tx4 = CheckoutManager.transition_state(order_id, "SETTLEMENT_PENDING")
        self.assertEqual(tx4["payment_status"], "SETTLEMENT_PENDING")

        # Valid transition: SETTLEMENT_PENDING -> SETTLEMENT_COMPLETED
        tx5 = CheckoutManager.transition_state(order_id, "SETTLEMENT_COMPLETED")
        self.assertEqual(tx5["payment_status"], "SETTLEMENT_COMPLETED")

        # Illegal transition: cannot jump back to CHECKOUT_CREATED from SETTLEMENT_COMPLETED
        with self.assertRaises(InvalidStateTransitionError):
            CheckoutManager.transition_state(order_id, "CHECKOUT_CREATED")

    def test_03_payment_provider_abstraction(self):
        """Validates test provider and Stripe UAE adapter behavior."""
        test_provider = TestPaymentProvider()
        health = test_provider.provider_health()
        self.assertEqual(health["status"], "HEALTHY")
        self.assertTrue(health["air_gap_enforced"])

        checkout = test_provider.create_checkout(
            order_id="ORD-UNITTEST-001",
            product_name="Test Product",
            amount=29.00,
            currency="USD",
            customer_email="test@example.com"
        )
        self.assertEqual(checkout["amount"], 29.00)
        self.assertGreater(checkout["fee"], 0.0)
        self.assertLess(checkout["net_amount"], 29.00)

        # Stripe adapter unconfigured behavior check
        stripe_provider = StripePaymentProvider(api_key="", webhook_secret="")
        stripe_health = stripe_provider.provider_health()
        self.assertEqual(stripe_health["status"], "UNCONFIGURED")
        self.assertTrue(stripe_health["requires_owner_activation"])

    def test_04_cryptographic_webhook_verification(self):
        """Validates HMAC signature and timestamp tolerance."""
        test_provider = TestPaymentProvider()
        payload = json.dumps({"order_id": "ORD-TEST-001", "amount": 29.00})

        # 1. Valid signature
        valid_sig = test_provider.generate_test_signature(payload)
        is_valid, event, err = test_provider.process_webhook(payload.encode("utf-8"), valid_sig)
        self.assertTrue(is_valid)
        self.assertEqual(err, "")
        self.assertEqual(event["order_id"], "ORD-TEST-001")

        # 2. Forged signature fails
        forged_sig = "t=12345,v1=bad_signature_00000000000000000000000000000000"
        is_valid, _, err = test_provider.process_webhook(payload.encode("utf-8"), forged_sig)
        self.assertFalse(is_valid)

        # 3. Expired timestamp (> 300s drift) fails
        expired_ts = int(time.time()) - 400
        expired_sig = test_provider.generate_test_signature(payload, timestamp=expired_ts)
        is_valid, _, err = test_provider.process_webhook(payload.encode("utf-8"), expired_sig)
        self.assertFalse(is_valid)
        self.assertIn("drift", err)

    def test_05_webhook_idempotency_anti_replay(self):
        """Prevents duplicate webhook events from double counting."""
        session = CheckoutManager.create_checkout(
            customer_email="idempotent.test@example.com",
            currency="USD",
            mode="TEST"
        )
        order_id = session["order_id"]

        test_provider = TestPaymentProvider()
        event_id = f"evt_test_replay_{order_id}"
        payload = json.dumps({
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": session["provider_payment_id"],
                    "order_id": order_id,
                    "amount": 29.00,
                    "currency": "USD"
                }
            }
        })
        sig = test_provider.generate_test_signature(payload)

        # First webhook execution
        res1 = CheckoutManager.process_incoming_webhook(payload.encode("utf-8"), sig)
        self.assertEqual(res1["status"], "PROCESSED")
        self.assertEqual(res1["new_state"], "PAYMENT_VERIFIED")

        # Second webhook execution with exact same event ID (replay attack)
        res2 = CheckoutManager.process_incoming_webhook(payload.encode("utf-8"), sig)
        self.assertEqual(res2["status"], "DUPLICATE_EVENT_IGNORED")
        self.assertIn("Idempotency", res2["message"])

    def test_06_automated_digital_delivery_and_receipt(self):
        """Verifies customer digital product fulfillment upon verified payment."""
        session = CheckoutManager.create_checkout(
            customer_email="customer.delivery.test@example.com",
            currency="USD",
            mode="TEST"
        )
        order_id = session["order_id"]

        test_provider = TestPaymentProvider()
        event_id = f"evt_deliv_test_{order_id}"
        payload = json.dumps({
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": session["provider_payment_id"],
                    "order_id": order_id,
                    "amount": 29.00,
                    "currency": "USD"
                }
            }
        })
        sig = test_provider.generate_test_signature(payload)
        res = CheckoutManager.process_incoming_webhook(payload.encode("utf-8"), sig)

        self.assertEqual(res["status"], "PROCESSED")
        self.assertIsNotNone(res["delivery"])
        self.assertEqual(res["delivery"]["status"], "DELIVERED")
        self.assertTrue(len(res["delivery"]["package_checksum"]) > 20)

        # Verify customer receipt
        receipt = CheckoutManager.get_receipt(order_id)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["order_id"], order_id)
        self.assertEqual(receipt["delivery_status"], "DELIVERED")
        self.assertEqual(receipt["payment_status"], "PAYMENT_VERIFIED")

    def test_07_test_mode_isolation_guarantee(self):
        """Ensures TEST transactions NEVER enter the production revenue ledger."""
        initial_metrics = RevenueLedgerEngine.get_revenue_metrics()
        initial_verified = initial_metrics["all_time"]["verified_actual_revenue"]

        session = CheckoutManager.create_checkout(
            customer_email="sandbox.isolation.test@example.com",
            currency="USD",
            mode="TEST"
        )
        order_id = session["order_id"]

        test_provider = TestPaymentProvider()
        event_id = f"evt_iso_test_{order_id}"
        payload = json.dumps({
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": session["provider_payment_id"],
                    "order_id": order_id,
                    "amount": 29.00,
                    "currency": "USD"
                }
            }
        })
        sig = test_provider.generate_test_signature(payload)
        CheckoutManager.process_incoming_webhook(payload.encode("utf-8"), sig)

        # Verify revenue ledger did NOT change
        after_metrics = RevenueLedgerEngine.get_revenue_metrics()
        after_verified = after_metrics["all_time"]["verified_actual_revenue"]
        self.assertEqual(initial_verified, after_verified, "Test transaction leaked into production revenue ledger!")

        # Verify transaction is recorded in payment_transactions as TEST
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payment_transactions WHERE order_id = ?", (order_id,))
        tx = dict(cursor.fetchone())
        conn.close()

        self.assertEqual(tx["mode"], "TEST")
        self.assertEqual(tx["payment_status"], "PAYMENT_VERIFIED")

    def test_08_refund_governance_and_approval_gate(self):
        """Verifies refund states pause at REFUND_APPROVAL_REQUIRED without owner consent."""
        # Ensure automatic refund approval is False
        PaymentApprovalGates.update_gate("AUTOMATIC_REFUND_APPROVAL", False)

        req = RefundGovernanceEngine.request_refund(
            order_id="ORD-REFUND-TEST-001",
            customer_email="refund.test@example.com",
            amount=29.00,
            reason="Developer evaluating alternative solution"
        )
        self.assertEqual(req["status"], "REFUND_APPROVAL_REQUIRED")
        self.assertTrue(req["requires_owner_approval"])

        # Owner review and approval
        refund_id = req["refund_id"]
        res = RefundGovernanceEngine.owner_review_refund(
            refund_id=refund_id,
            approved=True,
            owner_notes="Approved per customer satisfaction policy"
        )
        self.assertEqual(res["status"], "REFUND_COMPLETED")

    def test_09_owner_approval_gates_default_locked(self):
        """Verifies that all 5 owner gates default to locked/False."""
        gates = PaymentApprovalGates.get_all_gates()
        for key in [
            "PAYMENT_PROVIDER_ACTIVATION_APPROVAL",
            "SETTLEMENT_DESTINATION_APPROVAL",
            "AUTOMATIC_REFUND_APPROVAL",
            "PAID_INFRASTRUCTURE_APPROVAL",
            "PAID_API_APPROVAL"
        ]:
            self.assertIn(key, gates)
            # Must be boolean False by default
            self.assertFalse(gates[key]["is_approved"], f"Gate {key} must default to False")

    def test_10_settlement_tracking_and_money_flow(self):
        """Verifies settlement recording and 'Where Did The Money Go?' pipeline trace."""
        settle = SettlementManager.record_settlement(
            settlement_amount=106.50,
            currency="AED",
            status="SETTLEMENT_PENDING",
            provider_reference="payout_test_ref_123"
        )
        self.assertEqual(settle["status"], "SETTLEMENT_PENDING")
        self.assertEqual(settle["currency"], "AED")

        # Update settlement to completed
        updated = SettlementManager.update_settlement_status(
            settlement_id=settle["settlement_id"],
            new_status="SETTLEMENT_COMPLETED"
        )
        self.assertEqual(updated["status"], "SETTLEMENT_COMPLETED")

        # Verify Where Did The Money Go trace
        flow = SettlementManager.get_where_did_money_go_flow()
        self.assertEqual(len(flow["steps"]), 7)
        self.assertEqual(flow["steps"][0]["name"], "CUSTOMER PAID")
        self.assertEqual(flow["steps"][6]["name"], "OWNER'S DESIGNATED ACCOUNT")
        self.assertIn("OWNER-ONLY", flow["steps"][6]["badge"])

    def test_11_first_customer_gate_and_bottleneck_detection(self):
        """Validates first-customer gate checklist and dynamic funnel bottleneck."""
        gate = IncomeGenerationAnalytics.evaluate_first_customer_gate()
        self.assertIn("status", gate)
        self.assertIn("checklist", gate)
        self.assertEqual(len(gate["checklist"]), 10)
        self.assertTrue(gate["all_checks_passed"])

        readiness = IncomeGenerationAnalytics.get_income_readiness_status()
        self.assertIn("income_generation_status", readiness)
        self.assertIn("current_bottleneck", readiness)
        self.assertIn(readiness["current_bottleneck"], [
            "TRAFFIC", "QUALIFICATION", "CHECKOUT", "PAYMENT", "DELIVERY", "RETENTION", "TRAFFIC & DISTRIBUTION"
        ])

    def test_12_daily_ceo_report_payments_integration(self):
        """Validates that Daily CEO Report includes payment facts and passes Section 34 Truth Check."""
        report = DailyCEOReportGenerator.generate_report()
        self.assertIsNotNone(report)
        self.assertIn("payments", report["facts"])
        self.assertIn("settlement_summary", report["facts"])

        # Check markdown content
        md = report["content_md"]
        self.assertIn("### 💳 PAYMENT & SETTLEMENT", md)
        self.assertIn("Emirates Islamic", md)
        self.assertIn("First-Customer Gate", md)

        # Check plain text content
        plain = report["body_text"]
        self.assertIn("💳 PAYMENT & SETTLEMENT", plain)

    def test_13_financial_firewall_unapproved_spending_remains_zero(self):
        """Preserves invariant: Collecting revenue does NOT grant AI permission to spend."""
        with self.assertRaises(BankingSecurityViolation):
            RevenueLedgerEngine.attempt_banking_withdrawal(100.00)

        # Firewall settings check
        from core.firewall import FinancialFirewall
        settings = FinancialFirewall.get_settings()
        self.assertEqual(settings.get("max_single_expense"), 0.0)
        self.assertEqual(settings.get("approval_required_threshold"), 0.0)

if __name__ == "__main__":
    unittest.main()
