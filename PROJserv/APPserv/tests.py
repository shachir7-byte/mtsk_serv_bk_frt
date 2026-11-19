import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from .models import Terminal, Employee, Client, DeviceModel, DeviceUnit, Service, RepairOrder, RepairWork, Payment


class ZmartServApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='test_admin', password='secret', email='a@b.c')
        self.token = Token.objects.create(user=self.user)
        self.api = APIClient()
        self.terminal = Terminal.objects.create(
            name='zmart-serv Тест',
            address='г. Сургут',
            phone='+79000000000',
            opening_hours='09:00-20:00'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            full_name='Тест Мастер',
            phone='+79001111111',
            role='admin'
        )
        self.employee.terminals.add(self.terminal)
        self.client_obj = Client.objects.create(full_name='Тестовый Клиент')
        self.model = DeviceModel.objects.create(brand='Apple', model_name='iPhone 14', category='Смартфон')
        self.unit = DeviceUnit.objects.create(client=self.client_obj, device_model=self.model, imei='111222333444555')
        self.service = Service.objects.create(code='TST-01', title='Замена экрана', category='Ремонт', base_price=Decimal('4000.00'))

    def test_orders_require_token_auth(self):
        response = self.api.get('/api/orders/')
        self.assertEqual(response.status_code, 401)

    def test_create_order_creates_event_and_calculates_balance(self):
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.api.post('/api/orders/', {
            'client': self.client_obj.id,
            'device_unit': self.unit.id,
            'terminal': self.terminal.id,
            'accepted_by': self.employee.id,
            'discount_amount': '500.00'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        order = RepairOrder.objects.get(id=response.data['id'])
        self.assertEqual(order.events.count(), 1)

        RepairWork.objects.create(order=order, service=self.service, master=self.employee, price=Decimal('4000.00'), status='done')
        Payment.objects.create(order=order, amount=Decimal('1500.00'), method='cash', status='paid')

        detail = self.api.get(f'/api/orders/{order.id}/')
        self.assertEqual(Decimal(str(detail.data['calculated_total'])), Decimal('3500.00'))
        self.assertEqual(Decimal(str(detail.data['paid_total'])), Decimal('1500.00'))
        self.assertEqual(Decimal(str(detail.data['balance_due'])), Decimal('2000.00'))

    def test_manual_cbv_services_endpoint(self):
        res_post = self.client.post(
            '/api/manual-services/',
            data=json.dumps({
                'code': 'TST-02',
                'title': 'Чистка динамика',
                'category': 'Сервис',
                'base_price': '1200.00',
                'standard_duration_minutes': 30
            }),
            content_type='application/json'
        )
        self.assertEqual(res_post.status_code, 201)
        res_get = self.client.get('/api/manual-services/')
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(len(res_get.json()['services']), 2)