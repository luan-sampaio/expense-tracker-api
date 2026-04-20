from decimal import Decimal

from django.test import Client, TestCase

from .models import Transaction


class TransactionSyncAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sync_applies_mutations_in_order_and_is_idempotent(self):
        payload = {
            "operations": [
                {
                    "client_operation_id": "op-1",
                    "operation": "add",
                    "transaction": {
                        "id": "txn_001",
                        "amount": "125.50",
                        "date": "2026-04-09T12:00:00Z",
                        "category": "food",
                        "type": "expense",
                        "description": "Almoco",
                    },
                },
                {
                    "client_operation_id": "op-2",
                    "operation": "update",
                    "transaction": {
                        "id": "txn_001",
                        "amount": "140.00",
                        "date": "2026-04-09T12:00:00Z",
                        "category": "food",
                        "type": "expense",
                        "description": "Almoco atualizado",
                    },
                },
            ]
        }

        first_response = self.client.post(
            "/api/transactions/sync",
            payload,
            content_type="application/json",
        )
        second_response = self.client.post(
            "/api/transactions/sync",
            payload,
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)

        transaction = Transaction.objects.get(id="txn_001")
        self.assertEqual(transaction.amount, Decimal("140.00"))
        self.assertEqual(transaction.description, "Almoco atualizado")

        results = second_response.json()["results"]
        self.assertEqual([result["status"] for result in results], ["applied", "applied"])

    def test_sync_update_upserts_missing_transaction(self):
        response = self.client.post(
            "/api/transactions/sync",
            {
                "operations": [
                    {
                        "operation": "update",
                        "transaction": {
                            "id": "txn_missing",
                            "amount": "88.90",
                            "date": "2026-04-10T15:30:00Z",
                            "category": "transport",
                            "type": "expense",
                            "description": "Combustivel",
                        },
                    }
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Transaction.objects.filter(id="txn_missing").exists())
        self.assertEqual(response.json()["results"][0]["status"], "applied")

    def test_sync_remove_is_safe_to_retry(self):
        Transaction.objects.create(
            id="txn_002",
            amount=Decimal("10.00"),
            date="2026-04-11T09:00:00Z",
            category="market",
            type=Transaction.Type.EXPENSE,
            description="Cafe",
        )

        payload = {
            "operations": [
                {
                    "client_operation_id": "op-remove",
                    "operation": "remove",
                    "transaction_id": "txn_002",
                }
            ]
        }

        first_response = self.client.post(
            "/api/transactions/sync",
            payload,
            content_type="application/json",
        )
        second_response = self.client.post(
            "/api/transactions/sync",
            payload,
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertFalse(Transaction.objects.filter(id="txn_002").exists())
        self.assertEqual(second_response.json()["results"][0]["status"], "applied")

    def test_sync_reports_invalid_semantic_operation(self):
        response = self.client.post(
            "/api/transactions/sync",
            {"operations": [{"operation": "add"}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["message"],
            "Transaction payload is required for add/update operations.",
        )
