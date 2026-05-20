# Day 1: Load Balancer & Reverse Proxy

## What is a Load Balancer?

When millions of users hit a website, one server can't handle all the traffic. A load balancer sits in front of multiple servers and distributes incoming requests across them.

```
Users → Load Balancer → Server 1
                      → Server 2
                      → Server 3
```

**Real-life analogy:** A security guard at a bank who directs customers to available counters.

## What is a Reverse Proxy?

A reverse proxy sits between users and servers. Users never talk to the real server directly.

```
Without proxy:  User → Server
With proxy:     User → Reverse Proxy → Server
```

Benefits:
- **Security** — hides real server addresses from attackers
- **Caching** — stores common responses, reduces server load
- **SSL Termination** — handles encryption so servers don't have to

A load balancer is a reverse proxy that distributes traffic across **multiple** servers.

## Key Concepts Implemented

### 1. Round Robin Algorithm

Requests are distributed in a cycle: Server 1 → Server 2 → Server 3 → Server 1 → ...

```python
server = servers[current % len(servers)]
current += 1
```

### 2. Error Handling / Failover

If a server is down, the load balancer skips it and tries the next one. If all servers are down, it returns a `503 Service Unavailable` response.

### 3. Health Checks

A background thread pings every server every 5 seconds:
- If a server responds → marked as **healthy**
- If a server doesn't respond → marked as **down** and removed from rotation

When a downed server comes back online, it's automatically added back.

## Architecture

```
                    ┌──────────────────┐
                    │   Load Balancer   │
                    │   (port 8080)     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼─────┐  ┌────▼────────┐
     │  Server 1  │  │  Server 2  │  │  Server 3   │
     │ (port 8081)│  │ (port 8082)│  │ (port 8083) │
     └────────────┘  └────────────┘  └─────────────┘
```

## Files

| File | Description |
|------|-------------|
| `server.py` | Simple HTTP server that responds with a message |
| `load_balancer.py` | Round-robin load balancer with health checks and failover |

## How to Run

### 1. Start the backend servers (each in a separate terminal)

```bash
python server.py 8081
python server.py 8082
python server.py 8083
```

### 2. Start the load balancer (in a new terminal)

```bash
python load_balancer.py
```

### 3. Test it

```bash
# Hit the load balancer multiple times — responses rotate between servers
curl http://localhost:8080
curl http://localhost:8080
curl http://localhost:8080
```

### 4. Test failover

Kill one of the backend servers (Ctrl+C), then curl the load balancer again. It will skip the dead server and route to healthy ones.

### 5. Test health checks

Watch the load balancer terminal logs. Every 5 seconds you'll see:

```
http://localhost:8081 is healthy ✓
http://localhost:8082 is down ✗
http://localhost:8083 is healthy ✓
```

Restart the killed server — it will be detected as healthy within 5 seconds.

## Other Load Balancing Algorithms (For Interview Knowledge)

| Algorithm | How It Works | Use Case |
|-----------|-------------|----------|
| **Round Robin** | Cycles through servers in order | Servers have equal capacity |
| **Weighted Round Robin** | Stronger servers get more traffic | Mixed server capacities |
| **Least Connections** | Sends to server with fewest active connections | Long-lived connections |
| **IP Hash** | Same client IP always goes to same server | When sessions need stickiness |

## L4 vs L7 Load Balancers

- **L4 (Transport Layer):** Routes based on IP and port. Fast, no content inspection. Example: AWS NLB
- **L7 (Application Layer):** Routes based on URL, headers, cookies. Smarter routing. Example: AWS ALB, Nginx

## Interview Tip

> "I'd place an L7 load balancer in front of the application servers to distribute traffic using round-robin. Health checks would automatically remove unhealthy instances. For path-based routing — like sending /api requests to API servers and /static to a CDN — an L7 balancer is the right choice."
