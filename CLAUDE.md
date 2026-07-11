# SmartBid AI

## Project Overview

SmartBid AI is an enterprise B2B procurement platform that automates the comparison of Request for Proposal (RFP) documents against multiple vendor datasheets.

The application is intended for real-world commercial use by pre-sales engineers, bid managers, and procurement teams.

The primary objective is to produce an explainable and deterministic Compliance Matrix that compares vendor offerings against customer requirements.

---

# Core Philosophy

This is NOT an AI chatbot.

This is NOT a document Q&A system.

This is NOT a generic RAG application.

The system is a structured document processing platform.

AI is used only to transform unstructured documents into structured data.

All business decisions are made by deterministic backend logic.

---

# High-Level Architecture

```
Frontend (React)
        │
        ▼
FastAPI Backend
        │
        ├─────────────── PostgreSQL (Supabase)
        │
        ├─────────────── Supabase Storage
        │
        ├─────────────── Redis
        │
        └─────────────── Celery Workers
```

---

# Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Shadcn UI
- TanStack Query
- TanStack Table
- React Hook Form
- Zod

## Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2

## Database

Supabase PostgreSQL

Use JSONB for extracted document data.

Do NOT use pgvector in the MVP.

## Storage

Supabase Storage

Never store PDFs inside PostgreSQL.

Only store metadata and storage paths.

## Background Jobs

Redis

Celery

## OCR

PyMuPDF

PaddleOCR

## AI

OpenAI GPT-5.5 (or Claude Sonnet)

LLM usage is restricted.

---

# Processing Pipeline

Every uploaded document MUST follow this pipeline.

```
Upload
    ↓
Storage
    ↓
Text Extraction
    ↓
Cleaning
    ↓
Structured JSON Extraction
    ↓
Pydantic Validation
    ↓
Store JSONB
    ↓
Rule-Based Matching
    ↓
Compliance Matrix
    ↓
Report Generation
```

Every stage must be independent.

Each stage should be replaceable without affecting the others.

---

# AI Responsibilities

The LLM is ONLY responsible for:

- Requirement Extraction
- Specification Extraction
- Synonym Understanding
- Unit Normalization

The LLM MUST NEVER

- Compare documents
- Generate compliance percentages
- Rank vendors
- Decide pass/fail
- Perform calculations

---

# Matching Philosophy

The matching engine is deterministic.

Examples

20 >= 20

TRUE

96 >= 95

TRUE

230 == 230

TRUE

All comparisons are implemented in Python.

Never ask the LLM to calculate scores.

---

# Compliance Score

Compliance scores are generated using backend business logic.

Never generate percentages using the LLM.

Every score must be reproducible.

---

# Explainability

Every compliance result must be traceable.

Store

- Source page
- Source paragraph
- Vendor value
- Required value

The user must always be able to verify why a match exists.

---

# Folder Structure

```
backend/

app/

api/
core/
database/
models/
schemas/
repositories/
services/
workers/
utils/

tests/

uploads/

Dockerfile

docker-compose.yml
```

---

# Layer Responsibilities

## API

Only

- Validate requests
- Return responses

No business logic.

---

## Services

Contain all business logic.

Examples

Authentication

Projects

Documents

Extraction

Matching

Reports

---

## Repositories

Contain database queries.

Never write SQL inside services.

---

## Models

SQLAlchemy models only.

---

## Schemas

Pydantic models only.

---

# Services

The application is composed of independent services.

Authentication Service

Project Service

Vendor Service

Document Service

Extraction Service

Validation Service

Matching Service

Report Service

Storage Service

Each service has one responsibility.

---

# Database Design

Primary entities

Users

Projects

Documents

Vendors

Requirements

VendorSpecifications

Matches

Reports

Extracted information should be stored in JSONB.

---

# API Design

RESTful APIs only.

Version every endpoint.

Example

/api/v1/projects

/api/v1/vendors

/api/v1/documents

---

# Authentication

JWT

Access Token

Refresh Token

Role Based Access

Roles

Admin

Engineer

Sales

Viewer

---

# Coding Standards

Use

- Python type hints
- Async where appropriate
- Dependency Injection
- SOLID principles
- Small reusable functions

Avoid

- God classes
- Massive controllers
- Duplicated logic
- Circular imports

---

# Error Handling

Always return structured API responses.

Example

{
    "success": false,
    "message": "Document not found",
    "error_code": "DOCUMENT_NOT_FOUND"
}

Never expose internal exceptions.

---

# Logging

Use structured logging.

Never use print().

Log

- Uploads
- Processing
- Matching
- Errors

---

# Background Jobs

Long-running tasks must run asynchronously.

Examples

OCR

LLM Extraction

Report Generation

Never block HTTP requests.

---

# Performance Goals

Design for

- Multiple projects
- Hundreds of documents
- Thousands of requirements

Optimize database queries.

Avoid N+1 queries.

Use pagination.

---

# Security

Validate every uploaded file.

Limit file size.

Validate MIME types.

Never trust filenames.

Sanitize document inputs.

Store secrets in environment variables.

---

# Testing

Every service should have unit tests.

Business logic must be testable without the API.

Use dependency injection to enable mocking.

---

# Future Features

The architecture should support future additions without major refactoring.

Possible future features

- pgvector
- Semantic Search
- Multi-tenancy
- Team Collaboration
- Audit Logs
- Notifications
- AI Explanations
- Vendor Analytics

Do NOT implement these unless explicitly requested.

---

# Instructions for Claude

Before implementing any feature:

1. Follow the existing architecture.
2. Reuse existing components whenever possible.
3. Do not introduce new libraries unless necessary.
4. Keep business logic inside services.
5. Keep APIs thin.
6. Ask for clarification if requirements conflict with this document.
7. Prioritize readability and maintainability over clever code.

When generating code:

- Write production-quality code.
- Include docstrings where helpful.
- Use meaningful names.
- Prefer composition over inheritance.
- Do not leave TODOs unless explicitly requested.

## Legacy Code Policy

The codebase may contain legacy modules that do not yet follow the target architecture.

Rules:

- All NEW features MUST follow the target architecture.
- Existing modules should not be refactored unless required.
- When modifying an existing module, improve it incrementally rather than rewriting it completely.
- Avoid mixing business logic into API routes.
- Prefer services and repositories for all new code.