from glob import glob
import os

from setuptools import find_packages, setup


package_name = "ultimate_gps_ros2"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml", "README.md", "LICENSE"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
        (
            os.path.join("share", package_name, "udev"),
            glob("udev/*.rules.example"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="UAlberta SPEAR",
    maintainer_email="software@spearrobotics.ca",
    description=(
        "ROS 2 NMEA driver for the Adafruit Ultimate GPS Breakout V3"
    ),
    license="MIT",
    extras_require={"test": ["pytest"]},
    entry_points={
        "console_scripts": [
            "gps_serial_probe = ultimate_gps_ros2.serial_probe:main",
            "ultimate_gps_node = ultimate_gps_ros2.gps_node:main",
        ],
    },
)
