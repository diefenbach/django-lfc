from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name='django-lfc',
    version="1.2b3",
    description='A CMS based on Django.',
    long_description=README,
    classifiers=[
        'Development Status :: 4 - Beta',
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
        'django-compressor == 1.4',
        'django-pagination == 1.0.7',
        'django-workflows == 1.1.1',
        'lfc-contact-form == 1.0.1',
        'lfc-page == 1.0.1',
        'lfc-portlets == 1.2',
        'lfc-theme == 1.2.1',
        'Pillow == 2.5.0',
        'tagging == 0.5',
    ],
)
