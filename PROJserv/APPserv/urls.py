from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    TerminalViewSet, EmployeeViewSet, ShiftViewSet, ClientViewSet,
    ClientContactViewSet, DeviceModelViewSet, DeviceUnitViewSet,
    DeviceBundleViewSet, ServiceViewSet, PartViewSet,
    StockItemViewSet, DonorViewSet, RepairOrderViewSet,
    DiagnosisViewSet, RepairWorkViewSet, InstalledPartViewSet,
    PaymentViewSet, DocumentViewSet, WarrantyViewSet,
    WarrantyCaseViewSet, async_supplier_check, seed_database,
    ManualServiceListView, ManualServiceDetailView
)

router = DefaultRouter()
router.register('terminals', TerminalViewSet)
router.register('employees', EmployeeViewSet)
router.register('shifts', ShiftViewSet)
router.register('clients', ClientViewSet)
router.register('client-contacts', ClientContactViewSet)
router.register('device-models', DeviceModelViewSet)
router.register('device-units', DeviceUnitViewSet)
router.register('device-bundles', DeviceBundleViewSet)
router.register('services', ServiceViewSet)
router.register('parts', PartViewSet)
router.register('stock-items', StockItemViewSet)
router.register('donors', DonorViewSet)
router.register('orders', RepairOrderViewSet)
router.register('diagnoses', DiagnosisViewSet)
router.register('repair-works', RepairWorkViewSet)
router.register('installed-parts', InstalledPartViewSet)
router.register('payments', PaymentViewSet)
router.register('documents', DocumentViewSet)
router.register('warranties', WarrantyViewSet)
router.register('warranty-cases', WarrantyCaseViewSet)

urlpatterns = [
    path('seed-database/', seed_database),
    path('async-supplier-check/', async_supplier_check),
    path('manual-services/', ManualServiceListView.as_view()),
    path('manual-services/<int:service_id>/', ManualServiceDetailView.as_view()),
] + router.get_urls()