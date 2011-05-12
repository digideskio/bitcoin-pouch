import urlparse

class subdomain:
    def process_request(self, request):
        bits = urlparse.urlsplit(request.META['HTTP_HOST'])[0].split('.')
        if not( len(bits) == 3):
            pass#Todo Raise an exception etc
        request.subdomain = bits[0]