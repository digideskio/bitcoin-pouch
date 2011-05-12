def subdomain(request):
    "Populate the subdomain in the template"
    return {'subdomain':request.subdomain}#request.subdomain has been populated via the Middleware.