"""
Middleware для автоматичного визначення Person з User
"""

from oids.models import Person


class PersonMiddleware:
    """
    Додає атрибут person до request для залогованих користувачів
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Додаємо person до request
        if request.user.is_authenticated:
            try:
                request.person = Person.objects.select_related('user').get(user=request.user)
            except Person.DoesNotExist:
                request.person = None
        else:
            request.person = None
        
        response = self.get_response(request)
        return response