import unittest
import urllib.error
import urllib.request
from pathlib import Path
import os
import subprocess
import sys
import time

PROCESSES = []


def tearDownModule():
    for process in PROCESSES:
        if process.poll() is None:
            process.terminate()

    for process in PROCESSES:
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    PROCESSES.clear()

def setUpModule():
    project_dir = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["BACKEND_URLS"] = (
        "http://localhost:8081,"
        "http://localhost:8082,"
        "http://localhost:8083"
    )

    commands = [
        ["server.py", "8081"],
        ["server.py", "8082"],
        ["server.py", "8083"],
        ["load_balancer.py"],
    ]

    try:
        for command in commands:
            PROCESSES.append(
                subprocess.Popen(
                    [sys.executable, *command],
                    cwd=project_dir,
                    env=environment,
                )
            )

        pending = {8080, 8081, 8082, 8083}
        deadline = time.monotonic() + 10

        while pending:
            if any(p.poll() is not None for p in PROCESSES):
                raise RuntimeError("A test server exited during startup")

            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Servers did not become ready: {sorted(pending)}"
                )

            for port in list(pending):
                try:
                    with urllib.request.urlopen(
                        f"http://localhost:{port}/healthz",
                        timeout=0.5,
                    ) as response:
                        if response.status == 200:
                            pending.remove(port)
                except (urllib.error.URLError, TimeoutError):
                    pass

            if pending:
                time.sleep(0.1)

    except BaseException:
        tearDownModule()
        raise


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