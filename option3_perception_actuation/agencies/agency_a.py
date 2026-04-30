"""
Endpoints:
- GET /events?since=<timestamp>: return all events since the given timestamp
- GET /health: return status: 
    - 200 OK if the primary agency is healthy, 
    - 503 Service Unavailable if in failover mode and secondary is healthy, 
    - 500 Internal Server Error if both are unhealthy.
"""
 