## Quick start

From the repository root, run:

```bash
python3 loadbalancer/run_local.py
```

This starts:
- Load balancer on port 8080
- Backends on ports 8081, 8082, and 8083

Keep this terminal running. In another terminal, test a request:

```bash
curl http://localhost:8080/
```

Press Ctrl+C in the startup terminal to stop all four servers.
Ports 8080–8083 must be available before starting.


## Automated tests

From the repository root, run:

```bash
python3 -m unittest discover -s loadbalancer/tests -p 'test_proxy.py' -v
```

The tests automatically start the load balancer and three backends,
wait for readiness, and stop them afterward.

Ports 8080–8083 must be available. Stop any manually started servers
or `run_local.py` before running the tests.

The tests verify:
- Successful responses include the expected body, content type,
  and content length.
- Backend 404 responses reach the client correctly.
- Three consecutive requests visit all three healthy backends.