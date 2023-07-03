from django.db import models


class BaseModel(models.Model):
    """
    작성자 : 최준영
    내용 : created_at과 updated_at을 상속시킬 추상화 클래스입니다.
    최초 작성일 : 2023.06.07
    업데이트 일자 : 2023.07.03
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        