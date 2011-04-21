from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language_from_request, ugettext_lazy as _

from bitcoind import *
from bitcoind.util import getaccount

DEFAULT_ADDRESS_LABEL = ""

CATEGORY_CHOICES = (
    ("send", "Send"),
    ("receive", "Receive")
)
class Address(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    label = models.CharField(_('Label'), max_length=50)
    address = models.CharField(_('Address'), max_length=34)
    #balance = models.DecimalField(_('Balance'), max_digits=16, decimal_places=8, default=0)
    is_primary = models.BooleanField(_('Primary'), default=False)
    
    def __unicode__(self):
        return self.address
    
    def accountName(self):
        if self.label == "":
            return getaccount(self.user, self.label)
    
    '''
    def increase(self, amount):
        self.balance += amount
        
    def decrease(self, amount):
        self.balance -= amount
    '''
    
class Transaction(models.Model):
    account = models.ForeignKey(Address, verbose_name=_('Account'))
    address = models.CharField(_('Address'), max_length=50)
    category = models.CharField(_(""), choices=CATEGORY_CHOICES, max_length=7)
    amount = models.DecimalField(_('Amount'), max_digits=16, decimal_places=8)
    txid = models.CharField(_('TXID'), max_length=50)
    confirmations = models.IntegerField(_("Confirmations"), max_length=3, default=0)
    time = models.DateTimeField(_('Created'), auto_now_add=True)