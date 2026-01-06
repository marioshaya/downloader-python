from setuptools import setup

setup(
    name='ytdl',
    version='1.0',
    py_modules=['yt_downloader'],
    install_requires=[
        'yt-dlp',
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'ytdl=yt_downloader:main',
        ],
    },
)
