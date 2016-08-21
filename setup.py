from setuptools import find_packages, setup
import os

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst', 'md')
except(IOError, ImportError):
    long_description = open('README.md').read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-niji',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='A pluggable forum APP for Django',
    long_description=long_description,
    url='https://github.com/ericls/niji',
    author='Shen Li',
    author_email='dustet@gmail.com',
    install_requires=[
        "Django>=1.8.1,<1.11",
        "mistune>=0.7.3",
        "celery>=3.1",
        "redis",
        "django-crispy-forms",
        "six",
        "Pillow",
        "xxhash==0.6.1",
        "djangorestframework",
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)