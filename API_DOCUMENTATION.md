# DawakSahl API Documentation

## Overview

The DawakSahl API is a comprehensive RESTful API for a pharmacy platform that supports multiple user types (patients, pharmacies, doctors) with full multilingual support (Arabic/English).

## Base URL

- **Development**: `http://localhost:5000/api/v1`
- **Production**: `https://your-app.onrender.com/api/v1`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Success message in English",
  "message_ar": "رسالة النجاح بالعربية",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message in English",
  "message_ar": "رسالة الخطأ بالعربية",
  "errors": {
    // Validation errors (optional)
  }
}
```

## Language Support

The API supports both Arabic and English. Include the `Accept-Language` header to specify your preferred language:

```
Accept-Language: ar  // For Arabic
Accept-Language: en  // For English (default)
```

## Rate Limiting

- **Default**: 1000 requests per hour
- **Authentication endpoints**: 10 requests per minute, 50 per hour
- **File uploads**: 20 requests per hour

## Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

### Pagination Response
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "per_page": 20,
    "pages": 8,
    "has_prev": false,
    "has_next": true
  }
}
```

---

## Authentication Endpoints

### Register User
**POST** `/auth/register`

Register a new user (patient, pharmacy, or doctor).

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "confirm_password": "securepassword123",
  "user_type": "patient",
  "first_name": "Ahmed",
  "last_name": "Ali",
  "phone": "0501234567",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "country": "SA",
  "city": "Riyadh",
  "district": "Al Malaz",
  "street": "King Fahd Road",
  "building_number": "123",
  "postal_code": "12345"
}
```

#### Response
```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "message_ar": "تم التسجيل بنجاح. يرجى التحقق من بريدك الإلكتروني.",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "user_type": "patient",
      "is_email_verified": false
    }
  }
}
```

### Login
**POST** `/auth/login`

Authenticate user and receive JWT tokens.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "remember_me": false
}
```

#### Response
```json
{
  "success": true,
  "message": "Login successful",
  "message_ar": "تم تسجيل الدخول بنجاح",
  "data": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "user_type": "patient",
      "first_name": "Ahmed",
      "last_name": "Ali"
    }
  }
}
```

### Verify Email
**POST** `/auth/verify-email`

Verify user's email address using verification token.

#### Request Body
```json
{
  "token": "verification-token"
}
```

### Forgot Password
**POST** `/auth/forgot-password`

Request password reset email.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

### Reset Password
**POST** `/auth/reset-password`

Reset password using reset token.

#### Request Body
```json
{
  "token": "reset-token",
  "password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

### Refresh Token
**POST** `/auth/refresh-token`

Get new access token using refresh token.

#### Headers
```
Authorization: Bearer <refresh-token>
```

### Logout
**POST** `/auth/logout`

Logout user and invalidate tokens.

#### Headers
```
Authorization: Bearer <access-token>
```

### Change Password
**POST** `/auth/change-password`

Change user's password (requires authentication).

#### Request Body
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

---

## User Management Endpoints

### Get User Profile
**GET** `/users/profile`

Get current user's profile information.

#### Headers
```
Authorization: Bearer <access-token>
```

#### Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "user_type": "patient",
      "first_name": "Ahmed",
      "last_name": "Ali",
      "phone": "0501234567",
      "date_of_birth": "1990-01-01",
      "gender": "male",
      "avatar_url": null,
      "is_email_verified": true,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "addresses": [...],
      "medical_info": {...}
    }
  }
}
```

### Update User Profile
**PUT** `/users/profile`

Update current user's profile information.

#### Request Body
```json
{
  "first_name": "Ahmed",
  "last_name": "Ali",
  "phone": "0501234567",
  "date_of_birth": "1990-01-01",
  "gender": "male"
}
```

### Upload Avatar
**POST** `/users/upload-avatar`

Upload user avatar image.

#### Request
- **Content-Type**: `multipart/form-data`
- **File field**: `avatar`
- **Allowed formats**: PNG, JPG, JPEG
- **Max size**: 16MB

### Get User Addresses
**GET** `/users/addresses`

Get user's saved addresses.

#### Response
```json
{
  "success": true,
  "data": {
    "addresses": [
      {
        "id": "uuid",
        "country": "SA",
        "city": "Riyadh",
        "district": "Al Malaz",
        "street": "King Fahd Road",
        "building_number": "123",
        "postal_code": "12345",
        "address_type": "home",
        "is_default": true
      }
    ]
  }
}
```

