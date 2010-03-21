# django imports
from django.conf.urls.defaults import *

# LFC Manage
urlpatterns = patterns('lfc.manage.views',

    # applications
    url(r'^applications$', "applications", name="lfc_applications"),
    url(r'^install-application/(?P<name>\w+)$', "install_application", name="lfc_install_application"),
    url(r'^uninstall-application/(?P<name>\w+)$', "uninstall_application", name="lfc_uninstall_application"),
    url(r'^reinstall-application/(?P<name>\w+)$', "reinstall_application", name="lfc_reinstall_application"),
    
    # cut'n paste
    url(r'^copy/(?P<id>\d+)$', "lfc_copy", name="lfc_copy"),
    url(r'^cut/(?P<id>\d+)$', "cut", name="lfc_cut"),
    url(r'^paste/(?P<id>\d+)$', "paste", name="lfc_paste"),
    url(r'^paste$', "paste", name="lfc_paste"),
    
    # content types
    url(r'^content-types$', "content_types", name="lfc_content_types"),
    url(r'^content-type/(?P<id>\d+)$', "content_type", name="lfc_content_type"),
    
    # filebrowser
    url(r'^filebrowser$', "filebrowser", name="lfc_filebrowser"),
    url(r'^fb-upload-image$', "fb_upload_image", name="lfc_fb_upload_image"),
    url(r'^fb-upload-file$', "fb_upload_file", name="lfc_fb_upload_file"),
    
    # manage content
    url(r'^add-object/(?P<id>\w+)$', "add_object", name="lfc_add_object"),
    url(r'^add-object$', "add_object", name="lfc_add_top_object"),
    url(r'^add-object/(?P<language>\w+)/(?P<id>\w+)$', "add_object", name="lfc_add_object"),
    url(r'^delete-object/(?P<id>\d+)$', "delete_object", name="lfc_delete_object"),
    url(r'^save-core-data/(?P<id>\d+)$', "object_core_data", name="lfc_save_object_core_data"),
    url(r'^save-meta-data/(?P<id>\d+)$', "object_meta_data", name="lfc_save_meta_data"),
    url(r'^save-seo/(?P<id>\d+)$', "object_seo_data", name="lfc_save_seo"),
    
    # images
    url(r'^page-images/(?P<id>\d+)$', "object_images", name="lfc_images"),
    url(r'^add-images/(?P<id>\d+)$', "add_object_images", name="lfc_add_images"),
    url(r'^update-images/(?P<id>\d+)$', "update_object_images", name="lfc_update_images"),
    
    url(r'^portal-images$', "portal_images", name="lfc_portal_images"),
    url(r'^add-portal-images$', "add_portal_images", name="lfc_add_portal_images"),
    url(r'^update-portal-images$', "update_portal_images", name="lfc_update_portal_images"),
    
    # files
    url(r'^object-files/(?P<id>\d+)$', "object_files", name="lfc_files"),
    url(r'^add-object-files/(?P<id>\d+)$', "add_object_files", name="lfc_add_files"),
    url(r'^update-object-files/(?P<id>\d+)$', "update_object_files", name="lfc_update_files"),

    url(r'^portal-files$', "portal_files", name="lfc_portal_files"),
    url(r'^add-portal-files$', "add_portal_files", name="lfc_add_portal_files"),
    url(r'^update-portal-files$', "update_portal_files", name="lfc_update_portal_files"),
    
    # comments
    url(r'^update-comments/(?P<id>\d+)$', "update_comments", name="lfc_update_comments"),
    
    # children
    url(r'^update-children/(?P<id>\d+)$', "update_object_children", name="lfc_update_object_children"),
    url(r'^update-portal-children$', "update_portal_children", name="lfc_update_portal_children"),
    
    # permissions
    url(r'^update-object-permissions/(?P<id>\d+)$', "update_object_permissions", name="lfc_update_object_permissions"),
    url(r'^update-portal-permissions$', "update_portal_permissions", name="lfc_update_portal_permissions"),

    # workflows
    url(r'^do-transition/(?P<id>\d+)$', "do_transition", name="lfc_do_transition"),

    url(r'^save-portal-core$', "portal_core", name="lfc_save_portal_core"),
    
    # portlets
    url(r'^add-portlet/(?P<object_type_id>\d+)/(?P<object_id>\d+)$', "add_portlet", name="lfc_add_portlet"),
    url(r'^update-portlets/(?P<object_type_id>\d+)/(?P<object_id>\d+)$', "update_portlets", name="lfc_update_portlets"),
    url(r'^delete-portlet/(?P<portletassignment_id>\d+)$', "delete_portlet", name="lfc_delete_portlet"),
    url(r'^edit-portlet/(?P<portletassignment_id>\d+)$', "edit_portlet", name="lfc_edit_portlet"),
    
    # translation
    url(r'^save-translation', "save_translation", name="lfc_save_translation"),
    url(r'^(?P<id>\d+)/translate/(?P<language>\w{2})', "translate_object", name="lfc_translate_object"),
    
    # navigation
    url(r'^set-navigation-tree-language/(?P<language>\w{2})', "set_navigation_tree_language", name="lfc_set_navigation_tree_language"),
    url(r'^set-template$', "set_template", name="lfc_set_template"),
    
    # content
    url(r'^$', "portal", name="lfc_manage_portal"),
    url(r'^(?P<id>\d+)$', "manage_object", name="lfc_manage_object"),
)
