import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('agv_ros')
    pkg_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config = os.path.join(pkg_share, 'config', 'navigation_hexagon.rviz')
    params_file = os.path.join(pkg_share, 'config', 'nav2_omni_params.yaml')
    default_world = os.path.join(pkg_share, 'worlds', 'hexagon.world')
    default_map = os.path.join(pkg_root, 'maps', 'hexagon_ground_truth.yaml')

    set_domain = SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='24')

    gui_arg = DeclareLaunchArgument('gui', default_value='true')
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false')
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='Gazebo world file'
    )
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='-4.0')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='-3.0')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.06')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='0.0')
    map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Absolute path to the saved map yaml file'
    )

    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gazebo_display.launch.py')
        ),
        launch_arguments={
            'world': LaunchConfiguration('world'),
            'gui': LaunchConfiguration('gui'),
            'ros_domain_id': '24',
            'use_rviz': 'false',
            'x_pose': LaunchConfiguration('x_pose'),
            'y_pose': LaunchConfiguration('y_pose'),
            'z_pose': LaunchConfiguration('z_pose'),
            'yaw': LaunchConfiguration('yaw'),
        }.items()
    )

    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'slam': 'False',
            'map': LaunchConfiguration('map'),
            'use_sim_time': 'True',
            'params_file': params_file,
            'autostart': 'True',
            'use_composition': 'False',
        }.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    return LaunchDescription([
        world_arg,
        gui_arg,
        use_rviz_arg,
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        yaw_arg,
        map_arg,
        set_domain,
        sim_launch,
        nav_launch,
        rviz_node,
    ])
