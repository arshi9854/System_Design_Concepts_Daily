from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
import threading
import time
import urllib.error
import os


class LoadBalancer(BaseHTTPRequestHandler):
    servers = [
        address.strip().rstrip("/")
        for address in os.environ.get(
            "BACKEND_URLS",
            "http://localhost:8081, http://localhost:8082, http://localhost:8083",
        ).split(",")
        if address.strip()
    ]
    healthy_servers = servers.copy()
    current = 0
    routing_lock = threading.Lock()

    max_inflight = int(os.environ.get("MAX_INFLIGHT", "100"))

    if max_inflight < 1:
        raise ValueError("MAX_INFLIGHT must be at least 1")

    request_slots = threading.BoundedSemaphore(max_inflight)

    def do_GET(self):
        if not self.request_slots.acquire(blocking=False):
            body = b"Load balancer is busy"
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Retry-After", "1")
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            self.handle_proxy_request()
        finally:
            self.request_slots.release()


    def handle_proxy_request(self):
        servers = self.healthy_servers

        if not servers:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'All servers are down')
            return

        with LoadBalancer.routing_lock:
            start_index = LoadBalancer.current % len(servers)
            LoadBalancer.current = (start_index + 1) % len(servers)

        for i in range(len(servers)):
            server = servers[(start_index + i) % len(servers)]

            try:
                with urllib.request.urlopen(
                    server + self.path,
                    timeout=2,
                ) as response:
                    body = response.read()
                    status = response.status
                    content_type = response.headers.get(
                        'Content-Type', 'application/octet-stream'
                    )

                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except urllib.error.HTTPError as error:
                with error:
                    body = error.read()
                    status = error.code
                    content_type = error.headers.get(
                        'Content-Type', 'application/octet-stream'
                    )

                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            except:
                print(f"{server} is down, trying next...")

        self.send_response(503)
        self.end_headers()
        self.wfile.write(b'All servers are down')

                                                                                         

def health_check():                                                                                                      
    while True:
        healthy = []                                                                                                     
        for server in LoadBalancer.servers:
            try:
                with urllib.request.urlopen(server + "/healthz", timeout=2) as response:
                    if response.status != 200:
                        raise ValueError("Health check returned a non-200 status")
                healthy.append(server)                                                                                   
            except (urllib.error.URLError, TimeoutError, ValueError):                                                                                                      
                pass
        previous = set(LoadBalancer.healthy_servers)
        current = set(healthy)

        for server in sorted(previous - current):
            print(f'{server} is down')
        
        for server in sorted(current - previous):
            print(f'{server} is healthy again')
        
        LoadBalancer.healthy_servers = healthy
        time.sleep(5)


if __name__ == '__main__':
    threading.Thread(target=health_check, daemon=True).start()
    ThreadingHTTPServer(('localhost', 8080), LoadBalancer).serve_forever()