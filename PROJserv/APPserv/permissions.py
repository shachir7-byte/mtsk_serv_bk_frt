from rest_framework.permissions import BasePermission


class IsEmployeeOrStaffPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(request.user, 'employee_profile'):
            employee = request.user.employee_profile
            if employee.role == 'admin':
                return True
            if hasattr(obj, 'terminal'):
                return employee.terminals.filter(id=obj.terminal_id).exists()
        return False