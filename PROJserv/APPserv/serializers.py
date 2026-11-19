from decimal import Decimal
from django.db.models import Sum
from rest_framework import serializers
from .models import (
    Terminal, Employee, Shift, ClientTag, Client, ClientContact,
    ClientLegalInfo, DeviceModel, DeviceUnit, DeviceSnapshot,
    Service, Part, StockItem, RepairOrder, DeviceBundle,
    Diagnosis, RepairWork, InstalledPart, Donor, StockMovement,
    Payment, PaymentCashDetail, PaymentCardDetail, PaymentSBPDetail,
    LedgerEntry, Document, Warranty, WarrantyCase, OrderEvent
)


class TerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terminal
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'user', 'full_name', 'phone', 'role', 'terminals']


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class ClientTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientTag
        fields = '__all__'


class ClientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContact
        fields = ['id', 'client', 'channel', 'kind', 'value', 'is_primary']


class ClientLegalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientLegalInfo
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    contacts = ClientContactSerializer(many=True, read_only=True)
    legal_info = ClientLegalInfoSerializer(read_only=True)
    tags_detail = ClientTagSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'full_name', 'client_type', 'tags', 'tags_detail', 'contacts', 'legal_info', 'created_at']


class DeviceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceModel
        fields = '__all__'


class DeviceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSnapshot
        fields = '__all__'


class DeviceUnitSerializer(serializers.ModelSerializer):
    model_detail = DeviceModelSerializer(source='device_model', read_only=True)
    snapshot = DeviceSnapshotSerializer(read_only=True)

    class Meta:
        model = DeviceUnit
        fields = [
            'id', 'client', 'device_model', 'model_detail',
            'imei', 'serial_number', 'color', 'ownership_status',
            'snapshot', 'created_at'
        ]


class DeviceBundleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceBundle
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = '__all__'


class StockItemSerializer(serializers.ModelSerializer):
    part_name = serializers.ReadOnlyField(source='part.name')
    available_qty = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = ['id', 'terminal', 'part', 'part_name', 'quantity_in', 'quantity_reserved', 'available_qty']

    def get_available_qty(self, obj):
        return obj.quantity_in - obj.quantity_reserved


class DiagnosisSerializer(serializers.ModelSerializer):
    master_name = serializers.ReadOnlyField(source='master.full_name')

    class Meta:
        model = Diagnosis
        fields = '__all__'


class RepairWorkSerializer(serializers.ModelSerializer):
    service_title = serializers.ReadOnlyField(source='service.title')
    master_name = serializers.ReadOnlyField(source='master.full_name')

    class Meta:
        model = RepairWork
        fields = '__all__'


class InstalledPartSerializer(serializers.ModelSerializer):
    part_name = serializers.ReadOnlyField(source='part.name')
    part_article = serializers.ReadOnlyField(source='part.article')

    class Meta:
        model = InstalledPart
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warranty
        fields = '__all__'


class WarrantyCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarrantyCase
        fields = '__all__'


class OrderEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source='actor.full_name')

    class Meta:
        model = OrderEvent
        fields = '__all__'


class RepairOrderSerializer(serializers.ModelSerializer):
    client_detail = ClientSerializer(source='client', read_only=True)
    device_detail = DeviceUnitSerializer(source='device_unit', read_only=True)
    bundle = DeviceBundleSerializer(read_only=True)
    diagnoses = DiagnosisSerializer(many=True, read_only=True)
    works = RepairWorkSerializer(many=True, read_only=True)
    installed_parts = InstalledPartSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)
    calculated_total = serializers.SerializerMethodField()
    paid_total = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()

    class Meta:
        model = RepairOrder
        fields = [
            'id', 'client', 'client_detail', 'device_unit', 'device_detail',
            'terminal', 'accepted_by', 'status', 'discount_amount',
            'calculated_total', 'paid_total', 'balance_due',
            'bundle', 'diagnoses', 'works', 'installed_parts',
            'payments', 'events', 'created_at', 'closed_at'
        ]

    def get_calculated_total(self, obj):
        works_sum = obj.works.exclude(status='failed').aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        parts_sum = obj.installed_parts.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        total = works_sum + parts_sum - obj.discount_amount
        return max(total, Decimal('0.00'))

    def get_paid_total(self, obj):
        paid = obj.payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return paid

    def get_balance_due(self, obj):
        return self.get_calculated_total(obj) - self.get_paid_total(obj)

class DonorSerializer(serializers.ModelSerializer):
    device_detail = DeviceUnitSerializer(source='device_unit', read_only=True)

    class Meta:
        model = Donor
        fields = ['id', 'device_unit', 'device_detail', 'source', 'status', 'extracted_parts', 'donor_credit']


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = '__all__'