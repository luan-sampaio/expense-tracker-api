from decimal import Decimal

from django.test import Client, TestCase

from .models import FinancialGoal, Transaction


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

    def test_sync_persists_and_returns_financial_classification_fields(self):
        response = self.client.post(
            "/api/transactions/sync",
            {
                "operations": [
                    {
                        "operation": "add",
                        "transaction": {
                            "id": "txn_investment",
                            "amount": "500.00",
                            "date": "2026-04-21T00:00:00Z",
                            "category": "other",
                            "type": "expense",
                            "description": "Aporte para reserva",
                            "financialNature": "investment",
                            "goalId": "goal-123",
                            "budgetGroupId": None,
                        },
                    }
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        transaction = Transaction.objects.get(id="txn_investment")
        self.assertEqual(transaction.financial_nature, "investment")
        self.assertEqual(transaction.goal_id, "goal-123")
        self.assertIsNone(transaction.budget_group_id)

        returned_transaction = response.json()["transactions"][0]
        self.assertEqual(returned_transaction["financialNature"], "investment")
        self.assertEqual(returned_transaction["goalId"], "goal-123")
        self.assertIsNone(returned_transaction["budgetGroupId"])

    def test_list_returns_financial_classification_fields(self):
        Transaction.objects.create(
            id="txn_budget",
            amount=Decimal("90.00"),
            date="2026-04-21T09:00:00Z",
            category="food",
            type=Transaction.Type.EXPENSE,
            description="Mercado",
            financial_nature=Transaction.FinancialNature.SPENDING,
            budget_group_id="needs",
        )

        response = self.client.get("/api/transactions/")

        self.assertEqual(response.status_code, 200)
        transaction = response.json()["results"][0]
        self.assertEqual(transaction["financialNature"], "spending")
        self.assertEqual(transaction["budgetGroupId"], "needs")
        self.assertIsNone(transaction["goalId"])

    def test_sync_rejects_financial_contribution_without_goal(self):
        response = self.client.post(
            "/api/transactions/sync",
            {
                "operations": [
                    {
                        "operation": "add",
                        "transaction": {
                            "id": "txn_invalid",
                            "amount": "500.00",
                            "date": "2026-04-21T00:00:00Z",
                            "category": "other",
                            "type": "expense",
                            "description": "Aporte sem meta",
                            "financialNature": "saving",
                        },
                    }
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertFalse(Transaction.objects.filter(id="txn_invalid").exists())

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
            "Informe os dados da transação para adicionar ou atualizar.",
        )

    def test_delete_transaction_is_idempotent(self):
        response = self.client.delete("/api/transactions/mns1x8g8pl6acfc")

        self.assertEqual(response.status_code, 204)

    def test_delete_transaction_accepts_trailing_slash(self):
        response = self.client.delete("/api/transactions/mns1c8pg02cd630/")

        self.assertEqual(response.status_code, 204)


class FinancialGoalAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_create_list_update_and_delete_financial_goal(self):
        create_response = self.client.post(
            "/api/financial-goals/",
            {
                "id": "goal-123",
                "name": "Reserva de emergencia",
                "targetAmount": "10000.00",
                "createdAt": "2026-04-21T00:00:00Z",
                "isArchived": False,
            },
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertTrue(FinancialGoal.objects.filter(id="goal-123").exists())
        self.assertEqual(create_response.json()["targetAmount"], "10000.00")

        list_response = self.client.get("/api/financial-goals/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["id"], "goal-123")

        update_response = self.client.put(
            "/api/financial-goals/goal-123",
            {
                "name": "Reserva completa",
                "targetAmount": "12000.00",
                "isArchived": True,
            },
            content_type="application/json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["name"], "Reserva completa")
        self.assertEqual(update_response.json()["targetAmount"], "12000.00")
        self.assertTrue(update_response.json()["isArchived"])

        delete_response = self.client.delete("/api/financial-goals/goal-123")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(FinancialGoal.objects.filter(id="goal-123").exists())
