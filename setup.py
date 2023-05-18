from setuptools import setup, find_packages

VERSION = '2023.03.18'
DESCRIPTION = 'A Python package to reverse image search in Google Lens'
LONG_DESCRIPTION = 'A Python package to reverse image search in Google Lens, with the ability to search by file path or by url.'

setup(
    name="google-lens-python",
    version=VERSION,
    author="Anhy Krishna Fitiavana",
    author_email="fitiavana.krishna@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests', 'bs4'],
    keywords=['python', 'google', 'scraping'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)