import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('agv_ros')
    pkg_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    default_world = os.path.join(pkg_share, 'worlds', 'hexagon.world')
    slam_params_file = os.path.join(pkg_share, 'config', 'slam_toolbox.yaml')
    default_map_base = os.path.join(pkg_root, 'maps', 'hexagon_slam_map')

    set_domain = SetEnvironmentVariable(name='ROS_DOMAIN_ID', value='24')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='Gazebo world file'
    )
    gui_arg = DeclareLaunchArgument('gui', default_value='true')
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz2 for monitoring SLAM'
    )
    x_pose_arg = DeclareLaunchArgument('x_pose', default_value='-2.0')
    y_pose_arg = DeclareLaunchArgument('y_pose', default_value='-0.5')
    z_pose_arg = DeclareLaunchArgument('z_pose', default_value='0.06')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='0.0')
    map_basename_arg = DeclareLaunchArgument(
        'map_basename',
        default_value=default_map_base,
        description='Base output path used by ros2 run nav2_map_server map_saver_cli -f <path>'
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

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params_file],
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'slam_rviz.launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    save_map_hint = LogInfo(
        msg=[
            'Khi quet map xong, mo terminal moi va chay: ',
            'export ROS_DOMAIN_ID=24 && ',
            'source ~/agv_ros/install/setup.bash && ',
            'ros2 run nav2_map_server map_saver_cli -f ',
            LaunchConfiguration('map_basename'),
        ]
    )

    navigation_hint = LogInfo(
        msg=[
            'Sau khi luu map, chay navigation bang lenh: ',
            'export ROS_DOMAIN_ID=24 && ',
            'source ~/agv_ros/install/setup.bash && ',
            'ros2 launch agv_ros navigation_hexagon.launch.py map:=',
            LaunchConfiguration('map_basename'),
            '.yaml',
        ]
    )

    return LaunchDescription([
        world_arg,
        gui_arg,
        use_rviz_arg,
        x_pose_arg,
        y_pose_arg,
        z_pose_arg,
        yaw_arg,
        map_basename_arg,
        set_domain,
        sim_launch,
        slam_node,
        rviz_launch,
        save_map_hint,
        navigation_hint,
    ])
