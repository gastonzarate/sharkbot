from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the current site URL from the request
        request = self.request
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        context["api_base_url"] = f"{scheme}://{host}"
        return context
