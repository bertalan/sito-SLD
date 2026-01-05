from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.http import HttpResponse

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.contrib.sitemaps.views import sitemap

from search import views as search_views
from django.views.generic import TemplateView
from .views import privacy_view, terms_view, custom_404_view, custom_403_view, custom_500_view, legacy_redirect_view

# Custom error handlers
handler403 = custom_403_view
handler404 = custom_404_view
handler500 = custom_500_view


def robots_txt(request):
    """Genera robots.txt dinamicamente."""
    # Ottieni il dominio corrente
    protocol = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    sitemap_url = f"{protocol}://{host}/sitemap.xml"
    
    # RSS Feed URL dinamico
    feed_line = ""
    try:
        from articles.models import ArticleIndexPage
        article_index = ArticleIndexPage.objects.live().first()
        if article_index:
            feed_url = f"{protocol}://{host}{article_index.url}feed/"
            feed_line = f"\n# RSS Feed\n# {feed_url}"
    except Exception:
        pass
    
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /prenota/checkout/",
        "",
        f"Sitemap: {sitemap_url}",
        feed_line,
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("prenota/", include("booking.urls")),
    path("termini/", terms_view, name="terms"),
    path("privacy/", privacy_view, name="privacy"),
    path("sitemap.xml", sitemap, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    # Legacy redirect: intercetta vecchie URL /it/* e /en/* ed estrae keyword per ricerca
    path("it/", legacy_redirect_view, name="legacy_redirect_root_it"),
    path("it/<path:path>", legacy_redirect_view, name="legacy_redirect_it"),
    path("en/", legacy_redirect_view, name="legacy_redirect_root_en"),
    path("en/<path:path>", legacy_redirect_view, name="legacy_redirect_en"),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
