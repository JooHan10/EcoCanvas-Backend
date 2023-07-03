from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegisterSerializer, PaymentScheduleSerializer, RegisterPaymentSerializer
from .models import RegisterPayment, Payment
from users.models import User
from rest_framework import status
from iamport import Iamport
from config import settings
import requests
from django.http import JsonResponse
from rest_framework.pagination import PageNumberPagination
from .cryption import CipherV1
from shop.models import ShopOrderDetail
import datetime

class ReceiptPagination(PageNumberPagination):
    '''
    작성자 : 송지명
    작성일 : 2023.06.24
    작성내용 : 페이지네이션
    업데이트 날짜 :
    '''  
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 60

class RegisterCustomerView(APIView):
    
    def post(self, request):
        '''
        작성자 : 송지명
        작성일 : 2023.06.08
        작성내용 : 유저의 카드 정보 등록.
        업데이트날짜 : 2023.06.30
        ''' 
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        '''
        작성자 : 송지명
        작성일 : 2023.06.13
        작성내용 : 유저의 카드정보 조회 
        업데이트날짜 : 
        '''
        register_payments = RegisterPayment.objects.filter(user=request.user)
        serializer = RegisterPaymentSerializer(register_payments, many=True)
        cipher = CipherV1()
        for payment in serializer.data:
            card_number = payment['card_number']
            decrypted_card = cipher.decrypt(card_number)
            show_card_number = f"{decrypted_card[:8]}****{decrypted_card[-4:]}"
            payment['card_number']= show_card_number            
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        
        card_id = request.data.get('id')
        register_payments = RegisterPayment.objects.get(user=request.user, id = card_id)
        if register_payments:           
            register_payments.delete()
            return Response({"message": "카드정보 삭제 성공"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "카드정보 없음"}, status=status.HTTP_404_NOT_FOUND)
        
        
    
        
class CreatePaymentScheduleView(APIView):
    def post(self, request, pk):
        '''
        작성자 : 송지명
        작성일 : 2023.06.08
        작성내용 : 캠페인 펀딩 예약 결제 기능.
        업데이트 날짜 : 2023.06.14
        '''
        serializer = PaymentScheduleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            data = serializer.save()
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, pk):
        '''
        작성자 : 송지명
        작성일 : 2023.06.13
        작성내용 : 예약 결제 후 예약 정보 조회, 캠페인 상태에 따라 결제 status 변경
        업데이트 날짜 : 2023.06.21
        '''
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        receipts = Payment.objects.get(user=request.user.id, pk=pk)
        merchant_uid = receipts.merchant_uid
        response = iamport.pay_schedule_get(merchant_uid)
        response_schedule = response['schedule_at']
        reservation_schedule = datetime.datetime.fromtimestamp(response_schedule)
        campaign = response['name']
        buyer = response['buyer_name']
        amount =response['amount']
        email = response['buyer_email']
        message =f"{buyer}님({email})은 {campaign}캠페인에 {amount}만큼 후원하셨습니다. \n결제일은 {reservation_schedule}입니다. \n후원에 진심으로 감사드립니다."
            
        return Response({"message": message}, status=status.HTTP_200_OK)
    
