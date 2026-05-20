from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import threading
import time


class LoadBalancer(BaseHTTPRequestHandler):
    servers = ["http://localhost:8081", "http://localhost:8082", "http://localhost:8083"]
    healthy_servers = servers.copy()
    current = 0
    
    def do_GET(self):
      servers = self.healthy_servers                                                                                       
      if not servers:
          self.send_response(503)                                                                                          
          self.end_headers()
          self.wfile.write(b'All servers are down')
          return                                                                                                           
   
      for i in range(len(servers)):                                                                                        
          server = servers[LoadBalancer.current % len(servers)]
          LoadBalancer.current = (LoadBalancer.current + 1) % len(servers)
                                                                                                                           
          try:
              response = urllib.request.urlopen(server + self.path)                                                        
              self.send_response(200)
              self.send_header('Content-type', 'text/html')
              self.end_headers()
              self.wfile.write(response.read())
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
    HTTPServer(('localhost', 8080), LoadBalancer).serve_forever()
