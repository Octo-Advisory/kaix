from setuptools import setup, find_packages
 
setup(
    name='frontend_app', 
    version='0.0.1',
    description='Mars 2 Custom App',
    author='Your Name',
    author_email='you@example.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['frappe'],
)
