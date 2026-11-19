from django.db import models
from django.contrib.auth.models import User


class Terminal(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    coordinates = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=30)
    opening_hours = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


class Employee(models.Model):
    ROLE_CHOICES = [
        ('master', 'Мастер'),
        ('receiver', 'Приёмщик'),
        ('cashier', 'Кассир'),
        ('admin', 'Администратор'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='master')
    terminals = models.ManyToManyField(Terminal, related_name='employees')


class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shifts')
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='shifts')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)


class ClientTag(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)


class Client(models.Model):
    CLIENT_TYPES = [
        ('individual', 'Физическое лицо'),
        ('legal', 'Юридическое лицо'),
    ]
    full_name = models.CharField(max_length=200)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, default='individual')
    tags = models.ManyToManyField(ClientTag, blank=True, related_name='clients')
    created_at = models.DateTimeField(auto_now_add=True)


class ClientContact(models.Model):
    CHANNEL_CHOICES = [
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('telegram', 'Telegram'),
    ]
    KIND_CHOICES = [
        ('personal', 'Личный'),
        ('work', 'Рабочий'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='phone')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='personal')
    value = models.CharField(max_length=150, db_index=True)
    is_primary = models.BooleanField(default=False)


class ClientLegalInfo(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='legal_info')
    company_name = models.CharField(max_length=255)
    inn = models.CharField(max_length=12, unique=True)
    ogrn = models.CharField(max_length=15, blank=True, null=True)
    legal_address = models.CharField(max_length=255)


class DeviceModel(models.Model):
    brand = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=150, db_index=True)
    category = models.CharField(max_length=100)
    specs_json = models.JSONField(default=dict, blank=True)


class DeviceUnit(models.Model):
    OWNERSHIP_CHOICES = [
        ('own', 'Клиентский'),
        ('donor_client', 'Донор от клиента'),
        ('donor_stock', 'Донор со склада'),
        ('purchased', 'Куплен под заказ'),
        ('exchange', 'Trade-in / Обмен'),
        ('returned', 'Возвращён клиенту'),
    ]
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    device_model = models.ForeignKey(DeviceModel, on_delete=models.PROTECT, related_name='units')
    imei = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    ownership_status = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='own')
    created_at = models.DateTimeField(auto_now_add=True)


class DeviceSnapshot(models.Model):
    device_unit = models.OneToOneField(DeviceUnit, on_delete=models.CASCADE, related_name='snapshot')
    board_version = models.CharField(max_length=100, blank=True, null=True)
    storage_gb = models.IntegerField(blank=True, null=True)
    region_code = models.CharField(max_length=50, blank=True, null=True)
    activation_lock_enabled = models.BooleanField(default=False)
    battery_health_percent = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


class Service(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    standard_duration_minutes = models.IntegerField(default=60)


class Part(models.Model):
    CATEGORY_CHOICES = [
        ('screen', 'Экран/Дисплей'),
        ('battery', 'Аккумулятор'),
        ('camera', 'Камера'),
        ('connector', 'Разъём'),
        ('board', 'Плата/Компонент'),
        ('housing', 'Корпус/Крышка'),
    ]
    article = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    compatible_models = models.ManyToManyField(DeviceModel, related_name='compatible_parts', blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.IntegerField(default=1)
    is_tracked = models.BooleanField(default=True)


class StockItem(models.Model):
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, related_name='stock_items')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='stock_items')
    quantity_in = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)

    class Meta:
        unique_together = ('terminal', 'part')


class RepairOrder(models.Model):
    STATUS_CHOICES = [
        ('received', 'Принят'),
        ('diagnostics', 'На диагностике'),
        ('approval', 'На согласовании'),
        ('in_repair', 'В ремонте'),
        ('testing', 'Тестирование'),
        ('ready', 'Готов к выдаче'),
        ('issued', 'Выдан клиенту'),
        ('cancelled', 'Отказ от ремонта'),
    ]
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='orders')
    device_unit = models.ForeignKey(DeviceUnit, on_delete=models.PROTECT, related_name='orders')
    terminal = models.ForeignKey(Terminal, on_delete=models.PROTECT, related_name='orders')
    accepted_by = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='accepted_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    closed_at = models.DateTimeField(blank=True, null=True)


class DeviceBundle(models.Model):
    order = models.OneToOneField(RepairOrder, on_delete=models.CASCADE, related_name='bundle')
    device_unit = models.ForeignKey(DeviceUnit, on_delete=models.CASCADE, related_name='bundles')
    has_case = models.BooleanField(default=False)
    has_sim = models.BooleanField(default=False)
    has_memory_card = models.BooleanField(default=False)
    has_charger = models.BooleanField(default=False)
    has_box = models.BooleanField(default=False)
    accessories_list = models.JSONField(default=list, blank=True)
    photos_urls = models.JSONField(default=list, blank=True)
    client_declared_defect = models.TextField()


class Diagnosis(models.Model):
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='diagnoses')
    master = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='diagnoses')
    problem_reported = models.TextField()
    problem_found = models.TextField()
    checklist_json = models.JSONField(default=dict)
    is_repairable = models.BooleanField(default=True)
    recommendation = models.TextField(blank=True)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class RepairWork(models.Model):
    WORK_TYPES = [
        ('repair', 'Ремонт'),
        ('diagnostics', 'Диагностика'),
        ('cleaning', 'Чистка'),
        ('flashing', 'Прошивка'),
        ('unlock', 'Разблокировка'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('in_progress', 'В процессе'),
        ('done', 'Выполнено'),
        ('failed', 'Не удалось'),
    ]
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='works')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='repair_works')
    master = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='performed_works')
    work_type = models.CharField(max_length=20, choices=WORK_TYPES, default='repair')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)


