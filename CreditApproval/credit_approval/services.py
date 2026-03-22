# Credit score logic (helper function and business logic)

from django.utils import timezone
from .models import Customer, Loan
from decimal import Decimal


def check_elegibility(data):
    customer = Customer.objects.get(customer_id=data["customer_id"])

    credit_score = calculate_credit_score(customer)

    emi_sum = calculate_current_emis(customer)

    approval, corrected_rate = apply_rules(
        credit_score, data["interest_rate"], emi_sum, customer, data["loan_amount"]
    )

    monthly_installment = calculate_emi(
        data["loan_amount"], corrected_rate, data["tenure"]
    )

    return {
        "customer_id": customer.customer_id,
        "approval": approval,
        "interest_rate": data["interest_rate"],
        "corrected_interest_rate": corrected_rate,
        "tenure": data["tenure"],
        "monthly_installment": monthly_installment,
    }


def calculate_credit_score(customer):
    # Get loans for customer
    loans = Loan.objects.filter(customer=customer)

    total_loans = loans.count()

    paid_on_time = sum(loan.emis_paid_on_time for loan in loans)

    current_year_loans = loans.filter(start_date__year=timezone.now().year).count()

    total_loan_volume = sum(loan.loan_amount for loan in loans)

    score = 0

    score += min(paid_on_time * 2, 40)
    score += min(total_loans * 5, 20)
    score += min(current_year_loans * 10, 20)
    score += min(float(total_loan_volume) / 100000, 20)

    if customer.current_debt > customer.approved_limit:
        return 0

    return min(score, 100)


def calculate_emi(principal, interest_rate, tenure):
    r = Decimal(interest_rate) / 12 / 100
    n = Decimal(tenure)

    if r == 0:
        return principal / n

    emi = (principal * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return emi


def calculate_current_emis(customer):
    loans = Loan.objects.filter(customer=customer)

    today = timezone.now().date()

    active_loans = loans.filter(end_date__gte=today)

    return sum(loan.monthly_repayment for loan in active_loans)


def apply_rules(credit_score, interest_rate, emi_sum, customer, loan_amount):
    approved = False
    corrected_interest_rate = interest_rate

    # EMI rule
    if emi_sum > Decimal(0.5) * customer.monthly_salary:
        return approved, corrected_interest_rate

    # Credit score rules
    if credit_score > 50:
        approved = True
    elif 30 < credit_score <= 50:
        approved = interest_rate > 12
    elif 10 < credit_score <= 30:
        approved = interest_rate > 16
    else:
        approved = False

    # Interest correction
    if credit_score > 50:
        corrected_interest_rate = interest_rate
    elif 30 < credit_score <= 50:
        corrected_interest_rate = max(interest_rate, 12)
    elif 10 < credit_score <= 30:
        corrected_interest_rate = max(interest_rate, 16)

    return approved, corrected_interest_rate
