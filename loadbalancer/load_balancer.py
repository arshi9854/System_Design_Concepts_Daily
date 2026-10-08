from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
import threading
import time
import urllib.error


class LoadBalancer(BaseHTTPRequestHandler):
    servers = ["http://localhost:8081", "http://localhost:8082", "http://localhost:8083"]
    healthy_servers = servers.copy()
    current = 0
    routing_lock = threading.Lock()

    def do_GET(self):
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
                  urllib.request.urlopen(server, timeout=2)
                  healthy.append(server)                                                                                   
                  print(f"{server} is healthy ✓")
              except:                                                                                                      
                  print(f"{server} is down ✗")
          LoadBalancer.healthy_servers = healthy
          time.sleep(5)


if __name__ == '__main__':
    threading.Thread(target=health_check, daemon=True).start()
    ThreadingHTTPServer(('localhost', 8080), LoadBalancer).serve_forever()