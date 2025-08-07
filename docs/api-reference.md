# 📚 API Reference

Complete API documentation for the CaseBuilder evidence management system.

## 🌐 Base URL

```
http://localhost:8000
```

## 🔐 Authentication

Currently, the API uses a simplified authentication model. In production, implement proper JWT or OAuth2 authentication.

## 📋 API Endpoints

### System Endpoints

#### GET `/`
**System Information**

Returns basic system information and available endpoints.

**Response:**
```json
{
  "message": "Welcome to CaseBuilder API",
  "version": "0.1.0",
  "environment": "development",
  "api_docs": "/api/v1/docs"
}
```

**Status Codes:**
- `200 OK`: Success

---

#### GET `/health`
**Health Check**

Returns system health status for monitoring and load balancers.

**Response:**
```json
{
  "status": "healthy",
  "service": "CaseBuilder",
  "version": "0.1.0"
}
```

**Status Codes:**
- `200 OK`: System is healthy
- `503 Service Unavailable`: System is unhealthy

---

### Evidence Management Endpoints

#### POST `/api/v1/evidence/upload/`
**Upload Evidence File**

Upload a new evidence file to the system.

**Request:**
- **Content-Type**: `multipart/form-data`
- **Parameters:**
  - `file` (required): The evidence file to upload
  - `case_id` (optional): Case identifier (default: "default_case")
  - `description` (optional): Description of the evidence
  - `tags` (optional): Comma-separated list of tags

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/evidence/upload/" \
  -F "file=@evidence.pdf" \
  -F "case_id=case_001" \
  -F "description=Contract evidence" \
  -F "tags=contract,legal,important"
```

**Response:**
```json
{
  "id": 1,
  "filename": "evidence.pdf",
  "case_id": "case_001",
  "description": "Contract evidence",
  "tags": ["contract", "legal", "important"],
  "created_by": 1,
  "status": "uploaded"
}
```

**Status Codes:**
- `201 Created`: File uploaded successfully
- `400 Bad Request`: Invalid file or parameters
- `413 Payload Too Large`: File size exceeds limit
- `415 Unsupported Media Type`: File type not allowed
- `500 Internal Server Error`: Server error during upload

---

#### GET `/api/v1/evidence/{evidence_id}`
**Retrieve Evidence**

Get details of a specific evidence item by ID.

**Parameters:**
- `evidence_id` (path, required): Unique identifier of the evidence

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/evidence/1"
```

**Response:**
```json
{
  "id": 1,
  "filename": "example.pdf",
  "case_id": "case_001",
  "description": "Sample evidence",
  "tags": ["document"],
  "created_by": 1,
  "status": "uploaded"
}
```

**Status Codes:**
- `200 OK`: Evidence found and returned
- `404 Not Found`: Evidence with specified ID not found
- `500 Internal Server Error`: Server error during retrieval

---

#### PUT `/api/v1/evidence/{evidence_id}`
**Update Evidence**

Update details of an existing evidence item.

**Parameters:**
- `evidence_id` (path, required): Unique identifier of the evidence

**Request Body:**
```json
{
  "description": "Updated description",
  "tags": ["updated", "modified"],
  "status": "reviewed"
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/evidence/1" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated contract evidence", "status": "reviewed"}'
```

**Response:**
```json
{
  "id": 1,
  "filename": "evidence.pdf",
  "case_id": "case_001",
  "description": "Updated contract evidence",
  "tags": ["contract", "legal", "important"],
  "created_by": 1,
  "status": "reviewed"
}
```

**Status Codes:**
- `200 OK`: Evidence updated successfully
- `400 Bad Request`: Invalid update data
- `404 Not Found`: Evidence with specified ID not found
- `500 Internal Server Error`: Server error during update

---

## 📊 Data Models

### Evidence Model

