from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name='python-issues',
        version= '1.0.0',
        description=(
            'Collects and saves issues from bugs.python.org'
        ),
        long_description=open('README.md').read(),
        author='HuangFuSL',
        author_email='huangfusl@outlook.com',
        maintainer='HuangFuSL',
        maintainer_email='huangfusl@outlook.com',
        license='MIT License',
        packages=find_packages(),
        platforms=["all"],
        url='',
        install_requires=['requests', 'beautifulsoup4']
    )
