import json
import asyncio
import aiohttp
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page, never_cache
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import (
    Terminal, Employee, Shift, ClientTag, Client, ClientContact,
    ClientLegalInfo, DeviceModel, DeviceUnit, DeviceSnapshot,
    DeviceBundle, Service, Part, StockItem, StockMovement,
    RepairOrder, Diagnosis, RepairWork, InstalledPart, Donor,
    Payment, PaymentCashDetail, LedgerEntry, Document,
    Warranty, WarrantyCase, OrderEvent
)
from .serializers import (
    TerminalSerializer, EmployeeSerializer, ShiftSerializer,
    ClientSerializer, ClientContactSerializer, DeviceModelSerializer,
    DeviceUnitSerializer, DeviceBundleSerializer, ServiceSerializer,
    PartSerializer, StockItemSerializer, RepairOrderSerializer,
    DiagnosisSerializer, RepairWorkSerializer, InstalledPartSerializer,
    DonorSerializer, StockMovementSerializer, PaymentSerializer,
    LedgerEntrySerializer, DocumentSerializer, WarrantySerializer,
    WarrantyCaseSerializer, OrderEventSerializer
)
from .permissions import IsEmployeeOrStaffPermission
from .forms import ServiceForm


def sandbox_page(request):
    return render(request, 'index.html')


