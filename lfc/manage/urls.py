# django imports
from django.conf.urls.defaults import *

# LFC Manage
urlpatterns = patterns('lfc.manage.views',
    url(r'^filebrowser$', "filebrowser", name="lfc_filebrowser"),
    url(r'^fb-upload-image$', "fb_upload_image", name="lfc_fb_upload_image"),
    url(r'^fb-upload-file$', "fb_upload_file", name="lfc_fb_upload_file"),
    
    url(r'^add-object/(?P<id>\w+)$', "add_object", name="lfc_add_object"),
    url(r'^add-object$', "add_object", name="lfc_add_top_object"),
    url(r'^add-object/(?P<language>\w+)/(?P<id>\w+)$', "add_object", name="lfc_add_object"),
    
    url(r'^delete-object/(?P<id>\d+)$', "delete_object", name="lfc_delete_object"),
    url(r'^save-core-data/(?P<id>\d+)$', "core_data", name="lfc_save_core_data"),
    url(r'^save-meta-data/(?P<id>\d+)$', "meta_data", name="lfc_save_meta_data"),
    url(r'^save-seo/(?P<id>\d+)$', "manage_seo", name="lfc_save_seo"),
    
    url(r'^add-images/(?P<id>\d+)$', "add_images", name="lfc_add_images"),
    url(r'^page-images/(?P<id>\d+)$', "images", name="lfc_images"),
    url(r'^update-images/(?P<id>\d+)$', "update_images", name="lfc_update_images"),
    
    url(r'^add-files/(?P<id>\d+)$', "add_files", name="lfc_add_files"),
    url(r'^page-files/(?P<id>\d+)$', "files", name="lfc_files"),
    url(r'^update-files/(?P<id>\d+)$', "update_files", name="lfc_update_files"),
    
    url(r'^update-comments/(?P<id>\d+)$', "update_comments", name="lfc_update_comments"),
    
    url(r'^dashboard$', "dashboard", name="lfc_manage_dashboard"),
    url(r'^portal$', "portal", name="lfc_manage_portal"),
    url(r'^save-portal-core$', "portal_core", name="lfc_save_portal_core"),
    
    url(r'^add-portlet/(?P<object_type_id>\d+)/(?P<object_id>\d+)$', "add_portlet", name="lfc_add_portlet"),
    url(r'^update-portlets/(?P<object_type_id>\d+)/(?P<object_id>\d+)$', "update_portlets", name="lfc_update_portlets"),
    url(r'^delete-portlet/(?P<portletassignment_id>\d+)$', "delete_portlet", name="lfc_delete_portlet"),
    url(r'^edit-portlet/(?P<portletassignment_id>\d+)$', "edit_portlet", name="lfc_edit_portlet"),
    
    url(r'^save-translation', "save_translation", name="lfc_save_translation"),
    url(r'^(?P<id>\d+)/translate/(?P<language>\w{2})', "translate_object", name="lfc_translate_object"),

    url(r'^$', "manage_objects", name="lfc_manage_objects"),
    url(r'^pages/?$', "manage_objects", name="lfc_manage_objects"),
    url(r'^(?P<id>\d+)$', "manage_object", name="lfc_manage_object"),
)
