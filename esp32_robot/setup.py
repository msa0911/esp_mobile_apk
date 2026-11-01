from setuptools import setup

package_name = 'esp32_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot_developer',
    maintainer_email='developer@example.com',
    description='Wi-Fi TCP motor bridge for an ESP32 differential-drive robot',
    license='Apache-2.0',
    entry_points={'console_scripts': ['motor_bridge = esp32_robot.motor_bridge:main', 'keyboard_control = esp32_robot.keyboard_control:main', 'joystick_control = esp32_robot.joystick_control:main']},
)
