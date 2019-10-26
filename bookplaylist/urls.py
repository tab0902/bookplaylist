"""bookplaylist URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

admin.site.site_title = _('BookPlayList site admin')
admin.site.site_header = _('BookPlayList administration')
admin.site.index_title = _('Home')

urlpatterns = [
    path('admin/f8ebb747-e59e-4540-94ac-34714c847267/', admin.site.urls),
    path('', include('main.urls')),
    path('accounts/', include('accounts.urls')),
] + static(settings.CERT_URL, document_root=settings.CERT_ROOT)
