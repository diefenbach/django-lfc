from setuptools import setup, find_packages
import os

version = '1.0.3'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()

setup(name='django-lfc',
      version=version,
      description='A CMS based on Django.',
      long_description=README,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      keywords='django lfc cms',
      author='Kai Diefenbach',
      author_email='kai.diefenbach@iqpp.de',
      url='http://www.iqpp.de',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'django-contact-form == 0.3',
        'django-pagination == 1.0.7',
        'django-portlets == 1.0',
        'django-workflows == 1.0.1',
        'tagging == 0.5',
        'feedparser == 4.1',
        'lfc_theme == 1.0',
      ],
      )
