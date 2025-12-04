"""
PlayerGold Setup Script
"""

from setuptools import setup, find_packages

setup(
    name="playergold",
    version="0.1.0",
    description="PlayerGold - Distributed AI Nodes Architecture for Gaming Blockchain",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="PlayerGold Team",
    author_email="dev@playergold.com",
    url="https://github.com/playergold/playergold",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "cryptography>=41.0.0",
        "ecdsa>=0.18.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "structlog>=23.1.0",
        "websockets>=11.0.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "tqdm>=4.65.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "playergold=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)