class InstalledPart(models.Model):
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='installed_parts')
    device_unit = models.ForeignKey(DeviceUnit, on_delete=models.CASCADE, related_name='installed_parts')
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='installations')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    warranty_months = models.IntegerField(default=3)
    installed_at = models.DateTimeField(auto_now_add=True)


class Donor(models.Model):
    SOURCE_CHOICES = [
        ('client', 'От клиента'),
        ('purchase', 'Закупка'),
    ]
    STATUS_CHOICES = [
        ('received', 'Получен'),
        ('disassembled', 'Разобран'),
        ('in_stock', 'На складе'),
        ('installed', 'Установлен'),
        ('sold', 'Продан'),
    ]
    device_unit = models.OneToOneField(DeviceUnit, on_delete=models.CASCADE, related_name='donor_record')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    extracted_parts = models.ManyToManyField(Part, blank=True, related_name='donors')
    donor_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('incoming', 'Приход'),
        ('issue', 'Выдача в ремонт'),
        ('return', 'Возврат'),
        ('write_off', 'Списание'),
        ('transfer', 'Перемещение'),
    ]
    part = models.ForeignKey(Part, on_delete=models.PROTECT, related_name='movements')
    from_terminal = models.ForeignKey(Terminal, on_delete=models.PROTECT, null=True, blank=True, related_name='outgoing_movements')
    to_terminal = models.ForeignKey(Terminal, on_delete=models.PROTECT, null=True, blank=True, related_name='incoming_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    order = models.ForeignKey(RepairOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Банковская карта'),
        ('sbp', 'СБП'),
        ('transfer', 'Перевод по счёту'),
        ('telegram_stars', 'Telegram Stars'),
        ('credit', 'Рассрочка/Кредит'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('paid', 'Оплачен'),
        ('refunded', 'Возвращён'),
        ('partially_refunded', 'Частично возвращён'),
    ]
    order = models.ForeignKey(RepairOrder, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='RUB')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider = models.CharField(max_length=100, blank=True)
    external_id = models.CharField(max_length=150, blank=True, null=True)
    receipt_link = models.URLField(blank=True, null=True)
    parent_payment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_payments')
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentCashDetail(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='cash_detail')
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name='cash_payments')
    received_amount = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


class PaymentCardDetail(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='card_detail')
    acquiring_terminal_id = models.CharField(max_length=100)
    rrn = models.CharField(max_length=50)
    auth_code = models.CharField(max_length=50)


class PaymentSBPDetail(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='sbp_detail')
    qr_id = models.CharField(max_length=150)
    sbp_transaction_id = models.CharField(max_length=150)


class LedgerEntry(models.Model):
    ACCOUNT_CHOICES = [
        ('cashbox', 'Касса'),
        ('receivables', 'Расчёты с клиентами'),
        ('revenue', 'Выручка'),
        ('cogs', 'Себестоимость'),
        ('debt', 'Долг'),
    ]
    account = models.CharField(max_length=30, choices=ACCOUNT_CHOICES)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    order = models.ForeignKey(RepairOrder, on_delete=models.PROTECT, related_name='ledger_entries')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    DOC_TYPES = [
        ('intake_receipt', 'Квитанция приёма'),
        ('completion_act', 'Акт выполненных работ'),
        ('payment_receipt', 'Квитанция оплаты'),
        ('warranty_card', 'Гарантийный талон'),
        ('service_report', 'Сервисный отчёт'),
    ]
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES)
    number = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    template_version = models.CharField(max_length=20, default='v1')
    pdf_url = models.URLField(blank=True, null=True)
    signature_hash = models.CharField(max_length=255, blank=True)


class Warranty(models.Model):
    WARRANTY_TYPES = [
        ('work', 'На работу'),
        ('part', 'На запчасть'),
        ('complex', 'Комплексная'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Истекла'),
        ('void', 'Аннулирована'),
    ]
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='warranties')
    device_unit = models.ForeignKey(DeviceUnit, on_delete=models.CASCADE, related_name='warranties')
    warranty_type = models.CharField(max_length=20, choices=WARRANTY_TYPES, default='complex')
    duration_months = models.IntegerField(default=3)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    covered_works = models.ManyToManyField(RepairWork, blank=True)
    covered_parts = models.ManyToManyField(InstalledPart, blank=True)
    conditions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')


class WarrantyCase(models.Model):
    COST_SOURCES = [
        ('warranty', 'За счёт гарантии'),
        ('paid', 'Платно'),
        ('goodwill', 'Лояльность сервиса'),
    ]
    warranty = models.ForeignKey(Warranty, on_delete=models.CASCADE, related_name='cases')
    original_order = models.ForeignKey(RepairOrder, on_delete=models.PROTECT, related_name='warranty_claims')
    new_diagnosis = models.ForeignKey(Diagnosis, on_delete=models.PROTECT, related_name='warranty_cases')
    is_repeat = models.BooleanField(default=True)
    cost_source = models.CharField(max_length=20, choices=COST_SOURCES, default='warranty')
    decision = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class OrderEvent(models.Model):
    order = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='order_events')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)