#  Defining request/response formats

from rest_framework import serializers
from .models import Customer, Loan


# /register request
class RegisterRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    age = serializers.IntegerField()
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    phone_number = serializers.CharField(max_length=50)


# /register response
class RegisterResponseSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    monthly_income = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="monthly_salary"
    )

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "name",
            "age",
            "monthly_income",
            "approved_limit",
            "phone_number",
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# /check-elegibility request
class CheckEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


# /check-elegibility response
class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)


# /create-loan request
class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


# /create-loan response
class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)


# Nested customer details inside loan details
class NestedCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["customer_id", "first_name", "last_name", "phone_number", "age"]


#  /view-loan/loan_id response
class ViewLoanByIdResponseSerializer(serializers.ModelSerializer):
    customer = NestedCustomerSerializer()
    monthly_installment = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="monthly_repayment"
    )

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "customer",
            "loan_amount",
            "interest_rate",
            "tenure",
            "monthly_installment",
        ]


# /view-loans/customer_id response
class ViewLoansResponseSerializer(serializers.ModelSerializer):
    monthly_installment = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="monthly_repayment"
    )
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "loan_amount",
            "interest_rate",
            "monthly_installment",
            "repayments_left",
        ]

    def get_repayments_left(self, obj):
        return obj.tenure - obj.emis_paid_on_time