class ReceiptAPIView(APIView):
    
    def post(self, request, user_id):
        '''
        작성자 : 송지명
        작성일 : 2023.06.14
        작성내용: 결제 후 모델에 저장
        업데이트 날짜 : 2023.06.23
        '''
        merchant_uid = request.data.get('merchant_uid')
        imp_uid = request.data.get('imp_uid')
        amount = request.data.get('amount')
        user_data = User.objects.get(id=user_id)
        response = Payment.objects.create(user=user_data, amount=amount, imp_uid=imp_uid,merchant_uid=merchant_uid,  status =None)
        response_data = {
            'user': user_data.username,
            'merchant_uid': response.merchant_uid,
            'imp_uid': response.imp_uid,
            'amount': response.amount,
            
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def get(self, request, user_id):
        '''
        작성자 : 송지명
        작성일 : 2023.06.14
        작성내용 : 유저의 결제정보 전체조회(모델에서 갖고옴), 예약결제 미포함으로 변경
        업데이트 날짜 : 2023.06.20
        '''
        receipts = Payment.objects.filter(user=user_id, campaign__isnull=True)
        
        receipt_data = []
        for receipt in receipts :
            receipt_data.append({
                'id' : receipt.pk,
                'user' : receipt.user.username,
                'amount': receipt.amount,
                'created_at': receipt.created_at,
                'product' : receipt.product.product_name,
                'status' : receipt.status
            })
        return Response(receipt_data, status=status.HTTP_200_OK)
    
class DetailReciptAPIView(APIView):
    
    def get(self, request, pk):
        '''
        작성자: 송지명
        작성일: 2023.06.18
        작성내용: 결제 상세 영수증
        업데이트 일자 : 2023.07.03
        '''
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        detail_receipt = Payment.objects.get(pk=pk)
        imp_uid = detail_receipt.imp_uid
        response=iamport.find_by_imp_uid(imp_uid=imp_uid)
        response_data = response['receipt_url']
        return Response(response_data, status=status.HTTP_200_OK)
    
    
class RefundReceiptAPIView(APIView):
    def post(self, request, pk):
        '''
        작성자: 송지명
        작성일: 2023.06.18
        작성내용: 결제 취소 요청하기
        업데이트 일자 : 2023.06.21        
        '''
        order = ShopOrderDetail.objects.get(order=pk)
        if order.order_detail_status == 0:
            receipt = Payment.objects.get(order=pk)
            receipt_status = request.data.get('status')
            if receipt_status == 6:
                other_reason = request.data.get('other_reason')
                receipt.other_status = other_reason
            receipt.status=receipt_status
            receipt.save()
            order.order_detail_status = 6
            order.save()
            return Response({'message': '결제취소 요청이 접수되었습니다.'}, status=status.HTTP_200_OK)
        else :
            return Response({'message': '취소할 수 없는 주문입니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
    
    def get(self, request, pk):
        '''
        작성자: 송지명
        작성일: 2023.07.03
        작성내용: 결제 취소 status 갖고오기
        업데이트 일자 : 
        '''
        status_choices = dict(Payment.STATUS_CHOICES)
        return Response(status_choices, status=status.HTTP_200_OK)
    
        
class DetailScheduleReceiptAPIView(APIView):
    '''
    작성자 : 송지명
    작성일 : 2023.06.12
    작성내용 : 예약결제 후 영수증 정보
    업데이트 날짜 : 2023.07.03
    '''
    def get(self, request, pk):
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        receipt = Payment.objects.get(pk=pk)
        merchant_uid = receipt.merchant_uid
        response = iamport.find_by_merchant_uid(merchant_uid=merchant_uid)
        response_data = response['receipt_url']
        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request, pk):
        '''
        작성자 : 송지명
        작성일 : 2023.06.17
        작성내용 : 예약 취소
        업데이트 날짜 : 2023.06.20
        '''
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        token = iamport.get_headers()
        receipt = Payment.objects.get(pk=pk)
        merchant_uid = receipt.merchant_uid
        customer_uid = receipt.customer_uid
        cancle_url = "https://api.iamport.kr/subscribe/payments/unschedule"
        payload = {
            'customer_uid' : customer_uid,
            'merchant_uid' : merchant_uid
        }
        response = requests.post(cancle_url, payload, headers=token)
        if response.status_code == 200 :
            receipt.status = 1
            receipt.save()            
            return Response({"message":"예약 결제 취소 완료"}, status=status.HTTP_200_OK)
        else :
            return Response({"message":"결제 취소에 실패하였습니다."},status=status.HTTP_400_BAD_REQUEST)
        
    def check_payment_status(self):
        payments = Payment.objects.filter(campaign__isnull=False, status="0")
        for payment in payments:
            campaign = payment.campaign
            if campaign.status == 3:
               self.post(None, payment.pk)
            elif campaign.status == 2:
                payment.status = 5
                payment.save()
            else:
                pass
        
    
class RefundpaymentsAPIView(APIView):
    
    def post(self, request, pk):
        '''
        작성자: 송지명
        작성일: 2023.06.18
        작성내용: 결제 취소, admin이 확인하여 취소.
        업데이트 일자 : 2023.06.20        
        '''
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        token = iamport.get_headers()
        receipt = Payment.objects.get(order=pk)
        imp_uid = receipt.imp_uid
        merchant_uid = receipt.merchant_uid
        
        cancel_url = "https://api.iamport.kr/payments/cancel"
        payload = {
            'imp_uid[]': [imp_uid],
            'merchant_uid[]': [merchant_uid]
        }
        response = requests.post(cancel_url, data=payload, headers=token)
        
        if response.status_code == 200:
            # 결제 취소 성공
            receipt.status = "4"
            receipt.save()
            return Response({'message': '결제가 취소되었습니다.'}, status=status.HTTP_200_OK)
        else:
            # 결제 취소 실패
            return Response({'message': '결제 취소에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
class ScheduleReceiptAPIView(APIView):
    
    pagination_class = ReceiptPagination    
    def get(self, request):
        '''
        작성자 : 송지명
        작성일 : 2023.06.21
        작성내용 : 유저의 예약결제정보 전체조회(모델에서 갖고옴)
        업데이트 날짜 : 2023.07.04
        '''
        receipts = Payment.objects.filter(user=request.user.id, campaign__isnull=False).order_by('-campaign__campaign_end_date')
        paginated_receipts = self.pagination_class().paginate_queryset(receipts, request)
        receipt_data = []
        for receipt in paginated_receipts :     
            receipt_data.append({
                'id' : receipt.pk,
                'user' : receipt.user.username,
                'amount': receipt.amount,
                'created_at': receipt.created_at,
                'campaign' : receipt.campaign.title,
                'campaign_date' : receipt.campaign.campaign_end_date.strftime('%Y-%m-%d'),
                'status' : receipt.get_status_display()
            })
            
            
        return Response({'results': receipt_data, 'count':len(receipts)}, status=status.HTTP_200_OK)