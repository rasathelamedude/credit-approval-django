from rest_framework.test import APITestCase
from rest_framework import status
from .models import Customer, Loan
from datetime import date
from dateutil.relativedelta import relativedelta


# Create your tests here.


# Helper function for creating test data
def create_customer(**kwargs):
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "age": 30,
        "phone_number": "9876543210",
        "monthly_salary": 50000,
        "approved_limit": 1800000,
        "current_debt": 0,
    }

    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


# Helper function for creating test data
def create_loan(customer, **kwargs):
    defaults = {
        "customer": customer,
        "loan_amount": 100000,
        "interest_rate": 15,
        "monthly_repayment": 9000,
        "tenure": 12,
        "emis_paid_on_time": 10,
        "start_date": date.today() - relativedelta(months=6),
        "end_date": date.today() + relativedelta(months=6),
    }

    defaults.update(kwargs)
    return Loan.objects.create(**defaults)


# Test cases for RegisterView
class RegisterViewTest(APITestCase):
    def test_register_customer_success(self):
        response = self.client.post(
            "/register",
            {
                "first_name": "John",
                "last_name": "Doe",
                "age": 25,
                "monthly_income": 50000,
                "phone_number": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "John Doe")
        self.assertEqual(float(response.data["approved_limit"]), 1800000.0)
        self.assertIn("customer_id", response.data)

    def test_register_customer_missing_fields(self):
        response = self.client.post(
            "/register",
            {"first_name": "John", "last_name": "Doe", "age": 30},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_customer_invalid_age(self):
        response = self.client.post(
            "/register",
            {
                "first_name": "John",
                "last_name": "Doe",
                "age": "not_an_int",
                "monthly_income": 50000,
                "phone_number": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_approved_limit_calculation(self):
        # 36 * 75000 = 2700000
        response = self.client.post(
            "/register",
            {
                "first_name": "John",
                "last_name": "Doe",
                "age": 28,
                "monthly_income": 75000,
                "phone_number": "9876543210",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data["approved_limit"]), 2700000.0)


class CheckEligibilityViewTest(APITestCase):
    def setUp(self):
        self.customer = create_customer()

    def test_eligibility_high_credit_score(self):
        # Create many loans that were paid on time
        for _ in range(10):
            create_loan(self.customer, emis_paid_on_time=22)

        response = self.client.post(
            "/check-eligibility",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 100000,
                "interest_rate": 15,
                "tenure": 12,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("approval", response.data)
        self.assertIn("corrected_interest_rate", response.data)
        self.assertIn("monthly_installment", response.data)

    def test_eligbility_rejected_when_debt_exceeds_limit(self):
        # current_debt > approved_limit
        self.customer.current_debt = 200000
        self.customer.approved_limit = 100000
        self.customer.save()

        response = self.client.post(
            "/check-eligibility",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 100000,
                "interest_rate": 15,
                "tenure": 12,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["approval"])

    def test_eligibility_customer_not_found(self):
        response = self.client.post(
            "/check-eligibility",
            {
                "customer_id": 9999,
                "loan_amount": 100000,
                "interest_rate": 15,
                "tenure": 12,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_eligibility_negative_loan_amount(self):
        response = self.client.post(
            "/check-eligibility",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": -100000,
                "interest_rate": 15,
                "tenure": 12,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_eligibility_corrected_interest_rate(self):
        # with a low range credit score of 10-30, interest rate must be >= 16%
        # sending 8% interest rate should return a corrected interest rate of 16%

        create_loan(
            self.customer,
            emis_paid_on_time=3,
            loan_amount=50000,
            monthly_repayment=100,
            start_date=date.today() - relativedelta(years=2),  # not current year
            end_date=date.today() + relativedelta(months=6),
        )

        response = self.client.post(
            "/check-eligibility",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 100000,
                "interest_rate": 8,
                "tenure": 12,
            },
            format="json",
        )

        # score: paid_on_time=3*2=6, loans=1*5=5, current_year=0, volume=1 → total ~12
        # score is in 10-30 range → corrected rate should be >= 16
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(float(response.data["corrected_interest_rate"]), 16.0)


class CreateLoanViewTest(APITestCase):
    def setUp(self):
        self.customer = create_customer()

    def test_create_loan_approved(self):
        # Create many loans that were paid on time
        for _ in range(10):
            create_loan(self.customer, emis_paid_on_time=12, monthly_repayment=100)

        response = self.client.post(
            "/create-loan",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 50000,
                "interest_rate": 15,
                "tenure": 12,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["loan_approved"])
        self.assertIsNotNone(response.data["loan_id"])
        self.assertIn("monthly_installment", response.data)

    def test_create_loan_rejected(self):
        # Try forcing rejection by current_debt > approved limit
        self.customer.current_debt = 200000
        self.customer.approved_limit = 100000
        self.customer.save()

        response = self.client.post(
            "/create-loan",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 100000,
                "interest_rate": 15,
                "tenure": 12,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["loan_approved"])
        self.assertIsNone(response.data["loan_id"])
        self.assertIn("message", response.data)

    def test_create_loan_with_missing_fields(self):
        response = self.client.post(
            "/create-loan",
            {
                "customer_id": self.customer.customer_id,
                "loan_amount": 100000,
                "interest_rate": 15,
                # missing tenure
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ViewLoanByIdViewTest(APITestCase):
    def setUp(self):
        self.customer = create_customer()
        self.loan = create_loan(self.customer)

    def test_view_loan_success(self):
        response = self.client.get(f"/view-loan/{self.loan.loan_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["loan_id"], self.loan.loan_id)
        self.assertIn("customer", response.data)
        self.assertEqual(
            response.data["customer"]["first_name"], self.customer.first_name
        )
        self.assertIn("loan_amount", response.data)
        self.assertIn("interest_rate", response.data)
        self.assertIn("monthly_installment", response.data)
        self.assertIn("tenure", response.data)

    def test_view_loan_not_found(self):
        response = self.client.get("/view-loan/9999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ViewLoansByCustomerIdViewTest(APITestCase):
    def setUp(self):
        self.customer = create_customer()
        self.loan1 = create_loan(self.customer)
        self.loan2 = create_loan(self.customer, loan_amount=200000)

    def test_view_loans_success(self):
        response = self.client.get(f"/view-loans/{self.customer.customer_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_view_loans_customer_not_found(self):
        response = self.client.get("/view-loans/9999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_view_loans_empty_for_new_customer(self):
        new_customer = create_customer(phone_number="1111111111")

        response = self.client.get(f"/view-loans/{new_customer.customer_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_view_loans_repayments_left_calculation(self):
        response = self.client.get(f"/view-loans/{self.customer.customer_id}")
        loan = response.data[0]

        # tenure=12, emis_paid_on_time=10, so repayments_left should be 2
        self.assertEqual(loan["repayments_left"], 2)
