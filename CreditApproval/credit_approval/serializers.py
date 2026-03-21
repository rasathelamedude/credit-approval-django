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


"""
Check loan eligibility based on credit score of  customer (out of 
100 ) based on the historical loan data from “loan_data.xlsx”, 
consider the following components while assigning a credit 
score: 
i. Past Loans paid on time  
ii. No of loans taken in past  
iii. Loan activity in current year  
iv. Loan approved volume 
v. If sum of current loans of customer > approved limit of 
customer , credit score = 0 
Based on the credit score of the customer , approve loans as 
per the following: 
▪ If credit_rating > 50 , approve loan 
▪ If 50 > credit_rating > 30 , approve loans with 
interest rate > 12% 
▪ If 30> credit_rating > 10 , approve loans with interest 
rate >16% 
▪ If 10> credit_rating , don’t approve any loans 
▪ If sum of all current EMIs > 50% of monthly salary , 
don’t approve any loans  
▪ If the interest rate does not match as per credit 
limit , correct the interest rate in the response, i.e 
suppose credit_limit is calculated to be 20 for a 
 
particular loan and the interest_rate is 8%, send a 
corrected_interest_rate = 16% (lowest of slab) in 
response

"""


# /check-elegibility request
class CheckEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()

    def validate_loan_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Loan amount cannot be negative")
        return value

    def validate_interest_rate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Interest rate cannot be negative")
        return value

    def validate_tenure(self, value):
        if value < 0:
            raise serializers.ValidationError("Tenure cannot be negative")
        return value

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError("Customer does not exist")
        return value

    def validate(self, attrs):
        return attrs


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
