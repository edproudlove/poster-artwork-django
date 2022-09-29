from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.PosterModel)
admin.site.register(models.LiveOrder)
admin.site.register(models.OrderItem)
admin.site.register(models.Customer)
admin.site.register(models.PaidOrder)
admin.site.register(models.Artist)


