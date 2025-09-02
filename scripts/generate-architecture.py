# File: scripts/generate_architecture.py
"""Generate architecture diagram using Python"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.programming.framework import React, Angular
from diagrams.programming.language import NodeJS, Python, Csharp, Rust
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Kafka
from diagrams.onprem.monitoring import Prometheus, Grafana
from diagrams.onprem.container import Docker
from diagrams.k8s.compute import Pod
from diagrams.k8s.network import Service

with Diagram("Recommendation System Architecture", filename="docs/images/architecture", show=False):
    users = Users("Users")
    
    with Cluster("Client Applications"):
        web = React("Web App")
        mobile = Angular("Mobile App")
    
    with Cluster("API Gateway"):
        gateway = NodeJS("API Gateway\n(Node.js)")
    
    with Cluster("Microservices"):
        ml_service = Python("ML Service\n(FastAPI)")
        user_service = Csharp("User Service\n(.NET)")
        cache_service = Rust("Cache Service\n(Rust)")
    
    with Cluster("Stream Processing"):
        stream = Python("Stream Processor\n(Kafka Streams)")
    
    with Cluster("Data Layer"):
        postgres = PostgreSQL("PostgreSQL")
        redis = Redis("Redis Cache")
        kafka = Kafka("Kafka")
    
    with Cluster("Monitoring"):
        prometheus = Prometheus("Prometheus")
        grafana = Grafana("Grafana")
    
    # Connections
    users >> Edge(label="HTTPS") >> [web, mobile]
    [web, mobile] >> Edge(label="REST API") >> gateway
    
    gateway >> Edge(label="HTTP") >> ml_service
    gateway >> Edge(label="HTTP") >> user_service
    gateway >> Edge(label="HTTP") >> cache_service
    
    ml_service >> Edge(label="Query") >> redis
    ml_service >> Edge(label="Query") >> postgres
    user_service >> Edge(label="Query") >> postgres
    cache_service >> Edge(label="Get/Set") >> redis
    
    stream >> Edge(label="Consume") >> kafka
    ml_service >> Edge(label="Produce") >> kafka
    
    [ml_service, user_service, cache_service] >> Edge(label="Metrics") >> prometheus
    prometheus >> Edge(label="Query") >> grafana

print("Architecture diagram generated at docs/images/architecture.png")
