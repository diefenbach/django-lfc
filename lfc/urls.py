# django imports
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

# tagging imports
from tagging.views import tagged_object_list

# lfc imports
from lfc.forms import ContactForm
from lfc.feeds import PageTagFeed
from lfc.models import Page
from lfc.sitemap import PageSitemap

# Tags
urlpatterns = patterns("lfc.views",
    url(r'tag/(?P<slug>[-\w]+)/(?P<tag>[^/]+)/$', "lfc_tagged_object_list", name="page_tag_detail"),
)

# Comments
urlpatterns += patterns("",
    (r'^comments/', include('django.contrib.comments.urls')),
)

# Login / Logout
urlpatterns += patterns('django.contrib.auth.views',
    url('^login/?$',  "login",  { "template_name" : "lfc/login.html" },  name='lfc_login'),
    url('^logout/?$', "logout", { "template_name" : "lfc/logged_out.html" }, name='lfc_logout'),
)

# Feeds
feeds = {
    "rss" : PageTagFeed,
}

urlpatterns += patterns('',
    url(r'(?P<url>rss.*)$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name="feed"),
)

# Contact form
urlpatterns += patterns('contact_form.views',
    url(r'^contact$', "contact_form", { "form_class" : ContactForm }, name='contact_form'),
    url(r'^sent$', direct_to_template, { 'template': 'contact_form/contact_form_sent.html' }, name='contact_form_sent'),
)

# Sitemaps
urlpatterns += patterns("django.contrib.sitemaps.views",
    url(r'^sitemap.xml', 'sitemap', {'sitemaps': {"pages": PageSitemap}})
)

# Robots
urlpatterns += patterns('django.views.generic.simple',
    (r'^robots.txt', 'direct_to_template', {'template': 'lfc/robots.txt'}),
)

# LFC
urlpatterns += patterns('lfc.views',
    url(r'^(?P<language>[-\w]{2})/search-results', "search_results", name="lfc_search"),
    url(r'^search-results', "search_results", name="lfc_search"),

    url(r'^set-language/(?P<language>[-\w]{2})/$', 'set_language', name="lfc_set_language"),
    url(r'^set-language/(?P<language>[-\w]{2})/(?P<id>\d+)/$', 'set_language', name="lfc_set_language"),

    url(r'^do-transition/(?P<id>\d+)/$', 'do_transition', name="lfc_do_transition"),

    url(r'^file/(?P<id>[-\w]*)', "file", name="lfc_file"),

    url(r'^(?P<language>[-\w]{2})$', "base_view", name="lfc_base_view"),
    url(r'^(?P<language>[-\w]{2})/(?P<slug>.*)', "base_view", name="lfc_base_view"),
    url(r'^(?P<slug>.*)$', "base_view", name="lfc_base_view"),
    url(r'^$', "base_view", name="lfc_base_view"),
)
