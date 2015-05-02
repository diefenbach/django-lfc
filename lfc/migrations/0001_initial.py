# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import lfc.fields.thumbs
from django.conf import settings
import django.db.models.deletion
import permissions
import workflows
import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflows', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='BaseContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_type', models.CharField(max_length=100, verbose_name='Content type', blank=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('display_title', models.BooleanField(default=True, verbose_name='Display title')),
                ('slug', models.SlugField(max_length=100, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('position', models.PositiveSmallIntegerField(default=1, verbose_name='Position')),
                ('language', models.CharField(default=b'0', max_length=10, verbose_name='Language', choices=[(b'0', 'Neutral'), (b'en', 'English'), (b'de', 'German')])),
                ('tags', tagging.fields.TagField(max_length=255, verbose_name='Tags', blank=True)),
                ('order_by', models.CharField(default=b'position', max_length=20, verbose_name='Order by', choices=[(b'position', 'Position ascending'), (b'-position', 'Position descending'), (b'publication_date', 'Publication date ascending'), (b'-publication_date', 'Publication date descending')])),
                ('exclude_from_navigation', models.BooleanField(default=False, verbose_name='Exclude from navigation')),
                ('exclude_from_search', models.BooleanField(default=False, verbose_name='Exclude from search results')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='Modification date')),
                ('publication_date', models.DateTimeField(null=True, verbose_name='Publication date', blank=True)),
                ('start_date', models.DateTimeField(null=True, verbose_name='Start date', blank=True)),
                ('end_date', models.DateTimeField(null=True, verbose_name='End date', blank=True)),
                ('meta_title', models.CharField(default=b'<portal_title> - <title>', max_length=100, verbose_name='Meta title')),
                ('meta_keywords', models.TextField(default=b'<tags>', verbose_name='Meta keywords', blank=True)),
                ('meta_description', models.TextField(default=b'<description>', verbose_name='Meta description', blank=True)),
                ('allow_comments', models.PositiveSmallIntegerField(default=1, verbose_name='Commentable', choices=[(1, 'Default'), (2, 'Yes'), (3, 'No')])),
                ('searchable_text', models.TextField(blank=True)),
                ('version', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('canonical', models.ForeignKey(related_name='translations', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Canonical', blank=True, to='lfc.BaseContent', null=True)),
                ('creator', models.ForeignKey(verbose_name='Creator', to=settings.AUTH_USER_MODEL, null=True)),
                ('parent', models.ForeignKey(related_name='children', verbose_name='Parent', blank=True, to='lfc.BaseContent', null=True)),
                ('standard', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Standard', blank=True, to='lfc.BaseContent', null=True)),
            ],
            options={
                'ordering': ['position'],
            },
            bases=(models.Model, workflows.WorkflowBase, permissions.PermissionBase),
        ),
        migrations.CreateModel(
            name='ContentTypeRegistration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(unique=True, max_length=100, verbose_name='Type', blank=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name', blank=True)),
                ('display_select_standard', models.BooleanField(default=True, verbose_name='Display select standard')),
                ('display_position', models.BooleanField(default=True, verbose_name='Display position')),
                ('global_addable', models.BooleanField(default=True, verbose_name='Global addable')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, blank=True)),
                ('slug', models.SlugField(max_length=100)),
                ('content_id', models.PositiveIntegerField(null=True, verbose_name='Content id', blank=True)),
                ('position', models.SmallIntegerField(default=999)),
                ('description', models.TextField(blank=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('file', models.FileField(upload_to=b'files')),
                ('content_type', models.ForeignKey(related_name='files', verbose_name='Content type', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=100, verbose_name='Action')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('obj', models.ForeignKey(related_name='content_objects', verbose_name='Content object', to='lfc.BaseContent')),
                ('user', models.ForeignKey(related_name='user', verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-creation_date',),
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title', blank=True)),
                ('slug', models.SlugField(max_length=100, verbose_name='Slug')),
                ('content_id', models.PositiveIntegerField(null=True, verbose_name='Content id', blank=True)),
                ('position', models.SmallIntegerField(default=999, verbose_name='Position')),
                ('caption', models.CharField(max_length=100, verbose_name='Caption', blank=True)),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('image', lfc.fields.thumbs.ImageWithThumbsField(upload_to=b'uploads')),
                ('content_type', models.ForeignKey(related_name='images', verbose_name='Content type', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='Portal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title', blank=True)),
                ('from_email', models.EmailField(max_length=254, verbose_name='From e-mail address')),
                ('notification_emails', models.TextField(verbose_name='Notification email addresses')),
                ('allow_comments', models.BooleanField(default=False, verbose_name='Allow comments')),
                ('standard', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name='Standard', blank=True, to='lfc.BaseContent', null=True)),
            ],
            bases=(models.Model, permissions.PermissionBase),
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('path', models.CharField(max_length=100)),
                ('children_columns', models.IntegerField(default=1, verbose_name='Subpages columns')),
                ('images_columns', models.IntegerField(default=1, verbose_name='Images columns')),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='WorkflowStatesInformation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('public', models.BooleanField(default=False)),
                ('review', models.BooleanField(default=False)),
                ('state', models.ForeignKey(to='workflows.State')),
            ],
        ),
        migrations.AddField(
            model_name='contenttyperegistration',
            name='default_template',
            field=models.ForeignKey(verbose_name='Default template', blank=True, to='lfc.Template', null=True),
        ),
        migrations.AddField(
            model_name='contenttyperegistration',
            name='subtypes',
            field=models.ManyToManyField(to='lfc.ContentTypeRegistration', verbose_name='Allowed sub types', blank=True),
        ),
        migrations.AddField(
            model_name='contenttyperegistration',
            name='templates',
            field=models.ManyToManyField(related_name='content_type_registrations', verbose_name='Templates', to='lfc.Template'),
        ),
        migrations.AddField(
            model_name='contenttyperegistration',
            name='workflow',
            field=models.ForeignKey(verbose_name='Workflow', blank=True, to='workflows.Workflow', null=True),
        ),
        migrations.AddField(
            model_name='basecontent',
            name='template',
            field=models.ForeignKey(verbose_name='Template', blank=True, to='lfc.Template', null=True),
        ),
        migrations.AddField(
            model_name='basecontent',
            name='working_copy_base',
            field=models.ForeignKey(related_name='working_copies', on_delete=django.db.models.deletion.SET_NULL, verbose_name='Working copy base', blank=True, to='lfc.BaseContent', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='basecontent',
            unique_together=set([('parent', 'slug', 'language')]),
        ),
    ]
