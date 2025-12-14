# SEED Backend API Documentation

This document describes the available API endpoints in the SEED backend system.

## Base URLs
- Authentication routes are prefixed with `/auth`
- Chatbot routes are prefixed with `/chatbot`

## Authentication Routes

### 1. Health Check
**Endpoint:** `GET /auth/`

**Description:** Returns the API status and service information.

**Input:** None

**Response:**
```json
{
    "status": "ok",
    "message": "API is running",
    "service": "noteswriter-backend"
}
```

**Status Code:** `200 OK`

---

### 2. User Signup (Send OTP)
**Endpoint:** `POST /auth/signup`

**Description:** Initiates user signup process by sending an OTP to the provided email address.

**Headers:**
- `Content-Type: application/json`

**Input:**
```json
{
    "email": "user@example.com",
    "password": "user_password"
}
```

**Success Response (OTP Sent):**
```json
{
    "status": "ok",
    "otpSent": true,
    "email": "user@example.com"
}
```
**Status Code:** `200 OK`

**Success Response (OTP Already Exists):**
```json
{
    "status": "exists",
    "otpSent": false,
    "timeLeft": 750,
    "email": "user@example.com"
}
```
**Status Code:** `200 OK`

**Error Responses:**
- **Missing Email:**
  ```json
  {
      "error": "Email is required"
  }
  ```
  **Status Code:** `400 Bad Request`

- **Invalid Content Type:**
  ```json
  {
      "error": "Content-Type must be application/json"
  }
  ```
  **Status Code:** `400 Bad Request`

- **Email Send Failure:**
  ```json
  {
      "error": "Failed to send email",
      "details": "Error details..."
  }
  ```
  **Status Code:** `500 Internal Server Error`

---

### 3. Verify OTP and Create Account
**Endpoint:** `POST /auth/verify_otp`

**Description:** Verifies the OTP sent to user's email and creates a new user account.

**Headers:**
- `Content-Type: application/json`

**Input:**
```json
{
    "email": "user@example.com",
    "otp": "123456",
    "password": "user_password"
}
```

**Success Response:**
```json
{
    "status": "verified",
    "verified": true,
    "message": "OTP verified and user created"
}
```
**Status Code:** `200 OK`

**Error Responses:**
- **Missing Required Fields:**
  ```json
  {
      "error": "Email, OTP and password are required"
  }
  ```
  **Status Code:** `400 Bad Request`

- **OTP Not Found/Expired:**
  ```json
  {
      "status": "not_found",
      "verified": false,
      "message": "OTP does not exist or has expired"
  }
  ```
  **Status Code:** `400 Bad Request`

- **Invalid OTP:**
  ```json
  {
      "status": "invalid",
      "verified": false,
      "message": "Invalid OTP"
  }
  ```
  **Status Code:** `400 Bad Request`

- **Database Error:**
  ```json
  {
      "status": "db_error",
      "verified": true,
      "message": "OTP verified but failed to create user",
      "details": "Error details..."
  }
  ```
  **Status Code:** `500 Internal Server Error`

- **Invalid Content Type:**
  ```json
  {
      "error": "Content-Type must be application/json"
  }
  ```
  **Status Code:** `400 Bad Request`

---

### 4. User Sign In
**Endpoint:** `POST /auth/signin`

**Description:** Authenticates user with email and password.

**Headers:**
- `Content-Type: application/json`

**Input:**
```json
{
    "email": "user@example.com",
    "password": "user_password"
}
```

**Success Response (Valid Credentials):**
```json
{
    "success": true
}
```
**Status Code:** `200 OK`

**Success Response (Invalid Credentials or User Not Found):**
```json
{
    "success": false
}
```
**Status Code:** `200 OK`

**Error Responses:**
- **Missing Required Fields:**
  ```json
  {
      "error": "Email and password are required"
  }
  ```
  **Status Code:** `400 Bad Request`

- **Database Error:**
  ```json
  {
      "error": "Database error",
      "details": "Error details..."
  }
  ```
  **Status Code:** `500 Internal Server Error`

- **Invalid Content Type:**
  ```json
  {
      "error": "Content-Type must be application/json"
  }
  ```
  **Status Code:** `400 Bad Request`

---

## Chatbot Routes

### 1. Chatbot Health Check
**Endpoint:** `GET /chatbot/`

**Description:** Returns the chatbot service health status.

**Input:** None

**Response:**
```json
{
    "status": "healthy"
}
```

**Status Code:** `200 OK`

---

### 2. Chat with AI
**Endpoint:** `POST /chatbot/chat`

**Description:** Sends a message to Gemini 2.5 Flash AI model and returns the response.

**Headers:**
- `Content-Type: application/json`

**Input:**
```json
{
    "message": "Hello, how are you?"
}
```

**Success Response:**
```json
{
    "response": "Hello! I'm doing well, thank you for asking. How can I help you today?"
}
```
**Status Code:** `200 OK`

**Error Responses:**
- **Missing Message:**
  ```json
  {
      "error": "Missing 'message' in request body"
  }
  ```
  **Status Code:** `400 Bad Request`

- **API Error:**
  ```json
  {
      "error": "Error details..."
  }
  ```
  **Status Code:** `500 Internal Server Error`

---

## Notes

1. **OTP Expiry:** OTPs are valid for 15 minutes (900 seconds)
2. **Password Handling:** All passwords should be hashed on the client side before sending to the server
3. **CORS:** All routes support cross-origin requests
4. **Email Service:** Uses Gmail API for sending OTP emails
5. **Database:** Uses Supabase for user data storage
6. **Cache:** Uses Redis for OTP storage and caching
7. **AI Model:** Uses Google's Gemini 2.5 Flash for chat responses