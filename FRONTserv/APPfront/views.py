import requests
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def index_view(request):
    zms_token = ''
    try:
        r = requests.get(f'{settings.BACKEND_API_URL}/api/zms-token/', timeout=2)
        if r.ok:
            zms_token = r.json().get('token', '')
    except Exception:
        pass
    return render(request, 'index.html', {'zms_token': zms_token})


@csrf_exempt
def api_gateway_proxy(request, subpath):
    target_url = f'{settings.BACKEND_API_URL}/api/{subpath}'
    if request.META.get('QUERY_STRING'):
        target_url += f"?{request.META['QUERY_STRING']}"

    headers = {'Content-Type': 'application/json'}
    auth_header = request.headers.get('Authorization')
    if auth_header:
        headers['Authorization'] = auth_header

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.body if request.method in ['POST', 'PUT', 'PATCH'] else None,
            timeout=10
        )
        return HttpResponse(
            content=resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'application/json')
        )
    except requests.RequestException as e:
        return JsonResponse({'detail': f'Бэкенд недоступен (порт 8000): {str(e)}'}, status=502)