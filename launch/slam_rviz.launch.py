import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('agv_ros')
    pkg_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    source_rviz_config = os.path.join(pkg_root, 'config', 'slam_hexagon.rviz')
    installed_rviz_config = os.path.join(pkg_share, 'config', 'slam_hexagon.rviz')
    default_rviz_config = source_rviz_config if os.path.exists(source_rviz_config) else installed_rviz_config

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config,
        description='RViz config file for SLAM'
    )

    set_domain = SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='24')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        output='screen',
    )

    return LaunchDescription([
        rviz_config_arg,
        set_domain,
        rviz_node,
    ])
