from django.db import models
from django.contrib.auth import User

# Create your models here.
class CallbackURL(models.Model):
    user = models.ForeignKey(User)
    url = models.CharField(max_length=255)
    num_confirmations = models.IntegerField()

class Alert(models.Model):
    callback = models.ForeignKey(CallbackURL)
    activated = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    item = models.CharField(max_length=255)
    transaction = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    