============
Installation
============

The easiest way at the moment is to use the provided buildout:

0. Install mercurial::

    $ easy_install mercurial

1. Get the buildout::

    hg clone http://bitbucket.org/diefenbach/lfc-buildout-development/

2. Execute the buildout::

    $ cd lfc-buildout-development
    $ python bootstrap
    $ bin/buildout -v

3. Start the server::

    $ bin/django runserver

4. Login::

    http://localhost:8000/login/ (admin/admin)

5. Go to the management interface::

    http://localhost:8000/manage/
