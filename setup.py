"""
Setup script for DXVK Manager Tool
Allows installation via: pip install .
Or from GitHub: pip install git+https://github.com/xRetr000/DXVK-Manager.git
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle platform-specific dependencies
                    if ';' in line:
                        # For platform-specific deps like pyelftools, include base requirement
                        base_req = line.split(';')[0].strip()
                        if base_req:
                            requirements.append(base_req)
                    else:
                        requirements.append(line)
    return requirements

setup(
    name='dxvk-manager',
    version='1.0.0',
    description='A cross-platform tool for automatically installing and managing DXVK files for games',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='xRetr000',
    author_email='xretrocs@gmail.com',
    url='https://github.com/xRetr000/DXVK-Manager',
    packages=find_packages(),
    py_modules=['dxvk_manager', 'gui', 'exe_analyzer', 'github_downloader', 
                'file_manager', 'logger', 'platform_utils'],
    install_requires=[
        'pefile>=2023.2.7',
        'requests>=2.31.0',
        'PyQt6>=6.6.0',
    ],
    extras_require={
        'linux': ['pyelftools>=0.29'],
    },
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'dxvk-manager=dxvk_manager:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment',
        'Topic :: System :: Hardware',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    keywords='dxvk gaming vulkan directx wine linux windows',
    project_urls={
        'Bug Reports': 'https://github.com/xRetr000/DXVK-Manager/issues',
        'Source': 'https://github.com/xRetr000/DXVK-Manager',
        'Documentation': 'https://github.com/xRetr000/DXVK-Manager#readme',
    },
)