@method_decorator(csrf_exempt, name='dispatch')
class ManualServiceListView(View):
    def get(self, request):
        services_list = [
            {
                'id': s.id,
                'code': s.code,
                'title': s.title,
                'category': s.category,
                'base_price': float(s.base_price),
                'standard_duration_minutes': s.standard_duration_minutes,
            }
            for s in Service.objects.all()
        ]
        return JsonResponse({'services': services_list})

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        form = ServiceForm(data)
        if form.is_valid():
            obj = form.save()
            return JsonResponse({'id': obj.id, 'code': obj.code}, status=201)
        return JsonResponse({'errors': form.errors}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ManualServiceDetailView(View):
    def get(self, request, service_id):
        s = get_object_or_404(Service, id=service_id)
        data = {
            'id': s.id,
            'code': s.code,
            'title': s.title,
            'category': s.category,
            'base_price': float(s.base_price),
            'standard_duration_minutes': s.standard_duration_minutes,
        }
        return JsonResponse(data)

    def put(self, request, service_id):
        s = get_object_or_404(Service, id=service_id)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        form = ServiceForm(data, instance=s)
        if form.is_valid():
            obj = form.save()
            return JsonResponse({'id': obj.id, 'title': obj.title, 'base_price': float(obj.base_price)}, status=200)
        return JsonResponse({'errors': form.errors}, status=400)


async def async_supplier_check(request):
    async def fetch_quote(session, index):
        try:
            timeout = aiohttp.ClientTimeout(total=2)
            async with session.get('http://matsyuk.site:2323/', timeout=timeout) as r:
                text = await r.text()
                return int(text.strip())
        except Exception:
            await asyncio.sleep(0.3)
            return 1000 + index * 250

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_quote(session, i)) for i in range(1, 4)]
        numbers = await asyncio.gather(*tasks)

    return JsonResponse({
        'quotes': numbers,
        'sum': sum(numbers),
        'average_part_cost': round(sum(numbers) / len(numbers), 2)
    })


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def seed_database(request):
    with transaction.atomic():
        t1, _ = Terminal.objects.get_or_create(
            name='FixMaster Центр (ул. Ленина, 15)',
            defaults={
                'address': 'г. Сургут, ул. Ленина, 15',
                'coordinates': '61.254035, 73.396221',
                'phone': '+7 (3462) 55-01-01',
                'opening_hours': '09:00 - 20:00',
                'is_active': True
            }
        )
        t2, _ = Terminal.objects.get_or_create(
            name='FixMaster ТРЦ Сити Молл',
            defaults={
                'address': 'г. Сургут, Югорский тракт, 38',
                'coordinates': '61.239110, 73.374890',
                'phone': '+7 (3462) 55-02-02',
                'opening_hours': '10:00 - 22:00',
                'is_active': True
            }
        )

        admin_user = request.user
        emp_admin, _ = Employee.objects.get_or_create(
            user=admin_user,
            defaults={
                'full_name': 'Вадим (Старший мастер / Админ)',
                'phone': '+7 (900) 111-22-33',
                'role': 'admin'
            }
        )
        emp_admin.terminals.set([t1, t2])

        master_user, _ = User.objects.get_or_create(username='master_alex')
        emp_master, _ = Employee.objects.get_or_create(
            user=master_user,
            defaults={
                'full_name': 'Алексей Соколов (Инженер BGA)',
                'phone': '+7 (900) 222-33-44',
                'role': 'master'
            }
        )
        emp_master.terminals.set([t1])

        shift, _ = Shift.objects.get_or_create(
            employee=emp_admin,
            terminal=t1,
            ended_at=None,
            defaults={'opening_cash': Decimal('5000.00')}
        )

        tag_vip, _ = ClientTag.objects.get_or_create(code='vip', defaults={'title': 'VIP Клиент'})
        tag_corp, _ = ClientTag.objects.get_or_create(code='b2b', defaults={'title': 'Корпоративный'})

        c1, _ = Client.objects.get_or_create(
            full_name='Иванов Артем Сергеевич',
            defaults={'client_type': 'individual'}
        )
        c1.tags.add(tag_vip)
        ClientContact.objects.get_or_create(
            client=c1, channel='phone', value='+79128887766',
            defaults={'kind': 'personal', 'is_primary': True}
        )
        ClientContact.objects.get_or_create(
            client=c1, channel='telegram', value='@artem_surgut',
            defaults={'kind': 'personal', 'is_primary': False}
        )

        c2, _ = Client.objects.get_or_create(
            full_name='ООО «СеверЛогистик»',
            defaults={'client_type': 'legal'}
        )
        c2.tags.add(tag_corp)
        ClientContact.objects.get_or_create(
            client=c2, channel='phone', value='+73462998877',
            defaults={'kind': 'work', 'is_primary': True}
        )
        ClientLegalInfo.objects.get_or_create(
            client=c2,
            defaults={
                'company_name': 'ООО «СеверЛогистик»',
                'inn': '8602123456',
                'ogrn': '1188617001234',
                'legal_address': 'г. Сургут, ул. Профсоюзов, 20'
            }
        )

        dm_iphone, _ = DeviceModel.objects.get_or_create(
            brand='Apple',
            model_name='iPhone 13 Pro 128GB',
            defaults={'category': 'Смартфон', 'specs_json': {'screen': '6.1 OLED 120Hz', 'chip': 'A15 Bionic'}}
        )
        dm_samsung, _ = DeviceModel.objects.get_or_create(
            brand='Samsung',
            model_name='Galaxy S23 Ultra 256GB',
            defaults={'category': 'Смартфон', 'specs_json': {'screen': '6.8 Dynamic AMOLED', 'stylus': True}}
        )

        unit_client, _ = DeviceUnit.objects.get_or_create(
            imei='354891092837461',
            defaults={
                'client': c1,
                'device_model': dm_iphone,
                'serial_number': 'F2L9X8Q1P0',
                'color': 'Sierra Blue',
                'ownership_status': 'own'
            }
        )
        DeviceSnapshot.objects.get_or_create(
            device_unit=unit_client,
            defaults={
                'board_version': '820-02096-A',
                'storage_gb': 128,
                'region_code': 'RU/A',
                'activation_lock_enabled': False,
                'battery_health_percent': 79
            }
        )

        unit_donor, _ = DeviceUnit.objects.get_or_create(
            imei='354891099999999',
            defaults={
                'client': c1,
                'device_model': dm_iphone,
                'serial_number': 'DONOR13PRO',
                'color': 'Graphite',
                'ownership_status': 'donor_client'
            }
        )

        srv_diag, _ = Service.objects.get_or_create(
            code='SRV-DIAG',
            defaults={'title': 'Комплексная диагностика', 'category': 'Диагностика', 'base_price': Decimal('0.00'), 'standard_duration_minutes': 30}
        )
        srv_screen, _ = Service.objects.get_or_create(
            code='SRV-SCR-13P',
            defaults={'title': 'Замена дисплейного модуля iPhone 13 Pro', 'category': 'Модульный ремонт', 'base_price': Decimal('3500.00'), 'standard_duration_minutes': 90}
        )
        srv_batt, _ = Service.objects.get_or_create(
            code='SRV-BAT-13P',
            defaults={'title': 'Замена аккумулятора с перепайкой контроллера BMS', 'category': 'Пайка / АКБ', 'base_price': Decimal('2500.00'), 'standard_duration_minutes': 60}
        )

        part_screen, _ = Part.objects.get_or_create(
            article='PRT-IP13P-OLED-ORIG',
            defaults={
                'name': 'Дисплей iPhone 13 Pro (Оригинал Снятый)',
                'brand': 'Apple',
                'category': 'screen',
                'purchase_price': Decimal('9500.00'),
                'retail_price': Decimal('14500.00'),
                'min_stock': 2
            }
        )
        part_screen.compatible_models.add(dm_iphone)

        part_batt, _ = Part.objects.get_or_create(
            article='PRT-IP13P-BAT-ORIG',
            defaults={
                'name': 'Аккумулятор iPhone 13 Pro 3095 mAh',
                'brand': 'Apple',
                'category': 'battery',
                'purchase_price': Decimal('1800.00'),
                'retail_price': Decimal('3500.00'),
                'min_stock': 3
            }
        )
        part_batt.compatible_models.add(dm_iphone)

        StockItem.objects.update_or_create(
            terminal=t1, part=part_screen,
            defaults={'quantity_in': 4, 'quantity_reserved': 0}
        )
        StockItem.objects.update_or_create(
            terminal=t1, part=part_batt,
            defaults={'quantity_in': 6, 'quantity_reserved': 0}
        )

        donor_obj, _ = Donor.objects.get_or_create(
            device_unit=unit_donor,
            defaults={
                'source': 'client',
                'status': 'received',
                'donor_credit': Decimal('4000.00')
            }
        )

        order1, created = RepairOrder.objects.get_or_create(
            client=c1,
            device_unit=unit_client,
            terminal=t1,
            accepted_by=emp_admin,
            defaults={
                'status': 'in_repair',
                'discount_amount': Decimal('500.00')
            }
        )

        if created:
            DeviceBundle.objects.create(
                order=order1,
                device_unit=unit_client,
                has_case=True,
                has_sim=False,
                has_memory_card=False,
                has_charger=False,
                has_box=False,
                accessories_list=['Силиконовый чехол MagSafe'],
                photos_urls=['/media/intake/ip13p_front.jpg'],
                client_declared_defect='Разбито стекло после падения, полосы по экрану, быстро садится батарея'
            )

            Diagnosis.objects.create(
                order=order1,
                master=emp_master,
                problem_reported='Разбит экран, слабый АКБ',
                problem_found='Повреждена матрица OLED, износ АКБ 79% (780 циклов), FaceID исправен',
                checklist_json={'face_id': 'OK', 'true_tone': 'OK', 'cameras': 'OK', 'charging_port': 'OK'},
                is_repairable=True,
                recommendation='Замена дисплейного модуля с переносом чипа IC и замена элемента АКБ',
                estimated_price=Decimal('23500.00')
            )

            RepairWork.objects.create(
                order=order1,
                service=srv_screen,
                master=emp_master,
                work_type='repair',
                price=Decimal('3500.00'),
                duration_minutes=90,
                status='done',
                note='Чип экрана перенесен, TrueTone сохранен'
            )
            RepairWork.objects.create(
                order=order1,
                service=srv_batt,
                master=emp_master,
                work_type='repair',
                price=Decimal('2500.00'),
                duration_minutes=60,
                status='in_progress',
                note='Калибровка контроллера АКБ'
            )

            InstalledPart.objects.create(
                order=order1,
                device_unit=unit_client,
                part=part_screen,
                price=Decimal('14500.00'),
                warranty_months=6
            )
            InstalledPart.objects.create(
                order=order1,
                device_unit=unit_client,
                part=part_batt,
                price=Decimal('3500.00'),
                warranty_months=3
            )

            p1 = Payment.objects.create(
                order=order1,
                amount=Decimal('10000.00'),
                currency='RUB',
                method='cash',
                status='paid',
                provider='cashbox_t1',
                paid_at=timezone.now()
            )
            PaymentCashDetail.objects.create(
                payment=p1,
                shift=shift,
                received_amount=Decimal('10000.00'),
                change_amount=Decimal('0.00')
            )
            LedgerEntry.objects.create(account='cashbox', debit=Decimal('10000.00'), credit=Decimal('0.00'), order=order1, payment=p1)
            LedgerEntry.objects.create(account='revenue', debit=Decimal('0.00'), credit=Decimal('10000.00'), order=order1, payment=p1)

            Document.objects.create(
                order=order1,
                doc_type='intake_receipt',
                number=f'KV-2026-{order1.id:04d}',
                template_version='v1'
            )

            OrderEvent.objects.create(order=order1, actor=emp_admin, old_status='', new_status='received', comment='Устройство принято на точке Ленина 15')
            OrderEvent.objects.create(order=order1, actor=emp_master, old_status='received', new_status='diagnostics', comment='Взято на диагностику')
            OrderEvent.objects.create(order=order1, actor=emp_master, old_status='diagnostics', new_status='in_repair', comment='Клиент согласовал стоимость, запчасти выданы')

    return Response({
        'status': 'success',
        'message': 'База данных успешно заполнена демо-данными сервисного центра!',
        'created_order_id': order1.id,
        'donor_id': donor_obj.id,
        'shift_id': shift.id
    })


