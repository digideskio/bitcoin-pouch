from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from bitcoind.models import Address

def what_next(request, extra_context={}):
    try:
        address = Address.objects.get(user=request.user, is_primary=True)
    except ObjectDoesNotExist:
        address = Address.objects.get(user=request.user)
        
    return render_to_response("about/what_next.html", dict({
        "address": address,
    }, **extra_context), context_instance=RequestContext(request))
