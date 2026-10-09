from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import time
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == "/healthz":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
            
        if self.path == "/missing":
            body = b"Resource not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/slow" and self.server.server_port == 8082:
            time.sleep(5)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        port = self.server.server_port
        message = f"<h1>Hello from backend on port {port}</h1>"
        self.wfile.write(message.encode("utf-8"))


if __name__ == '__main__':
    port = int(sys.argv[1])                                                                                                  
    server = ThreadingHTTPServer(
    ('localhost', port),
    SimpleHTTPRequestHandler,
)
    server.serve_forever()
