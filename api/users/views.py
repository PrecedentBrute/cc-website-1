from rest_framework.response import Response
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import serializers, status,generics
from .serializers import VisitorSerializer,CustomUserSerializer
from .models import Visitor,CustomUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes,smart_str,force_bytes,force_str,DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import Util
from django.contrib.auth import login,authenticate,logout
from django.http import HttpResponsePermanentRedirect
import os


class VisitorRegistrationView(APIView):
    """
    Create a new Visitor
    """
    def get(self,request,format=None):
        visitors = Visitor.objects.all()
        serializer = VisitorSerializer(visitors, many=True)
        return Response(serializer.data)


    def post(self, request, format=None):
        request.data['is_visitor']=True
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            queryset = CustomUser.objects.filter(email=request.data['email'])
            if queryset.exists():
                return Response({'msg': 'User already exists'}, status=status.HTTP_406_NOT_ACCEPTABLE)
            serializer.save()
            user=CustomUser.objects.filter(email=request.data['email'])[0]
            Visitor.objects.create(user=user)
            return Response({'msg': 'User Created'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisitorUpdateView(APIView):
    """
    get_object fetches an instance, put method to update it
    """
    # Could not make get_object return properly so temporarily shifted that part inside put method

    def put(self, request, format=None):
        try:
            user=CustomUser.objects.get(email=request.data['email'])
            visitor=Visitor.objects.get(pk=user.id)
        except Visitor.DoesNotExist:
            return Response({'msg', 'User Not Found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = VisitorSerializer(visitor, data=request.data)
        if serializer.is_valid():
            # Update values here
            return Response({'msg': 'User Updated'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Login a user (any type)
    """
    def post(self, request, format=None):
        data = request.data
        username = data['email']
        password = data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response({'msg':'Provided Credentials do not match'})

class LogoutView(APIView):
    """
    Logout a user
    """
    def get(self,request,format=None):
        logout(request)
        return Response({'msg':'Logged Out'},status=status.HTTP_200_OK)


class RequestPasswordResetEmail(APIView):
    """
    Views to request a password reset email, generates a token
    """
    def post(self, request):
   
        email = request.data['email']

        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(
                request=request).domain
            relativeLink = reverse(
                'PasswordReset', kwargs={'uidb64': uidb64, 'token': token})

            absurl = 'http://'+current_site + relativeLink
            email_body = 'Hello, \nUse link below to reset your password  \n' + \
                absurl
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your passsword'}
            Util.send_email(data)
        return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)


class PasswordTokenCheck(APIView):
    """
    Class to check the validity of the generated tokens with user, 
    the link is generated and sent to mail to access this view
    """
    def get(self, request, *args,**kwargs):
        token = kwargs['token']
        uidb64= kwargs['uidb64']

        try:
            id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)
            print(user)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'msg': 'Invalid Token'}, status=status.HTTP_401_UNAUTHORIZED)


            return Response({'msg': 'Valid Token', 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)
           
        except DjangoUnicodeDecodeError as identifier:
            if not PasswordResetTokenGenerator().check_token(user):
                return Response({'msg': 'Invalid Token'}, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordView(APIView):
    """
    View to set the new password after validity checks
    """
    def put(self, request):
        try:
            password=request.data['password']
            uidb64=request.data['uidb64']
            token=request.data['token']
            id=force_str(urlsafe_base64_decode(uidb64))
            user=CustomUser.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'msg':'Error'},status=status.HTTP_401_UNAUTHORIZED)

            user.password=password
            user.save()
            return (user)
        except:
            return Response({'msg': 'Error'}, status=status.HTTP_401_UNAUTHORIZED)
            
# Member Views  ----- Sanyam
