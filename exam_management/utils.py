from exam_management.models import Notification

def notificar(user, message):
    Notification.objects.create(user=user, message=message)