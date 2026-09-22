from setuptools import setup, find_packages

setup(
    name='kaix',
    version='0.0.1',
    description='Mars 2.0 Frontend App',
    author='Marsbazaar.com',
    author_email='info@marsbazaar.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['frappe'],
)
