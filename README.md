# Event Driven Order Processing System

## Overview

This project demonstrates a **simple event-driven architecture** using **Apache Kafka**, **Docker**, and **Python services**.

Instead of processing orders synchronously, the API publishes events to Kafka which are then processed by a downstream service.

This architecture improves:

- scalability
- decoupling of services
- fault tolerance

---

# Architecture
Client --> Order API --> Kafka (orders topic) --> Order Processor --> Database


### Components

#### Order API

- Receives order requests
- Generates a unique `order_id`
- Publishes order events to Kafka

#### Kafka

- Acts as the event streaming platform
- Stores order events temporarily
- Allows downstream consumers to process them asynchronously

#### Order Processor

- Consumes order events from Kafka
- Processes the order
- Stores the result in the database

---

# Kafka Design Decisions

## Topic Strategy

For this portfolio project, a **single Kafka topic (`orders`)** is used.

Because the expected message volume is low, a single topic keeps the system simple and easy to understand.

In a production system, it would be better to separate topics by event type, for example:

- `orders-created`
- `payments-processed`
- `orders-shipped`

Benefits of multiple topics include:

- higher throughput
- clearer separation of responsibilities
- easier scaling of individual services

---

## Partition Key

The partition key chosen is **`order_id`**.

Reasons:

- Each order has a unique identifier
- Ensures events for the same order go to the same partition
- Avoids duplicates that could occur with fields such as:

    - `customer_id` (customers may place multiple orders)
    - `product_id` (many orders may contain the same product)

Random partition keys could work, but most systems already generate a unique `order_id`, so using it is the most natural and reliable option.

---

## Replication Factor

For this project:

```replication.factor = 1```


This is because the system currently runs **only one Kafka broker locally**.

In production environments, a **replication factor of at least 3** is typically used to provide fault tolerance and high availability.

---

## Data Retention

For an ordering system, **short retention periods are generally preferred** because order events may contain sensitive customer information.

Kafka should be used primarily as an **event transport layer**, not long-term storage.

Long-term records should instead be stored in a secure database.

---

# Running the System

Start the environment with Docker Compose:

```bash
docker compose up
```

This will start:

* Kafka

* Zookeeper

* Order API

* Order Processor

# Technologies Used

* Apache Kafka

* Docker / Docker Compose

* Python

* FastAPI

* kafka-python client

# Future Improvements

This project demonstrates the core concepts of an event-driven architecture, but several improvements would be implemented in a production environment.

## Schema Registry

Introduce a schema management system such as **Confluent Schema Registry** with **Avro or Protobuf**.

Benefits:

- enforce message structure
- prevent producers from sending invalid data
- enable safe schema evolution

Example improvements:

- versioned schemas
- backward compatibility validation
- consumer schema negotiation

---

## Dead Letter Queue (DLQ)

Introduce a **Dead Letter Queue topic** (e.g., `orders-dlq`) to capture messages that fail processing.

Reasons:

- prevents message loss
- allows investigation of failed events
- avoids blocking the consumer pipeline

Example workflow:
orders topic → Order Processor → ├── success → database | failure → orders-dlq |

---

## Retry Mechanism

Implement a retry strategy for transient failures such as:

- temporary database outages
- downstream service failures
- network issues

Possible approaches:

- retry topics (`orders-retry`)
- exponential backoff
- scheduled retries

---

## Increased Partitioning

Currently, the `orders` topic uses a minimal configuration.

In production, increasing the number of partitions would allow:

- parallel message processing
- higher throughput
- horizontal scaling of consumers

Example:
```bash
orders topic
partitions: 6+
```
Consumers in the same **consumer group** could then process events in parallel.

---

## Observability and Monitoring

Add monitoring and tracing to improve system reliability.

Potential tools:

- Prometheus
- Grafana
- OpenTelemetry
- centralized logging (ELK stack)

Key metrics to monitor:

- consumer lag
- message throughput
- error rates
- processing latency

---

## Security

For production environments, the following would be implemented:

- TLS encryption for Kafka communication
- SASL authentication
- secrets management
- encryption of sensitive customer data

---

## Idempotent Consumers

To prevent duplicate processing, consumers should implement **idempotency guarantees**.

Approaches include:

- storing processed `order_id`s
- transactional message processing
- Kafka exactly-once semantics

---

# Summary

This project demonstrates a basic **event-driven order processing pipeline using Kafka**. While intentionally 
simple for demonstration purposes, the architecture can be expanded with schema management, retry strategies, 
monitoring, and security features to support real-world production workloads.