from decimal import Decimal

from django.test import Client, TestCase

from .models import Transaction


class TransactionSyncAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def base_transaction_payload(self, **overrides):
        payload = {
            "id": "txn_validation",
            "amount": "125.50",
            "date": "2026-04-09T12:00:00Z",
            "category": "food",
            "type": "expense",
            "description": "Almoco",
        }
        payload.update(overrides)
        return payload

    def test_create_rejects_invalid_domain_values_with_friendly_messages(self):
        cases = [
            (
                {"amount": "0"},
                "amount",
                "O valor da transação deve ser maior que zero.",
            ),
            (
                {"amount": "-10.00"},
                "amount",
                "O valor da transação deve ser maior que zero.",
            ),
            (
                {"description": "   "},
                "description",
                "Informe uma descrição para a transação.",
            ),
            (
                {"description": "a" * 256},
                "description",
                "A descrição deve ter no máximo 255 caracteres.",
            ),
            (
                {"category": "crypto"},
                "category",
                "Escolha uma categoria válida.",
            ),
            (
                {"date": "2026-31-99"},
                "date",
                "Informe uma data válida.",
            ),
        ]

        for overrides, field, message in cases:
            with self.subTest(overrides=overrides):
                response = self.client.post(
                    "/api/transactions/",
                    self.base_transaction_payload(**overrides),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["message"], "Revise os campos destacados.")
                self.assertEqual(response.json()["fields"][field], message)

    def test_create_rejects_category_that_does_not_match_transaction_type(self):
        response = self.client.post(
            "/api/transactions/",
            self.base_transaction_payload(category="salary", type="expense"),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["message"], "Revise os campos destacados.")
        self.assertEqual(
            response.json()["fields"]["category"],
            "A categoria escolhida não combina com o tipo da transação.",
        )

    def test_create_returns_standard_error_shape_for_duplicate_id(self):
        Transaction.objects.create(
            id="txn_validation",
            amount=Decimal("10.00"),
            date="2026-04-11T09:00:00Z",
            category="food",
            type=Transaction.Type.EXPENSE,
            description="Cafe",
        )

        response = self.client.post(
            "/api/transactions/",
            self.base_transaction_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["message"], "Não foi possível salvar a transação.")
        self.assertEqual(
            response.json()["fields"]["id"],
            "Já existe uma transação com este identificador.",
        )

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
            "Informe os dados da transação para adicionar ou atualizar.",
        )

    def test_delete_transaction_is_idempotent(self):
        response = self.client.delete("/api/transactions/mns1x8g8pl6acfc")

        self.assertEqual(response.status_code, 204)

    def test_delete_transaction_accepts_trailing_slash(self):
        response = self.client.delete("/api/transactions/mns1c8pg02cd630/")

        self.assertEqual(response.status_code, 204)