class TerminalViewSet(ModelViewSet):
    queryset = Terminal.objects.all()
    serializer_class = TerminalSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class EmployeeViewSet(ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsEmployeeOrStaffPermission]


@method_decorator(never_cache, name='dispatch')
class ShiftViewSet(ModelViewSet):
    queryset = Shift.objects.select_related('employee', 'terminal').order_by('-started_at')
    serializer_class = ShiftSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['POST'], detail=True, url_path='close')
    def close_shift(self, request, pk=None):
        shift = self.get_object()
        if shift.ended_at is not None:
            raise ValidationError({'detail': 'Смена уже закрыта'})

        cash_in = Payment.objects.filter(
            order__terminal=shift.terminal,
            method='cash',
            status='paid',
            paid_at__gte=shift.started_at
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        cash_out = Payment.objects.filter(
            order__terminal=shift.terminal,
            method='cash',
            status='refunded',
            paid_at__gte=shift.started_at
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        shift.closing_cash = shift.opening_cash + cash_in - cash_out
        shift.ended_at = timezone.now()
        shift.save()
        return Response(self.get_serializer(shift).data)


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.prefetch_related('contacts', 'tags').all()
    serializer_class = ClientSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['GET'], detail=False, url_path='by-phone')
    def find_by_phone(self, request):
        phone = request.query_params.get('phone', '').strip()
        if not phone:
            raise ValidationError({'detail': 'Параметр phone обязателен'})
        clients = self.get_queryset().filter(contacts__channel='phone', contacts__value__icontains=phone).distinct()
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)


