import unittest
import urllib.error
import urllib.request


class ProxyIntegrationTests(unittest.TestCase):
    def test_successful_request(self):
        with urllib.request.urlopen(
            "http://localhost:8080/",
            timeout=5,
        ) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(
                response.headers.get_content_type(),
                "text/html",
            )

            body = response.read()
            expected_bodies = {
                f"<h1>Hello from backend on port {port}</h1>".encode()
                for port in (8081, 8082, 8083)
            }
            self.assertIn(body, expected_bodies)
            self.assertEqual(
                int(response.headers["Content-Length"]),
                len(body),
            )

    def test_backend_404_is_preserved(self):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(
                    "http://localhost:8080/missing",
                    timeout=5,
                )

            with caught.exception as response:
                self.assertEqual(response.code, 404)
                self.assertEqual(
                    response.headers.get_content_type(),
                    "text/plain",
                )
                self.assertEqual(response.read(), b"Resource not found")

    def test_round_robin_visits_every_backend(self):
        responses = []

        for _ in range(3):
            with urllib.request.urlopen(
                "http://localhost:8080/",
                timeout=5,
            ) as response:
                self.assertEqual(response.status, 200)
                responses.append(response.read())

        expected = {
            f"<h1>Hello from backend on port {port}</h1>".encode()
            for port in (8081, 8082, 8083)
        }

        self.assertEqual(set(responses), expected)


if __name__ == "__main__":
    unittest.main()