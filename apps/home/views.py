from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import models

from account.utils import get_default_redirect
from account.models import OtherServiceInfo
from account.forms import SignupForm, LoginForm
from emailconfirmation.models import EmailAddress, EmailConfirmation

association_model = models.get_model('django_openid', 'Association')
if association_model is not None:
    from django_openid.models import UserOpenidAssociation

def direct(request):
    site = Site.objects.get_current()
    if request.META['HTTP_HOST'] == site.domain or request.META['HTTP_HOST'] == "localhost:8000":
        # The visitor has hit the main webpage, so redirect to /mypage/ 
        if request.user.is_authenticated():
            return render_to_response('js-remote/index.html', {}, context_instance=RequestContext(request))
        else:
            return render_to_response('home/unauthenticated.html', {"login_form": LoginForm(), "signup_form": SignupForm()}, context_instance=RequestContext(request))
    else: # It's a subdomain
        # Split the domain into it's parts, remove the main part of the domain 
        # from the requested host, and we're left with one variable: 'subdomain'.
        # We also strip out the 'www.' non web-savvy users often type 'www' in 
        # front of every website they visit, so let's not show them an error message!
        domain_parts = site.domain.split(".")
        domain = ".".join(domain_parts[1:])
        subdomain = request.META['HTTP_HOST'].replace(domain, '').replace('.', '').replace('www', '')
        return HttpResponseRedirect(reverse("profile_detail", subdomain))
    

