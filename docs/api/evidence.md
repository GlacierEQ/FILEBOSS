# Evidence API

## Overview
The Evidence API manages digital evidence in the FILEBOSS system. Evidence can include documents, images, videos, and other file types relevant to legal cases. The API supports file uploads, metadata management, and integration with AI analysis services.

## Base URL
```
https://api.fileboss.example.com/v1
```

## Endpoints

### Upload Evidence

**POST** `/evidence/upload`

Uploads a new evidence file. This is a multipart form-data request.

#### Request Headers
- `Content-Type`: `multipart/form-data`
- `Authorization`: `Bearer <access_token>`

#### Form Data
- `file` (required): The file to upload
- `case_id` (required): ID of the case this evidence belongs to
- `name` (optional): Custom name for the evidence
- `description` (optional): Description of the evidence
- `type` (optional): Type of evidence (e.g., document, image, video, audio)
- `tags` (optional): Comma-separated list of tags
- `metadata` (optional): JSON string with additional metadata

#### Request
```http
POST /evidence/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="contract.pdf"
Content-Type: application/pdf

<file content here>
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="case_id"

550e8400-e29b-41d4-a716-446655440000
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="description"

Signed contract from 2022
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

#### Response
```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "File is being processed",
  "location": "/evidence/status/123e4567-e89b-12d3-a456-426614174000"
}
```

### Get Evidence Status

**GET** `/evidence/status/{job_id}`

Gets the status of an evidence processing job.

#### Path Parameters
- `job_id` (string, required): The processing job ID

#### Request
```http
GET /evidence/status/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "evidence_id": "660e8400-e29b-41d4-a716-446655440000",
  "progress": 100,
  "message": "Processing complete",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:01:30Z"
}
```

### Get Evidence

**GET** `/evidence/{evidence_id}`

Retrieves evidence metadata by ID.

#### Path Parameters
- `evidence_id` (string, required): The ID of the evidence to retrieve

#### Request
```http
GET /evidence/660e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "contract.pdf",
  "original_name": "contract_2022_signed.pdf",
  "description": "Signed contract from 2022",
  "type": "document",
  "status": "processed",
  "file_size": 1234567,
  "mime_type": "application/pdf",
  "storage_path": "/cases/550e8400/evidence/660e8400.pdf",
  "hash_sha256": "a1b2c3...",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:01:30Z",
  "metadata": {
    "pages": 15,
    "author": "John Smith",
    "title": "Service Agreement",
    "created": "2022-06-15T00:00:00Z",
    "modified": "2022-06-16T00:00:00Z"
  },
  "ai_analysis": {
    "status": "completed",
    "summary": "This appears to be a service agreement between Company A and Client B...",
    "key_terms": ["confidentiality", "term", "termination", "payment"],
    "sentiment": "neutral",
    "entities": [
      {"type": "PERSON", "text": "John Smith", "start": 123, "end": 133},
      {"type": "ORGANIZATION", "text": "Acme Corp", "start": 145, "end": 154}
    ]
  },
  "tags": ["contract", "2022", "signed"],
  "permissions": {
    "can_download": true,
    "can_edit": true,
    "can_delete": false
  }
}
```

### Download Evidence

**GET** `/evidence/{evidence_id}/download`

Downloads the evidence file.

#### Path Parameters
- `evidence_id` (string, required): The ID of the evidence to download

#### Query Parameters
- `version` (string, optional): Specific version to download (if versioning is enabled)
- `format` (string, optional): Requested format (e.g., 'pdf', 'txt' for conversion if supported)

#### Request
```http
GET /evidence/660e8400-e29b-41d4-a716-446655440000/download
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="contract.pdf"
Content-Length: 1234567

