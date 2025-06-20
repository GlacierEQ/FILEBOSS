# Cases API

## Overview
The Cases API manages legal cases in the FILEBOSS system. Each case can contain multiple pieces of evidence, documents, and timeline events.

## Base URL
```
https://api.fileboss.example.com/v1
```

## Endpoints

### List Cases

**GET** `/cases`

Retrieves a paginated list of cases.

#### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20, max: 100)
- `status` (string, optional): Filter by case status
- `assignee_id` (string, optional): Filter by assignee ID
- `client_id` (string, optional): Filter by client ID
- `sort` (string, optional): Sort field (e.g., `created_at:desc`)

#### Request
```http
GET /cases?page=1&page_size=20&status=open
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "case_number": "2023-CIV-001",
      "title": "Smith v. Johnson",
      "description": "Breach of contract dispute",
      "status": "open",
      "priority": "high",
      "client_id": "660e8400-e29b-41d4-a716-446655440000",
      "assigned_to": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Create Case

**POST** `/cases`

Creates a new case.

#### Request
```http
POST /cases
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "case_number": "2023-CIV-001",
  "title": "Smith v. Johnson",
  "description": "Breach of contract dispute",
  "status": "open",
  "priority": "high",
  "client_id": "660e8400-e29b-41d4-a716-446655440000",
  "assigned_to": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "case_number": "2023-CIV-001",
  "title": "Smith v. Johnson",
  "description": "Breach of contract dispute",
  "status": "open",
  "priority": "high",
  "client_id": "660e8400-e29b-41d4-a716-446655440000",
  "assigned_to": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

### Get Case

**GET** `/cases/{case_id}`

Retrieves a specific case by ID.

#### Path Parameters
- `case_id` (string, required): The ID of the case to retrieve

#### Request
```http
GET /cases/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "case_number": "2023-CIV-001",
  "title": "Smith v. Johnson",
  "description": "Breach of contract dispute",
  "status": "open",
  "priority": "high",
  "client_id": "660e8400-e29b-41d4-a716-446655440000",
  "assigned_to": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "metadata": {
    "evidence_count": 5,
    "document_count": 12,
    "timeline_events": 8
  }
}
```

### Update Case

**PATCH** `/cases/{case_id}`

Updates a specific case.

#### Path Parameters
- `case_id` (string, required): The ID of the case to update

#### Request
```http
PATCH /cases/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "in_review",
  "priority": "medium"
}
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "case_number": "2023-CIV-001",
  "title": "Smith v. Johnson",
  "description": "Breach of contract dispute",
  "status": "in_review",
  "priority": "medium",
  "client_id": "660e8400-e29b-41d4-a716-446655440000",
  "assigned_to": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-02T10:30:00Z"
}
```

### Delete Case

**DELETE** `/cases/{case_id}`

Marks a case as deleted (soft delete).

#### Path Parameters
- `case_id` (string, required): The ID of the case to delete

#### Request
```http
DELETE /cases/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 204 No Content
```

### List Case Evidence

**GET** `/cases/{case_id}/evidence`

Retrieves evidence associated with a case.

#### Path Parameters
- `case_id` (string, required): The ID of the case

#### Query Parameters
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20, max: 100)
- `type` (string, optional): Filter by evidence type
- `status` (string, optional): Filter by evidence status
- `sort` (string, optional): Sort field (e.g., `created_at:desc`)

#### Request
```http
GET /cases/550e8400-e29b-41d4-a716-446655440000/evidence
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "name": "Contract_2022.pdf",
      "description": "Signed contract from 2022",
      "type": "document",
      "status": "processed",
      "file_size": 1234567,
      "mime_type": "application/pdf",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

## Data Models

### Case
```typescript
interface Case {
  id: string;
  case_number: string;
  title: string;
  description?: string;
  status: 'open' | 'in_review' | 'closed' | 'archived';
  priority: 'low' | 'medium' | 'high' | 'critical';
  client_id: string;
  assigned_to?: string;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  deleted_at?: string; // ISO 8601 datetime
  metadata?: {
    evidence_count: number;
    document_count: number;
    timeline_events: number;
  };
}
```

### Case List Response
```typescript
interface CaseListResponse {
  items: Case[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
```

## Error Responses

### 400 Bad Request
Invalid request parameters or missing required fields.

### 401 Unauthorized
Missing or invalid authentication token.

### 403 Forbidden
User does not have permission to access the requested resource.

### 404 Not Found
Case with the specified ID was not found.

### 409 Conflict
Case with the same case number already exists.

### 422 Unprocessable Entity
Validation error with the request data.
