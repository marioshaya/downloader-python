from setuptools import setup

setup(
    name='downloader',
    version='1.0',
    py_modules=['downloader'],
    install_requires=[
        'yt-dlp',
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'dwn=downloader:main',
        ],
    },
)
