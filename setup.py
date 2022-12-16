import setuptools

setuptools.setup(
    name='clarkstamp',
    version='0.1.0',
    author='Justin Wong',
    author_email='jkwongfl@yahoo.com',
    description='A TUI for interactive media playback and timestamping, using MPV.',
    packages=setuptools.find_packages(),
    install_requires=['blessed', 'docopt', 'python-mpv'],
    entry_points={'console_scripts': ['clark=clarkstamp.clarkstamp:run_cli']},
    python_requires='>=3.7',
)
