import setuptools

setuptools.setup(
    name='clark-mpv',
    version='0.2.0',
    author='Justin Wong',
    author_email='justin@wonger.dev',
    description='A TUI for media playback and timestamping, using MPV.',
    packages=setuptools.find_packages(),
    install_requires=['blessed', 'docopt', 'python-mpv'],
    entry_points={'console_scripts': ['clark=clark.main:run_cli']},
    python_requires='>=3.7',
)
