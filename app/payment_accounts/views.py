import json

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .serializers import CreatePaymentSerializer
from .services.create_payment import create_payment
from .services.payment_acceptance import payment_acceptance


class CreatePaymentView(CreateAPIView):
    serializer_class = CreatePaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = CreatePaymentSerializer(data=request.POST)

        if serializer.is_valid():
            serialized_data = serializer.validated_data
        else:
            return Response(400)

        confirmation_url = create_payment(serialized_data)

        return Response({'confirmation_url': confirmation_url}, 200)


class CreatePaymentAcceptanceView(CreateAPIView):

    def post(self, request, *args, **kwargs):
        response = json.loads(request.body)

        if payment_acceptance(response):
            return Response(200)
        return Response(404)


# from django.shortcuts import render
# # mypaymentapp/views.py
# from django.shortcuts import get_object_or_404, redirect
# from django.template.response import TemplateResponse
# from payments import get_payment_model, RedirectNeeded
#
#
# def payment_details(request, payment_id):
#     payment = get_object_or_404(get_payment_model(), id=payment_id)
#
#     try:
#         form = payment.get_form(data=request.POST or None)
#     except RedirectNeeded as redirect_to:
#         return redirect(str(redirect_to))
#
#     return TemplateResponse(
#         request,
#         'payment.html',
#         {'form': form, 'payment': payment}
#     )
