from django.contrib import admin
from .models import (
    Terminal, Employee, Shift, ClientTag, Client, ClientContact,
    ClientLegalInfo, DeviceModel, DeviceUnit, DeviceSnapshot,
    Service, Part, StockItem, RepairOrder, DeviceBundle,
    Diagnosis, RepairWork, InstalledPart, Donor, StockMovement,
    Payment, LedgerEntry, Document, Warranty, WarrantyCase, OrderEvent
)

admin.site.register(Terminal)
admin.site.register(Employee)
admin.site.register(Shift)
admin.site.register(ClientTag)
admin.site.register(Client)
admin.site.register(ClientContact)
admin.site.register(ClientLegalInfo)
admin.site.register(DeviceModel)
admin.site.register(DeviceUnit)
admin.site.register(DeviceSnapshot)
admin.site.register(Service)
admin.site.register(Part)
admin.site.register(StockItem)
admin.site.register(RepairOrder)
admin.site.register(DeviceBundle)
admin.site.register(Diagnosis)
admin.site.register(RepairWork)
admin.site.register(InstalledPart)
admin.site.register(Donor)
admin.site.register(StockMovement)
admin.site.register(Payment)
admin.site.register(LedgerEntry)
admin.site.register(Document)
admin.site.register(Warranty)
admin.site.register(WarrantyCase)
admin.site.register(OrderEvent)