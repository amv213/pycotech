import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="pycotech",
    version="0.2.0",
    description="Tools and wrappers to interface with PT-104 PicoLog® Data "
                "Loggers and files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Alvise Vianello",
    author_email="alvise@vianello.ai",
    url="https://gitlab.com/amv213/pycotech",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later " 
        "(GPLv3+)",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Science/Research",
        "Operating System :: Microsoft :: Windows",
        ],
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'matplotlib',
        'pandas',
        'pyyaml',
        'setuptools',
    ],
    extras_require={
        "doc": [
            'myst-parser',
            'sphinx',
            'sphinx-book-theme',
            'sphinx-copybutton',
            'sphinx-togglebutton',
            'sphinx-panels',
        ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['plw-player=pycotech.plw_player:main',
                            'plw-recorder=pycotech.plw_recorder:main'],
    }
)

# to build the package run the following:
# python setup.py sdist bdist_wheel
# twine check dist/*