<file content>
```

### Update Evidence

**PATCH** `/evidence/{evidence_id}`

Updates evidence metadata.

#### Path Parameters
- `evidence_id` (string, required): The ID of the evidence to update

#### Request
```http
PATCH /evidence/660e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Contract 2022 - Final",
  "description": "Final signed contract from 2022 with all amendments",
  "tags": ["contract", "2022", "signed", "final"]
}
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Contract 2022 - Final",
  "description": "Final signed contract from 2022 with all amendments",
  "tags": ["contract", "2022", "signed", "final"],
  "updated_at": "2023-01-02T14:30:00Z"
}
```

### Delete Evidence

**DELETE** `/evidence/{evidence_id}`

Marks evidence as deleted (soft delete).

#### Path Parameters
- `evidence_id` (string, required): The ID of the evidence to delete

#### Query Parameters
- `permanent` (boolean, optional): If true, permanently deletes the evidence (admin only)

#### Request
```http
DELETE /evidence/660e8400-e29b-41d4-a716-446655440000
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 204 No Content
```

### Search Evidence

**GET** `/evidence/search`

Searches evidence across all accessible cases.

#### Query Parameters
- `q` (string, required): Search query
- `case_id` (string, optional): Filter by case ID
- `type` (string, optional): Filter by evidence type
- `tags` (string, optional): Comma-separated list of tags to filter by
- `from_date` (string, optional): Filter by creation date (ISO 8601)
- `to_date` (string, optional): Filter by creation date (ISO 8601)
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20, max: 100)
- `sort` (string, optional): Sort field (e.g., `created_at:desc`)

#### Request
```http
GET /evidence/search?q=confidentiality&tags=contract&page=1&page_size=10
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
      "name": "NDA_Agreement.pdf",
      "description": "Non-disclosure agreement with vendor",
      "type": "document",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "case_title": "Smith v. Johnson",
      "snippet": "...confidential information as defined in Section 5...",
      "tags": ["nda", "contract", "confidential"],
      "created_at": "2023-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "facets": {
    "types": [
      {"value": "document", "count": 1}
    ],
    "tags": [
      {"value": "contract", "count": 1},
      {"value": "nda", "count": 1},
      {"value": "confidential", "count": 1}
    ],
    "cases": [
      {"id": "550e8400-e29b-41d4-a716-446655440000", "title": "Smith v. Johnson", "count": 1}
    ]
  }
}
```

## Data Models

### Evidence
```typescript
interface Evidence {
  id: string;
  case_id: string;
  name: string;
  original_name: string;
  description?: string;
  type: string;
  status: 'uploading' | 'processing' | 'processed' | 'error';
  file_size: number;
  mime_type: string;
  storage_path: string;
  hash_sha256: string;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  deleted_at?: string; // ISO 8601 datetime
  metadata?: Record<string, any>;
  ai_analysis?: {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    summary?: string;
    key_terms?: string[];
    sentiment?: 'positive' | 'negative' | 'neutral' | 'mixed';
    entities?: Array<{
      type: string;
      text: string;
      start: number;
      end: number;
      metadata?: Record<string, any>;
    }>;
    raw_data?: any;
    processed_at?: string; // ISO 8601 datetime
  };
  tags?: string[];
  permissions?: {
    can_download: boolean;
    can_edit: boolean;
    can_delete: boolean;
  };
}
```

### Search Response
```typescript
interface SearchResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  facets?: {
    types?: Array<{ value: string; count: number }>;
    tags?: Array<{ value: string; count: number }>;
    cases?: Array<{ id: string; title: string; count: number }>;
    [key: string]: any;
  };
}
```

## Error Responses

### 400 Bad Request
- Invalid request parameters
- Missing required fields
- File too large
- Unsupported file type

### 401 Unauthorized
- Missing or invalid authentication token

### 403 Forbidden
- User does not have permission to access the requested resource
- Action not allowed on this evidence item

### 404 Not Found
- Evidence with the specified ID was not found
- Case not found (when linking evidence)

### 409 Conflict
- Evidence with the same name already exists in this case

### 413 Payload Too Large
- Uploaded file exceeds maximum allowed size

### 415 Unsupported Media Type
- Unsupported file format

### 422 Unprocessable Entity
- Validation error with the request data
- Invalid metadata format
- Invalid tag format
