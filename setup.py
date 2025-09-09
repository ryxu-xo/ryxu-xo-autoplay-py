"""
Setup script for ryxu-xo-autoplay Python package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ryxu-xo-autoplay",
    version="1.0.0",
    author="ryxu-xo",
    description="A high-performance autoplay API for Lavalink clients with source-to-source continuity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryxu-xo/ryxu-xo-autoplay",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "asyncio",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="lavalink, autoplay, music, discord, bot, youtube, spotify, soundcloud",
    project_urls={
        "Bug Reports": "https://github.com/ryxu-xo/ryxu-xo-autoplay/issues",
        "Source": "https://github.com/ryxu-xo/ryxu-xo-autoplay",
    },
)
