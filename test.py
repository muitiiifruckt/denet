import unittest
from fastapi.testclient import TestClient
from main import app  # Импортируй app из своего файла, например main.py

client = TestClient(app)

class TestTokenAPI(unittest.TestCase):

    def print_debug(self, title, sent=None, expected=None, received=None):
        print(f"\n--- {title} ---")
        if sent is not None:
            print(f"🔸 Sent: {sent}")
        if expected is not None:
            print(f"✅ Expected: {expected}")
        if received is not None:
            print(f"📥 Received: {received}")

    def test_get_balance(self):
        address = "0x51f1774249Fc2B0C2603542Ac6184Ae1d048351d"
        response = client.get(f"/get_balance?address={address}")
        data = response.json()

        self.print_debug(
            "TEST get_balance",
            sent={"address": address},
            expected="response with 'balance'",
            received=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("balance", data)

    def test_get_balance_batch(self):
        addresses = [
            "0x51f1774249Fc2B0C2603542Ac6184Ae1d048351d",
            "0x4830AF4aB9cd9E381602aE50f71AE481a7727f7C"
        ]
        response = client.post("/get_balance_batch", json={"addresses": addresses})
        data = response.json()

        self.print_debug(
            "TEST get_balance_batch",
            sent={"addresses": addresses},
            expected="response with list of 2 balances",
            received=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("balances", data)
        self.assertIsInstance(data["balances"], list)
        self.assertEqual(len(data["balances"]), 2)

    def test_get_top(self):
        n = 3
        response = client.get(f"/get_top?n={n}")
        data = response.json()

        self.print_debug(
            "TEST get_top",
            sent={"n": n},
            expected=f"top list with <= {n} items",
            received=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("top", data)
        self.assertIsInstance(data["top"], list)
        self.assertLessEqual(len(data["top"]), n)

    def test_get_top_with_transactions(self):
        n = 3
        response = client.get(f"/get_top_with_transactions?n={n}")
        data = response.json()

        self.print_debug(
            "TEST get_top_with_transactions",
            sent={"n": n},
            expected="list of (address, balance, last_tx_date)",
            received=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("top_with_tx", data)
        self.assertIsInstance(data["top_with_tx"], list)

    def test_get_token_info(self):
        response = client.get("/get_token_info")
        data = response.json()

        self.print_debug(
            "TEST get_token_info",
            sent=None,
            expected="token info with name, symbol, totalSupply",
            received=data
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("name", data)
        self.assertIn("symbol", data)
        self.assertIn("totalSupply", data)

if __name__ == "__main__":
    unittest.main()