class ClientContactViewSet(ModelViewSet):
    queryset = ClientContact.objects.all()
    serializer_class = ClientContactSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


@method_decorator(cache_page(60 * 15), name='list')
class DeviceModelViewSet(ModelViewSet):
    queryset = DeviceModel.objects.all()
    serializer_class = DeviceModelSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class DeviceUnitViewSet(ModelViewSet):
    queryset = DeviceUnit.objects.select_related('device_model', 'snapshot').all()
    serializer_class = DeviceUnitSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['GET'], detail=False, url_path='donors')
    def get_donors(self, request):
        donors = self.get_queryset().filter(ownership_status__in=['donor_client', 'donor_stock'])
        serializer = self.get_serializer(donors, many=True)
        return Response(serializer.data)


class DeviceBundleViewSet(ModelViewSet):
    queryset = DeviceBundle.objects.all()
    serializer_class = DeviceBundleSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


@method_decorator(cache_page(60 * 15), name='list')
class ServiceViewSet(ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class PartViewSet(ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class StockItemViewSet(ModelViewSet):
    queryset = StockItem.objects.select_related('part', 'terminal').all()
    serializer_class = StockItemSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class DonorViewSet(ModelViewSet):
    queryset = Donor.objects.select_related('device_unit').prefetch_related('extracted_parts').all()
    serializer_class = DonorSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @action(methods=['POST'], detail=True, url_path='disassemble')
    def disassemble(self, request, pk=None):
        donor = self.get_object()
        if donor.status != 'received':
            raise ValidationError({'detail': 'Донор уже разобран или списан'})

        terminal_id = request.data.get('terminal_id')
        part_ids = request.data.get('part_ids', [])
        if not terminal_id or not part_ids:
            raise ValidationError({'detail': 'Укажите terminal_id и список part_ids'})

        terminal = Terminal.objects.filter(id=terminal_id).first()
        if not terminal:
            raise ValidationError({'detail': 'Терминал не найден'})

        with transaction.atomic():
            parts = Part.objects.filter(id__in=part_ids)
            for part in parts:
                stock, _ = StockItem.objects.get_or_create(terminal=terminal, part=part)
                stock.quantity_in += 1
                stock.save()
                StockMovement.objects.create(
                    part=part,
                    to_terminal=terminal,
                    movement_type='incoming',
                    quantity=1,
                    reason=f'Разбор донора #{donor.id}'
                )
                donor.extracted_parts.add(part)

            donor.status = 'disassembled'
            donor.device_unit.ownership_status = 'donor_stock'
            donor.device_unit.save()
            donor.save()

        return Response(self.get_serializer(donor).data)


@method_decorator(never_cache, name='dispatch')
class RepairOrderViewSet(ModelViewSet):
    queryset = RepairOrder.objects.select_related(
        'client', 'device_unit', 'terminal', 'accepted_by'
    ).prefetch_related(
        'works', 'installed_parts', 'payments', 'diagnoses', 'events'
    ).order_by('-created_at')
    serializer_class = RepairOrderSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsEmployeeOrStaffPermission]

    def perform_create(self, serializer):
        device = serializer.validated_data['device_unit']
        if device.ownership_status == 'returned':
            raise ValidationError({'detail': 'Нельзя создать заказ на возвращённое устройство без повторного приёма'})
        order = serializer.save()
        OrderEvent.objects.create(
            order=order,
            actor=order.accepted_by,
            old_status='',
            new_status=order.status,
            comment='Заказ-наряд создан при приёме устройства'
        )

    @action(methods=['POST'], detail=True, url_path='transition')
    def transition_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        valid_statuses = dict(RepairOrder.STATUS_CHOICES).keys()

        if new_status not in valid_statuses:
            raise ValidationError({'detail': 'Недопустимый статус заказа'})

        if new_status == 'issued':
            serializer = self.get_serializer(order)
            if serializer.data['balance_due'] > 0:
                raise ValidationError({'detail': 'Нельзя выдать устройство: заказ не оплачен полностью'})
            order.closed_at = timezone.now()

        old_status = order.status
        order.status = new_status
        order.save()

        actor = getattr(request.user, 'employee_profile', order.accepted_by)
        OrderEvent.objects.create(
            order=order,
            actor=actor,
            old_status=old_status,
            new_status=new_status,
            comment=comment
        )
        return Response(self.get_serializer(order).data)

    @action(methods=['GET'], detail=False, url_path='period/(?P<period>week|month|year)/(?P<from_date>[^/.]+)')
    def orders_by_period(self, request, period=None, from_date=None):
        try:
            start_dt = datetime.fromisoformat(from_date)
        except ValueError:
            raise ValidationError({'detail': 'Неверный формат даты, используйте YYYY-MM-DD'})

        days_map = {'week': 7, 'month': 30, 'year': 365}
        end_dt = start_dt + timedelta(days=days_map[period])
        orders = self.get_queryset().filter(created_at__gte=start_dt, created_at__lt=end_dt)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class DiagnosisViewSet(ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class RepairWorkViewSet(ModelViewSet):
    queryset = RepairWork.objects.all()
    serializer_class = RepairWorkSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class InstalledPartViewSet(ModelViewSet):
    queryset = InstalledPart.objects.all()
    serializer_class = InstalledPartSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.validated_data['order']
            part = serializer.validated_data['part']
            stock = StockItem.objects.select_for_update().filter(
                terminal=order.terminal,
                part=part
            ).first()

            if not stock or (stock.quantity_in - stock.quantity_reserved) < 1:
                raise ValidationError({'detail': 'Запчасть отсутствует на складе данного терминала'})

            stock.quantity_in -= 1
            stock.save()

            StockMovement.objects.create(
                part=part,
                from_terminal=order.terminal,
                movement_type='issue',
                quantity=1,
                order=order,
                reason=f'Установка в заказ #{order.id}'
            )
            serializer.save()


@method_decorator(never_cache, name='dispatch')
class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            payment = serializer.save(paid_at=timezone.now(), status='paid')
            LedgerEntry.objects.create(
                account='cashbox',
                debit=payment.amount,
                credit=0,
                order=payment.order,
                payment=payment
            )
            LedgerEntry.objects.create(
                account='revenue',
                debit=0,
                credit=payment.amount,
                order=payment.order,
                payment=payment
            )

    @action(methods=['POST'], detail=True, url_path='refund')
    def refund_payment(self, request, pk=None):
        parent = self.get_object()
        if parent.status != 'paid':
            raise ValidationError({'detail': 'Возврат возможен только для оплаченного платежа'})

        refund_amount = Decimal(str(request.data.get('amount', parent.amount)))
        if refund_amount <= 0 or refund_amount > parent.amount:
            raise ValidationError({'detail': 'Некорректная сумма возврата'})

        with transaction.atomic():
            refund_obj = Payment.objects.create(
                order=parent.order,
                amount=refund_amount,
                currency=parent.currency,
                method=parent.method,
                status='refunded',
                parent_payment=parent,
                paid_at=timezone.now()
            )
            parent.status = 'partially_refunded' if refund_amount < parent.amount else 'refunded'
            parent.save()

            LedgerEntry.objects.create(
                account='revenue',
                debit=refund_amount,
                credit=0,
                order=parent.order,
                payment=refund_obj
            )
            LedgerEntry.objects.create(
                account='cashbox',
                debit=0,
                credit=refund_amount,
                order=parent.order,
                payment=refund_obj
            )

        return Response(self.get_serializer(refund_obj).data)

    @action(methods=['POST'], detail=False, url_path='apply-donor-credit')
    def apply_donor_credit(self, request):
        order_id = request.data.get('order_id')
        donor_id = request.data.get('donor_id')
        order = RepairOrder.objects.filter(id=order_id).first()
        donor = Donor.objects.filter(id=donor_id).first()

        if not order or not donor:
            raise ValidationError({'detail': 'Заказ или донор не найден'})
        if donor.donor_credit <= 0:
            raise ValidationError({'detail': 'У данного донора нет доступного кредита для зачёта'})

        with transaction.atomic():
            amount = donor.donor_credit
            payment = Payment.objects.create(
                order=order,
                amount=amount,
                method='transfer',
                status='paid',
                provider='donor_offset',
                paid_at=timezone.now()
            )
            donor.donor_credit = Decimal('0.00')
            donor.save()

            LedgerEntry.objects.create(
                account='receivables',
                debit=amount,
                credit=0,
                order=order,
                payment=payment
            )
            LedgerEntry.objects.create(
                account='revenue',
                debit=0,
                credit=amount,
                order=order,
                payment=payment
            )

        return Response(self.get_serializer(payment).data)


class DocumentViewSet(ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class WarrantyViewSet(ModelViewSet):
    queryset = Warranty.objects.all()
    serializer_class = WarrantySerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class WarrantyCaseViewSet(ModelViewSet):
    queryset = WarrantyCase.objects.all()
    serializer_class = WarrantyCaseSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]