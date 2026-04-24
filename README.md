# Credit Approval System

A Django REST API that evaluates loan eligibility based on credit scoring derived from historical customer and loan data. Built as a backend-only service with no frontend requirement.

## Tech Stack

- **Django 5** + **Django REST Framework** — API layer
- **PostgreSQL** — primary database
- **Celery** + **Redis** — background workers for data ingestion
- **Docker** + **Docker Compose** — containerized deployment

## Project Structure

```
CreditApproval/              ← repo root
├── CreditApproval/          # Project config (settings, urls, celery)
├── credit_approval/         # Main application
│   ├── models.py            # Customer and Loan models
│   ├── serializers.py       # Request/response shapes
│   ├── services.py          # Credit scoring business logic
│   ├── tasks.py             # Celery background ingestion tasks
│   ├── views.py             # API endpoint handlers
│   └── urls.py              # App-level routing
├── .gitignore
├── Dockerfile
├── README.md
├── customer_data.xlsx        # Seed data — customers
├── docker-compose.yml
├── loan_data.xlsx            # Seed data — historical loans
└── requirements.txt
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Run the Application

```bash
docker compose up --build -d
```

This single command will:

1. Build the Django application image
2. Start PostgreSQL and Redis containers
3. Run database migrations automatically
4. Start the Celery worker
5. Ingest `customer_data.xlsx` and `loan_data.xlsx` into the database in the background
6. Start the Django development server on port `4000`

The API will be available at `http://localhost:4000`.

### Database Admin (Adminer)

Visit `http://localhost:8080` to inspect the database.

```
System:   PostgreSQL
Server:   db
Username: postgres
Password: postgres
Database: postgres
```

## API Endpoints

### `POST /register`

Register a new customer. Approved credit limit is calculated automatically as `36 × monthly_income` rounded to the nearest lakh.

**Request:**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": "9876543210"
}
```

**Response:**

```json
{
  "customer_id": 1,
  "name": "John Doe",
  "age": 30,
  "monthly_income": 50000,
  "approved_limit": 1800000,
  "phone_number": "9876543210"
}
```

---

### `POST /check-eligibility`

Check loan eligibility based on a credit score calculated from historical loan data.

**Request:**

```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 12.5,
  "tenure": 12
}
```

**Response:**

```json
{
  "customer_id": 1,
  "approval": true,
  "interest_rate": 12.5,
  "corrected_interest_rate": 12.5,
  "tenure": 12,
  "monthly_installment": 9456.0
}
```

---

### `POST /create-loan`

Process a new loan based on eligibility. Returns `loan_approved: false` with a message if not eligible.

**Request:**

```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 12.5,
  "tenure": 12
}
```

**Response:**

```json
{
  "loan_id": 101,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved",
  "monthly_installment": 9456.0
}
```

---

### `GET /view-loan/<loan_id>`

View details of a specific loan along with customer information.

**Response:**

```json
{
  "loan_id": 101,
  "customer": {
    "customer_id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "9876543210",
    "age": 30
  },
  "loan_amount": 100000.0,
  "interest_rate": 12.5,
  "monthly_installment": 9456.0,
  "tenure": 12
}
```

---

### `GET /view-loans/<customer_id>`

View all active loans for a specific customer.

**Response:**

```json
[
  {
    "loan_id": 101,
    "loan_amount": 100000.0,
    "interest_rate": 12.5,
    "monthly_installment": 9456.0,
    "repayments_left": 10
  }
]
```

---

## Credit Scoring Logic

Credit scores are calculated out of 100 based on the following components from historical loan data:

- Past loans paid on time
- Number of loans taken in the past
- Loan activity in the current year
- Total loan approved volume

Loan approval thresholds based on credit score:

| Credit Score | Decision                          |
| ------------ | --------------------------------- |
| > 50         | Approved                          |
| 30 – 50      | Approved with interest rate > 12% |
| 10 – 30      | Approved with interest rate > 16% |
| < 10         | Rejected                          |

Additional rules:

- If total current EMIs exceed 50% of monthly salary — rejected
- If total current loan volume exceeds approved limit — credit score set to 0

## Running Tests

Unit tests cover all 5 endpoints including success cases, validation, rejection logic, and response shapes.

To run the test suite locally:

```bash
python manage.py test credit_approval
```

## Stopping the Application

```bash
docker compose down -v
```

The `-v` flag removes the volumes as well, wiping the database. If you want to stop the containers but keep the data intact:

```bash
docker compose down
```

## Background Workers

On startup, Celery automatically ingests the provided Excel files into the database using background tasks — the server starts immediately without waiting for ingestion to complete.
