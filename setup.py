import setuptools

with open('README.md', mode='r', encoding='utf-8') as readme_file:
    long_description = readme_file.read()


setuptools.setup(
    name="lad-cli",
    version="1.0.1",
    author="Florian Wahl",
    author_email="florian.wahl.developer@gmail.com",
    description="A cli script to detect and list files including Alternate Data Streams under linux using the getfattr command.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wahlflo/lad",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
    install_requires=[
       'cli-formatter>=1.0.0',
       'python-dateutil>=2.8.1',
       'psutil>=5.7.0'
    ],
    entry_points={
        "console_scripts": [
            "lad=list_all_data.cli_script:main",
            "listAllData=list_all_data.cli_script:main"
        ],
    }
)