### Add Address
**POST** `/users/addresses`

Add new address for user.

#### Request Body
```json
{
  "country": "SA",
  "city": "Riyadh",
  "district": "Al Malaz",
  "street": "King Fahd Road",
  "building_number": "123",
  "postal_code": "12345",
  "address_type": "home",
  "is_default": false
}
```

### Update Address
**PUT** `/users/addresses/{address_id}`

Update existing address.

### Delete Address
**DELETE** `/users/addresses/{address_id}`

Delete address.

---

## Medication Endpoints

### List Medications
**GET** `/medications`

Get list of medications with search and filtering.

#### Query Parameters
- `search`: Search term for medication name
- `category_id`: Filter by category
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "Paracetamol",
        "name_ar": "باراسيتامول",
        "generic_name": "Acetaminophen",
        "brand_name": "Tylenol",
        "strength": "500mg",
        "form": "tablet",
        "category": {
          "id": "uuid",
          "name": "Pain Relief",
          "name_ar": "مسكنات الألم"
        },
        "description": "Pain reliever and fever reducer",
        "description_ar": "مسكن للألم وخافض للحرارة",
        "side_effects": [...],
        "contraindications": [...],
        "price_range": {
          "min": 10.00,
          "max": 25.00
        }
      }
    ],
    "total": 150,
    "page": 1,
    "per_page": 20
  }
}
```

### Get Medication Details
**GET** `/medications/{medication_id}`

Get detailed information about a specific medication.

### Get Medication Categories
**GET** `/medications/categories`

Get list of medication categories.

#### Response
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "uuid",
        "name": "Pain Relief",
        "name_ar": "مسكنات الألم",
        "description": "Medications for pain management",
        "description_ar": "أدوية لإدارة الألم",
        "parent_id": null,
        "subcategories": [...]
      }
    ]
  }
}
```

---

## Pharmacy Endpoints

### List Pharmacies
**GET** `/pharmacies`

Get list of pharmacies with search and filtering.

#### Query Parameters
- `search`: Search term for pharmacy name
- `city`: Filter by city
- `district`: Filter by district
- `latitude`: User latitude for distance calculation
- `longitude`: User longitude for distance calculation
- `radius`: Search radius in kilometers
- `is_open`: Filter by currently open pharmacies
- `services`: Filter by services (comma-separated)
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "pharmacy_name": "Al Dawaa Pharmacy",
        "pharmacy_name_ar": "صيدلية الدواء",
        "pharmacist_name": "Dr. Mohammed Ali",
        "phone": "0112345678",
        "email": "info@aldawaa.com",
        "address": "King Fahd Road, Al Malaz",
        "city": "Riyadh",
        "district": "Al Malaz",
        "latitude": 24.7136,
        "longitude": 46.6753,
        "distance": 2.5,
        "rating": 4.5,
        "total_reviews": 120,
        "is_verified": true,
        "is_open": true,
        "operating_hours": {
          "saturday": {"open": "08:00", "close": "22:00"},
          "sunday": {"open": "08:00", "close": "22:00"}
        },
        "services": ["delivery", "consultation", "insurance"]
      }
    ],
    "total": 50,
    "page": 1,
    "per_page": 20
  }
}
```

### Get Pharmacy Details
**GET** `/pharmacies/{pharmacy_id}`

Get detailed information about a specific pharmacy.

### Get Pharmacy Inventory
**GET** `/pharmacies/{pharmacy_id}/inventory`

Get pharmacy's medication inventory.

#### Query Parameters
- `search`: Search medications in inventory
- `category_id`: Filter by category
- `in_stock`: Filter by availability

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "medication": {
          "id": "uuid",
          "name": "Paracetamol",
          "name_ar": "باراسيتامول",
          "strength": "500mg",
          "form": "tablet"
        },
        "price": 15.50,
        "stock_quantity": 100,
        "is_available": true,
        "expiry_date": "2025-12-31",
        "batch_number": "BATCH123"
      }
    ]
  }
}
```

---

## Prescription Endpoints

### List User Prescriptions
**GET** `/prescriptions`

Get current user's prescriptions.

