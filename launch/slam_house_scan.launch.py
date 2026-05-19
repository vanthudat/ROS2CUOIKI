import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory('agv_ros')
    pkg_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    house_scan_world = os.path.join(pkg_share, 'worlds', 'house_scan.world')
    default_map_base = os.path.join(pkg_root, 'maps', 'house_scan_map')

    gui_arg = DeclareLaunchArgument('gui', default_value='true')
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz2 for monitoring SLAM'
    )
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='-4.0')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='-3.0')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.06')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='0.0')
    map_basename_arg = DeclareLaunchArgument(
        'map_basename',
        default_value=default_map_base,
        description='Base output path used by map_saver_cli -f <path>'
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'slam_hexagon.launch.py')
        ),
        launch_arguments={
            'world': house_scan_world,
            'gui': LaunchConfiguration('gui'),
            'x_pose': LaunchConfiguration('x_pose'),
            'y_pose': LaunchConfiguration('y_pose'),
            'z_pose': LaunchConfiguration('z_pose'),
            'yaw': LaunchConfiguration('yaw'),
            'map_basename': LaunchConfiguration('map_basename'),
        }.items()
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'slam_rviz.launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    return LaunchDescription([
        gui_arg,
        use_rviz_arg,
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        yaw_arg,
        map_basename_arg,
        slam_launch,
        rviz_launch,
    ])
