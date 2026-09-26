class TranslationMixin:

    def resolve_translated_value(self, obj, field_base_name):

        # Get the current user language from the request context
        request = self.context.get('request')
        language = getattr(request, 'language', 'en')

        # Build the targeted database field name
        target_field = f"{field_base_name}_{language}"

        # Return the localized field value, fallback to English if missing
        return getattr(obj, target_field, getattr(obj, f"{field_base_name}_en", ""))