```json
{
  "id": "integer",
  "filename": "string",
  "case_id": "string",
  "description": "string",
  "tags": ["string"],
  "created_by": "integer",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Field Descriptions:**
- `id`: Unique identifier for the evidence
- `filename`: Original filename of the uploaded file
- `case_id`: Identifier linking evidence to a specific case
- `description`: Human-readable description of the evidence
- `tags`: Array of tags for categorization and search
- `created_by`: User ID of the person who uploaded the evidence
- `status`: Current status (uploaded, reviewed, archived, etc.)
- `created_at`: Timestamp when evidence was created
- `updated_at`: Timestamp when evidence was last modified

### Error Response Model

```json
{
  "detail": "string",
  "status_code": "integer",
  "timestamp": "datetime"
}
```

---

## 🔧 Request/Response Examples

### Upload Multiple Files

```bash
# Upload multiple files in sequence
for file in *.pdf; do
  curl -X POST "http://localhost:8000/api/v1/evidence/upload/" \
    -F "file=@$file" \
    -F "case_id=case_001" \
    -F "description=Batch upload: $file"
done
```

### Bulk Update Evidence

```bash
# Update multiple evidence items
evidence_ids=(1 2 3 4 5)
for id in "${evidence_ids[@]}"; do
  curl -X PUT "http://localhost:8000/api/v1/evidence/$id" \
    -H "Content-Type: application/json" \
    -d '{"status": "reviewed"}'
done
```

### Search and Filter (Future Enhancement)

```bash
# Future endpoint for searching evidence
curl -X GET "http://localhost:8000/api/v1/evidence/search?case_id=case_001&status=uploaded&tags=contract"
```

---

## 🚨 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid file format. Only PDF, DOCX, and image files are allowed.",
  "status_code": 400
}
```

#### 404 Not Found
```json
{
  "detail": "Evidence not found",
  "status_code": 404
}
```

#### 413 Payload Too Large
```json
{
  "detail": "File size exceeds maximum limit of 100MB",
  "status_code": 413
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred while processing request",
  "status_code": 500
}
```

---

## 📈 Rate Limiting

Current implementation does not include rate limiting. For production deployment, consider implementing:

- **Per-IP Rate Limiting**: 100 requests per minute
- **Per-User Rate Limiting**: 1000 requests per hour
- **File Upload Limiting**: 10 uploads per minute

---

## 🔒 Security Considerations

### File Upload Security

- **File Type Validation**: Only specific file types are allowed
- **File Size Limits**: Maximum 100MB per file
- **Virus Scanning**: Implement antivirus scanning for uploaded files
- **Content Validation**: Validate file contents match file extensions

### API Security

- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Protection**: Using parameterized queries
- **XSS Protection**: Proper output encoding
- **CSRF Protection**: Implement CSRF tokens for state-changing operations

---

## 🧪 Testing the API

### Using curl

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test file upload
curl -X POST "http://localhost:8000/api/v1/evidence/upload/" \
  -F "file=@test.pdf" \
  -F "case_id=test_case"

# Test evidence retrieval
curl http://localhost:8000/api/v1/evidence/1
```

### Using Python requests

```python
import requests

# Upload file
with open('evidence.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/evidence/upload/',
        files={'file': f},
        data={'case_id': 'case_001', 'description': 'Test evidence'}
    )
print(response.json())

# Get evidence
response = requests.get('http://localhost:8000/api/v1/evidence/1')
print(response.json())
```

### Using JavaScript/fetch

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('case_id', 'case_001');

fetch('http://localhost:8000/api/v1/evidence/upload/', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// Get evidence
fetch('http://localhost:8000/api/v1/evidence/1')
.then(response => response.json())
.then(data => console.log(data));
```

---

## 📖 Interactive Documentation

The API provides interactive documentation through:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These interfaces allow you to:
- Explore all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Download OpenAPI specifications

---

**API Reference complete. Ready for integration and development.**

Next: [Deployment Guide](deployment.md)