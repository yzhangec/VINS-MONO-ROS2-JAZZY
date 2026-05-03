# SPDX-License-Identifier: BSD-3-Clause
# Single launch: EuRoC-style VINS-MONO stack (feature_tracker + RViz, vins_estimator + pose_graph).
# Optional: delayed ros2 bag play, benchmark ground-truth publisher.
#
# Examples:
#   ros2 launch vins_estimator vins_euroc_bringup.launch.py
#   ros2 launch vins_estimator vins_euroc_bringup.launch.py \\
#     play_bag:=true bag_path:=/path/to/MH_01_easy_ros2
#   ros2 launch vins_estimator vins_euroc_bringup.launch.py \\
#     with_benchmark:=true sequence_name:=MH_01_easy

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _setup_delayed_bag(context, *args, **kwargs):
    """Start bag playback after a short delay so subscribers are ready."""
    if context.launch_configurations.get('play_bag', 'false').lower() not in (
        'true',
        '1',
        'yes',
    ):
        return []
    delay_str = context.launch_configurations.get('bag_delay_sec', '3.0')
    try:
        delay = float(delay_str)
    except ValueError:
        delay = 3.0
    return [
        TimerAction(
            period=delay,
            actions=[
                LogInfo(
                    msg=[
                        '[vins_euroc_bringup] Playing bag: ',
                        LaunchConfiguration('bag_path'),
                    ]
                ),
                ExecuteProcess(
                    cmd=[
                        'ros2',
                        'bag',
                        'play',
                        LaunchConfiguration('bag_path'),
                    ],
                    output='screen',
                ),
            ],
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'play_bag',
                default_value='false',
                description="If 'true', runs ros2 bag play <bag_path> after bag_delay_sec.",
            ),
            DeclareLaunchArgument(
                'bag_path',
                default_value='',
                description='Absolute path to a ROS 2 bag directory (metadata.yaml inside).',
            ),
            DeclareLaunchArgument(
                'bag_delay_sec',
                default_value='3.0',
                description='Seconds to wait before starting bag playback.',
            ),
            DeclareLaunchArgument(
                'with_benchmark',
                default_value='false',
                description="If 'true', includes benchmark_publisher (EuRoC CSV ground truth).",
            ),
            DeclareLaunchArgument(
                'sequence_name',
                default_value='MH_01_easy',
                description='EuRoC sequence name (folder under benchmark_publisher/config/).',
            ),
            LogInfo(
                msg=(
                    '[vins_euroc_bringup] Starting feature_tracker+RViz and '
                    'vins_estimator+pose_graph (EuRoC config).'
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare('feature_tracker'),
                            'launch',
                            'vins_feature_tracker.launch.py',
                        ]
                    )
                )
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare('vins_estimator'),
                            'launch',
                            'euroc.launch.py',
                        ]
                    )
                )
            ),
            GroupAction(
                condition=IfCondition(LaunchConfiguration('with_benchmark')),
                actions=[
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            PathJoinSubstitution(
                                [
                                    FindPackageShare('benchmark_publisher'),
                                    'launch',
                                    'benchmark_publisher.launch.py',
                                ]
                            )
                        ),
                        launch_arguments=[
                            ('sequence_name', LaunchConfiguration('sequence_name')),
                        ],
                    ),
                    LogInfo(msg='[vins_euroc_bringup] Included benchmark_publisher.'),
                ],
            ),
            OpaqueFunction(function=_setup_delayed_bag),
        ]
    )
