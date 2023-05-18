from rest_framework.routers import DefaultRouter, Route


class CustomDefaultRouter(DefaultRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = ""
