from django.db import models
from users.models import User


class Notification(models.Model):
    '''
    작성자 : 장소은
    내용 : 사용자의 알림 레코드
    작성일 : 2023.06.22
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    participant = models.ForeignKey(
        'campaigns.Participant',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    restock = models.ForeignKey(
        'shop.RestockNotification',
        on_delete=models.CASCADE,
        related_name='restock_notification',
        null=True,
        blank=True
    )
    message = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.message}"
