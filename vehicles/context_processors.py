from .models import Brand


def brands_processor(request):
    return {'footer_brands': Brand.objects.all()[:6]}
