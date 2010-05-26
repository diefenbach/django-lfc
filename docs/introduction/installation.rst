============
Installation
============

For Users
=========

The easiest way is to use the provided installer:

1. Download the installer

   http://pypi.python.org/packages/source/d/django-lfc/django-lfc-installer-1.0b1.tar.gz

2. Unpack the tarball::

    $ tar xzf django-lfc-installer-1.0b1.tar.gz

3. Execute the buildout::

    $ cd lfc-installer
    $ python bootstrap
    $ bin/buildout -v

4. Run the tests::

    $ bin/django test lfc

5. Start the server::

    $ bin/django runserver

6. Login::

    http://localhost:8000/login/ (admin/admin)

7. Go to the management interface::

    http://localhost:8000/manage/

For Developers
==============

This will checkout the latest versions within trunk.

1. Install mercurial::

    $ easy_install mercurial

2. Get the buildout::

    hg clone http://bitbucket.org/diefenbach/lfc-buildout-development/

3. Execute the buildout::

    $ cd lfc-buildout-development
    $ python bootstrap
    $ bin/buildout -v

4. Run the tests::

    $ bin/django test lfc

5. Start the server::

    $ bin/django runserver

6. Login::

    http://localhost:8000/login/ (admin/admin)

7. Go to the management interface::

    http://localhost:8000/manage/

Using a own database
====================

If you don't want to use the provided and prepared sqlite database you have to
do some further steps.

1. Change settings.py according to your database

2. Sync the database::

    $ bin/django syncdb

3. Initialize the database

 You can choose from two different setups:

 simple
     Creates default portlets, templates, content types and a simple
     workflow for a simple site::

      $ bin/django runscript lfc_initialize_simple

 portal
     Creates default portlets, templates, content types, roles and
     permissions and workflows for a larger portal::

      $ bin/django runscript lfc_initialize_portal