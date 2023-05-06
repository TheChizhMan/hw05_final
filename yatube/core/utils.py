from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone


def year(request):
    current_year = timezone.now().year
    return {
        'year': current_year,
    }


def paginator(request, posts):
    paginator = Paginator(posts, settings.PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
