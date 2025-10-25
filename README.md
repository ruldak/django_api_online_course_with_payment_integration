# Online Course Platform API Project

This project is an API backend for an online course platform built with Django and Django Rest Framework. The API provides functionality for user management, a course catalog, a shopping cart system, enrollments, and payment integration.

This project is specifically designed to showcase modern backend development skills, with a focus on scalability, security, and maintainability.

## Showcased Skills & Features

### 1. RESTful API Development
- **Framework**: Built using **Django Rest Framework (DRF)**, the industry standard for creating robust APIs with Python.
- **Architecture**: Follows best practices by separating logic into multiple Django apps (`user`, `courses`, `payment`, `enrollments`) for high modularity.
- **Serializers**: Utilizes `ModelSerializer` for efficient data conversion and secure input validation.
- **Views & ViewSets**: Implements `APIView` and `ViewSet` to handle business logic and HTTP requests.

### 2. Database Design & ORM
- **Relational Schema**: A well-structured database design to manage complex relationships between Users, Courses, Lessons, Categories, Carts, and Transactions.
    - `User` (Django default) ↔ `Course` (One-to-Many, as instructor)
    - `Course` ↔ `Lesson` (One-to-Many)
    - `User` ↔ `Cart` (One-to-One)
    - `Cart` ↔ `CartItem` ↔ `Course` (Shopping cart system)
    - `User` ↔ `Enrollment` ↔ `PaymentTransaction` ↔ `Course` (Enrollment relationship after successful payment)
- **Django ORM**: Full utilization of the Django ORM for safe and efficient database queries, preventing SQL Injection vulnerabilities.

### 3. Authentication & Security
- **JSON Web Tokens (JWT)**: Implemented token-based authentication using `djangorestframework-simplejwt` for secure and stateless endpoints.
- **Permissions**: Use of DRF's permission system to control access, for example, distinguishing between regular users and instructors.

### 4. Payment Gateway Integration
- **Multi-Gateway**: Integrated with two leading payment providers:
    - **PayPal**: Implemented the "Create Order" and "Capture Order" flow using the PayPal REST API.
    - **Stripe**: Implemented the secure `Checkout Session` flow and handling of payment status notifications via **Stripe Webhooks**.
- **Transactions**: A flexible `PaymentTransaction` model to record every transaction, its status (`pending`, `success`, `failed`), and the originating payment gateway.

### 5. Automated API Documentation
- **OpenAPI 3.0**: Integrated with `drf-spectacular` to automatically generate an OpenAPI 3.0 schema from the codebase.
- **Interactive UI**: The API documentation is accessible via a user-friendly UI:
    - **Swagger UI**: `/api/docs/`
    - **Redoc**: `/api/redoc/`
  This allows frontend developers or other API consumers to easily understand and test every endpoint.

### 6. Advanced Features
- **Filtering**: Use of `django-filter` to provide powerful filtering capabilities on list endpoints (e.g., searching for courses by category).
- **Custom Logic**: Implementation of custom logic such as total price calculation within the cart (`Cart.get_total_price`).

## Technology Stack
- **Backend**: Python, Django, Django Rest Framework
- **Database**: MySQL (configured, but can be swapped with any Django-supported database)
- **Authentication**: djangorestframework-simplejwt
- **API Documentation**: drf-spectacular
- **Payment Integration**: PayPal REST API, Stripe API
- **Others**: python-decouple (for environment variable management)

## Setup & Installation
1.  **Clone the repository**
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables** (create a `.env` file).
5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```
6.  **Run the server:**
    ```bash
    python manage.py runserver
    ```