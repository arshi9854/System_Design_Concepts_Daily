from http.server import BaseHTTPRequestHandler, HTTPServer

import sys
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Hello, World!</h1>')


if __name__ == '__main__':
    port = int(sys.argv[1])                                                                                                  
    server = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
    server.serve_forever()
