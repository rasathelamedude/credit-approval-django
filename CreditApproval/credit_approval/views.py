from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import (
    RegisterRequestSerializer,
    RegisterResponseSerializer,
    CheckEligibilityRequestSerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    ViewLoanByIdResponseSerializer,
    ViewLoansByCustomerIdResponseSerializer,
)
from .services import check_elegibility
from datetime import date
from dateutil.relativedelta import relativedelta


# Create your views here. (controllers)


# POST /register
class RegisterView(APIView):
    def post(self, request):
        # 1. validate the request using serializer
        request_serializer = RegisterRequestSerializer(data=request.data)

        if not request_serializer.is_valid():
            return Response(
                {"message": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request_serializer.validated_data

        # 2. Calculate approved limit
        approved_limit = round(36 * data["monthly_income"] / 100000) * 100000

        # 3. save the new customer in the database
        customer = Customer.objects.create(
            first_name=data["first_name"],
            last_name=data["last_name"],
            age=data["age"],
            phone_number=data["phone_number"],
            monthly_salary=data["monthly_income"],
            approved_limit=approved_limit,
            current_debt=0,
        )

        # 4. send the response
        response_serializer = RegisterResponseSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# POST /check-elegibility
class CheckEligibilityView(APIView):
    def post(self, request):
        # 1. validate the request using serializer
        request_serializer = CheckEligibilityRequestSerializer(data=request.data)

        if not request_serializer.is_valid():
            return Response(
                {"message": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 2. check the eligibility using service methods
        result = check_elegibility(request_serializer.validated_data)

        # 3. send the response
        response_serializer = CheckEligibilityResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# POST /create-loan
class CreateLoanView(APIView):
    # POST /create-loan
    def post(self, request):
        # 1. validate the request using serializer
        request_serializer = CreateLoanRequestSerializer(data=request.data)

        if not request_serializer.is_valid():
            return Response(
                {"message": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )

        data = request_serializer.validated_data

        # 2. Check eligibility of the customer
        eligibility_result = check_elegibility(data)

        if not eligibility_result["approval"]:
            response_serializer = CreateLoanResponseSerializer(
                {
                    "loan_id": None,
                    "customer_id": data["customer_id"],
                    "loan_approved": False,
                    "message": "Loan not approved based on credit score",
                    "monthly_installment": eligibility_result["monthly_installment"],
                }
            )
            return Response(
                response_serializer.data, status=status.HTTP_400_BAD_REQUEST
            )

        # 3. get the customer's id who applied for the job, start date and end date
        customer = Customer.objects.get(pk=data["customer_id"])
        start_date = date.today()
        end_date = start_date + relativedelta(months=int(data["tenure"]))

        # save the new loan in the database
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=data["loan_amount"],
            interest_rate=eligibility_result["corrected_interest_rate"],
            monthly_repayment=eligibility_result["monthly_installment"],
            tenure=data["tenure"],
            emis_paid_on_time=0,
            start_date=start_date,
            end_date=end_date,
        )

        # 4. send the response
        response_serializer = CreateLoanResponseSerializer(
            {
                "loan_id": loan.loan_id,
                "customer_id": customer.customer_id,
                "loan_approved": True,
                "message": "Loan approved",
                "monthly_installment": eligibility_result["monthly_installment"],
            }
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# GET /view-loan/{loan_id}
class ViewLoanByIdView(APIView):
    def get(self, request, loan_id):
        # 1. Try to get the loan
        try:
            loan = Loan.objects.select_related("customer").get(pk=loan_id)
        except Loan.DoesNotExist:
            return Response(
                {"message": "Loan not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # 2. send the response
        response_serializer = ViewLoanByIdResponseSerializer(loan)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# GET /view-loans/{customer_id}
class ViewLoansByCustomerIdView(APIView):
    def get(self, request, customer_id):
        # 1. Try to get the customer
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # 2. Get the loans for the found customer
        loans = Loan.objects.filter(customer=customer)

        # 3. send the response
        response_serializer = ViewLoansByCustomerIdResponseSerializer(loans, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
