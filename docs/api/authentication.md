# Authentication API

## Overview
FILEBOSS uses JWT (JSON Web Tokens) for authentication. All API endpoints (except `/auth/login` and `/health`) require a valid JWT token in the `Authorization` header.

## Base URL
```
https://api.fileboss.example.com/v1
```

## Authentication Flow

1. User submits credentials to `/auth/login`
2. Server validates credentials and returns a JWT token
3. Client includes the token in subsequent requests in the `Authorization` header
4. Server validates the token for each request

## Endpoints

### Login

**POST** `/auth/login`

Authenticates a user and returns a JWT token.

#### Request
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "securepassword123"
}
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "attorney",
    "is_active": true
  }
}
```

#### Error Responses
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account is disabled

### Refresh Token

**POST** `/auth/refresh`

Refreshes an expired access token using a refresh token.

#### Request
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "new.jwt.token.here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Logout

**POST** `/auth/logout`

Invalidates the current access token.

#### Request
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

#### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "message": "Successfully logged out"
}
```

## Authentication Headers

All authenticated requests must include the following header:

```
Authorization: Bearer <access_token>
```

## Token Expiration and Renewal

- Access tokens are valid for 1 hour
- Refresh tokens are valid for 7 days
- Clients should handle 401 responses by attempting to refresh the token

## Rate Limiting

- 100 requests per minute per IP for unauthenticated endpoints
- 1000 requests per minute per user for authenticated endpoints
- Response headers include rate limit information:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in window
  - `X-RateLimit-Reset`: Time when limit resets (UTC epoch seconds)

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field_name": ["Error details"]
    }
  }
}
```

## Security Considerations

- Always use HTTPS
- Store tokens securely (httpOnly cookies recommended for web)
- Implement proper token expiration and refresh logic
- Rotate refresh tokens on use
- Implement proper CORS policies