#### Query Parameters
- `status`: Filter by status (pending, verified, rejected, filled)
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "doctor_name": "Dr. Ahmed Hassan",
        "doctor_name_ar": "د. أحمد حسن",
        "hospital_clinic": "King Faisal Hospital",
        "prescription_date": "2024-01-15",
        "file_url": "/uploads/prescriptions/prescription_123.pdf",
        "file_name": "prescription.pdf",
        "status": "verified",
        "verification_notes": "Prescription verified successfully",
        "verified_at": "2024-01-16T10:30:00",
        "medications_extracted": [
          {
            "name": "Paracetamol",
            "strength": "500mg",
            "quantity": "20 tablets",
            "instructions": "Take 1 tablet every 6 hours"
          }
        ]
      }
    ]
  }
}
```

### Upload Prescription
**POST** `/prescriptions`

Upload a new prescription.

#### Request
- **Content-Type**: `multipart/form-data`
- **File field**: `prescription_file`
- **Allowed formats**: PNG, JPG, JPEG, PDF
- **Max size**: 16MB

#### Additional Fields
```json
{
  "doctor_name": "Dr. Ahmed Hassan",
  "doctor_name_ar": "د. أحمد حسن",
  "doctor_license": "DOC123456",
  "hospital_clinic": "King Faisal Hospital",
  "hospital_clinic_ar": "مستشفى الملك فيصل",
  "prescription_date": "2024-01-15"
}
```

### Get Prescription Details
**GET** `/prescriptions/{prescription_id}`

Get detailed information about a specific prescription.

### Verify Prescription (Pharmacy Only)
**PUT** `/prescriptions/{prescription_id}/verify`

Verify prescription (pharmacy users only).

#### Request Body
```json
{
  "status": "verified",
  "verification_notes": "Prescription verified successfully",
  "verification_notes_ar": "تم التحقق من الوصفة بنجاح",
  "medications_extracted": [
    {
      "name": "Paracetamol",
      "strength": "500mg",
      "quantity": "20 tablets",
      "instructions": "Take 1 tablet every 6 hours"
    }
  ]
}
```

---

## Order Endpoints

### List User Orders
**GET** `/orders`

Get current user's orders.

#### Query Parameters
- `status`: Filter by status
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "order_number": "DWK20240115123456ABC",
        "pharmacy": {
          "id": "uuid",
          "pharmacy_name": "Al Dawaa Pharmacy",
          "phone": "0112345678"
        },
        "prescription": {
          "id": "uuid",
          "doctor_name": "Dr. Ahmed Hassan"
        },
        "status": "confirmed",
        "total_amount": 125.50,
        "delivery_fee": 15.00,
        "delivery_address": {
          "street": "King Fahd Road",
          "city": "Riyadh",
          "district": "Al Malaz"
        },
        "estimated_delivery": "2024-01-16T14:00:00",
        "items": [
          {
            "medication": {
              "name": "Paracetamol",
              "strength": "500mg"
            },
            "quantity": 2,
            "unit_price": 15.50,
            "total_price": 31.00
          }
        ],
        "created_at": "2024-01-15T10:00:00"
      }
    ]
  }
}
```

### Create Order
**POST** `/orders`

Create a new order.

#### Request Body
```json
{
  "pharmacy_id": "uuid",
  "prescription_id": "uuid",
  "delivery_address_id": "uuid",
  "items": [
    {
      "pharmacy_inventory_id": "uuid",
      "quantity": 2
    }
  ],
  "notes": "Please deliver before 5 PM",
  "notes_ar": "يرجى التوصيل قبل الساعة 5 مساءً"
}
```

### Get Order Details
**GET** `/orders/{order_id}`

Get detailed information about a specific order.

### Update Order Status (Pharmacy Only)
**PUT** `/orders/{order_id}/status`

Update order status (pharmacy users only).

#### Request Body
```json
{
  "status": "preparing",
  "notes": "Order is being prepared",
  "notes_ar": "جاري تحضير الطلب",
  "estimated_delivery": "2024-01-16T14:00:00"
}
```

### Cancel Order
**POST** `/orders/{order_id}/cancel`

Cancel an order.

#### Request Body
```json
{
  "reason": "Changed my mind",
  "reason_ar": "غيرت رأيي"
}
```

---

## Chat Endpoints

### List Conversations
**GET** `/chat/conversations`

Get user's chat conversations.

