def subdomain(request):
    # Populate the subdomain in the template
    return {'subdomain':request.subdomain}