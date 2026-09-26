from django.utils import translation

class AppPreferencesMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Get the language from request headers, set default English
        language = request.headers.get('Accept-Language','en').lower()

        # Activate language if it is supported by our e-commerce store
        if language in ['ar','en']:
            translation.activate(language)
            request.language = language
        else:
            translation.activate('en')
            request.language = 'en'

        response = self.get_response(request)

        # Clean up and deactivate translation after processing the request
        translation.deactivate()
        return response

        