#### Response
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "uuid",
        "pharmacy": {
          "id": "uuid",
          "pharmacy_name": "Al Dawaa Pharmacy"
        },
        "last_message": {
          "content": "Thank you for your order",
          "content_ar": "شكراً لك على طلبك",
          "sent_at": "2024-01-15T15:30:00",
          "sender_type": "pharmacy"
        },
        "unread_count": 2,
        "created_at": "2024-01-15T10:00:00"
      }
    ]
  }
}
```

### Start New Conversation
**POST** `/chat/conversations`

Start a new conversation with a pharmacy.

#### Request Body
```json
{
  "pharmacy_id": "uuid",
  "initial_message": "Hello, I have a question about my order",
  "initial_message_ar": "مرحباً، لدي سؤال حول طلبي"
}
```

### Get Conversation Messages
**GET** `/chat/conversations/{conversation_id}/messages`

Get messages in a conversation.

#### Query Parameters
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "content": "Hello, I have a question about my order",
        "content_ar": "مرحباً، لدي سؤال حول طلبي",
        "sender": {
          "id": "uuid",
          "first_name": "Ahmed",
          "user_type": "patient"
        },
        "message_type": "text",
        "is_read": true,
        "sent_at": "2024-01-15T15:00:00"
      }
    ]
  }
}
```

### Send Message
**POST** `/chat/conversations/{conversation_id}/messages`

Send a message in a conversation.

#### Request Body
```json
{
  "content": "Thank you for your help",
  "content_ar": "شكراً لك على مساعدتك",
  "message_type": "text"
}
```

---

## Notification Endpoints

### List Notifications
**GET** `/notifications`

Get user's notifications.

#### Query Parameters
- `is_read`: Filter by read status
- `type`: Filter by notification type
- `page`: Page number
- `per_page`: Items per page

#### Response
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "Order Confirmed",
        "title_ar": "تم تأكيد الطلب",
        "message": "Your order #DWK123 has been confirmed",
        "message_ar": "تم تأكيد طلبك رقم #DWK123",
        "type": "order_update",
        "is_read": false,
        "data": {
          "order_id": "uuid",
          "order_number": "DWK123"
        },
        "created_at": "2024-01-15T16:00:00"
      }
    ],
    "unread_count": 5
  }
}
```

### Mark Notification as Read
**PUT** `/notifications/{notification_id}/read`

Mark a specific notification as read.

### Mark All Notifications as Read
**PUT** `/notifications/read-all`

Mark all notifications as read.

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## Common Error Responses

### Validation Error (422)
```json
{
  "success": false,
  "message": "Validation failed",
  "message_ar": "فشل في التحقق من صحة البيانات",
  "errors": {
    "email": ["This field is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### Unauthorized (401)
```json
{
  "success": false,
  "message": "Authentication required",
  "message_ar": "المصادقة مطلوبة"
}
```

### Rate Limit Exceeded (429)
```json
{
  "success": false,
  "message": "Rate limit exceeded",
  "message_ar": "تم تجاوز حد المعدل"
}
```

---

## WebSocket Events (Future Implementation)

The API is designed to support real-time features through WebSocket connections:

- **Chat messages**: Real-time messaging
- **Order updates**: Live order status updates
- **Notifications**: Instant notifications

---

## SDK and Libraries

### JavaScript/TypeScript
```javascript
// Example usage with axios
const api = axios.create({
  baseURL: 'https://api.dawaksahl.com/api/v1',
  headers: {
    'Accept-Language': 'ar', // or 'en'
    'Authorization': 'Bearer ' + token
  }
});

// Login
const response = await api.post('/auth/login', {
  email: 'user@example.com',
  password: 'password123'
});
```

### Python
```python
import requests

# Example usage
api_base = 'https://api.dawaksahl.com/api/v1'
headers = {
    'Accept-Language': 'ar',  # or 'en'
    'Authorization': f'Bearer {token}'
}

# Login
response = requests.post(f'{api_base}/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
}, headers=headers)
```

---

## Testing

### Health Check
**GET** `/health`

Check API health status.

#### Response
```json
{
  "status": "healthy",
  "message": "DawakSahl API is running",
  "message_ar": "واجهة برمجة تطبيقات دواكسهل تعمل",
  "version": "1.0.0"
}
```

### API Info
**GET** `/api/v1/`

Get API information and available endpoints.

---

## Support

For API support and questions:
- **Email**: api-support@dawaksahl.com
- **Documentation**: https://docs.dawaksahl.com
- **Status Page**: https://status.dawaksahl.com

---

*Last updated: January 2024*

