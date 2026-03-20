from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.


class RegisterView(APIView):
    def post(self, request):
        return Response({"message": "success"})


class LoginView(APIView):
    def post(self, request):
        return Response({"message": "success"})
