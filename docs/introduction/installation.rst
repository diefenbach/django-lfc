============
Installation
============

For Users
=========

The easiest way is to use the provided installer:

1. Download the installer

   http://pypi.python.org/packages/source/d/django-lfc/django-lfc-installer-1.0a8.tar.gz
   
2. Unpack the tarball::

    $ tar xzf django-lfc-installer-1.0a8.tar.gz
    
3. Execute the buildout::

    $ cd lfc-installer
    $ python bootstrap
    $ bin/buildout -v

4. Start the server::

    $ bin/django runserver

5. Login::

    http://localhost:8000/login/ (admin/admin)

6. Go to the management interface::

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

4. Start the server::

    $ bin/django runserver

5. Login::

    http://localhost:8000/login/ (admin/admin)

6. Go to the management interface::

    http://localhost:8000/manage/
