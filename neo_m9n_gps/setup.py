from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'neo_m9n_gps'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml', 'README.md']),
        (
            os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml')),
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py')),
        ),
        (
            os.path.join('share', package_name, 'docs'),
            glob(os.path.join('docs', '*.md')),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UAlberta SPEAR',
    maintainer_email='spear@ualberta.ca',
    description='ROS 2 serial driver for the u-blox NEO-M9N-00B GNSS receiver.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'gps_node = neo_m9n_gps.gps_node:main',
            'gps_probe = neo_m9n_gps.serial_probe:main',
        ],
    },
)
