from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'spear_gui'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    package_data={
        package_name: ['*.png', '*.ttf'],
    },
    include_package_data=True,
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UAlberta SPEAR',
    maintainer_email='software@spearrobotics.ca',
    description='SPEAR rover camera and operator interfaces',
    license='Proprietary',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'main_gui = spear_gui.main_gui:main',
            'camera_node = spear_gui.camera_node:main',
            'rover_camera_manager = spear_gui.rover_camera_manager:main',
            'current_motor_vals_gui = spear_gui.current_motor_vals_gui:main',
            'gps_mission_panel = spear_gui.gps_mission_panel:main',
        ],
    },
)
