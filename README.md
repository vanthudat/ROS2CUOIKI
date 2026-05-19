# ROS2CUOIKI - AGV Mecanum, SLAM va Navigation

Repo nay chua bai lam ROS 2 cho mo phong AGV 4 banh mecanum co tay may trong Gazebo, hien thi tren RViz, dieu khien bang ban phim, tao ban do bang SLAM Toolbox, chay Navigation2 va danh gia chat luong ban do.

Package chinh: `agv_ros`

## Noi dung da lam

- Xay dung mo hinh robot AGV tu `urdf/demo2.urdf`, gom khung xe, 4 banh mecanum, lidar, camera va tay may 2 khop.
- Cau hinh Gazebo + `ros2_control` de spawn robot, dieu khien van toc banh va dieu khien vi tri tay may.
- Viet node dieu khien dong hoc mecanum tu `/cmd_vel` sang `/wheel_velocity_controller/commands`.
- Viet teleop ban phim cho robot di tien/lui, ngang trai/phai, cheo va xoay tai cho.
- Viet teleop ban phim cho tay may qua `/arm_position_controller/commands`.
- Tao cac launch file cho mo phong, RViz, SLAM va Navigation2.
- Cau hinh SLAM Toolbox de quet map tu laser scan trong moi truong Gazebo.
- Cau hinh Navigation2 voi AMCL, map server, planner, controller va costmap cho robot omni/mecanum.
- Tao nhieu map thu nghiem trong `maps/` de so sanh anh huong cua cac tham so SLAM.
- Viet script danh gia ban do bang RMSE, error rate, Occupied IoU, Free IoU va tao bieu do trong `reports/`.

## Cau truc thu muc

```text
agv_ros/
|-- config/                 # Tham so controller, SLAM Toolbox, Nav2 va RViz
|-- launch/                 # Launch Gazebo, SLAM, Navigation va RViz
|-- maps/                   # Ban do PGM/YAML, anh so sanh va panel danh gia
|-- meshes/                 # File STL cua robot
|-- reports/                # Bang chi so va hinh tong hop ket qua SLAM
|-- Rviz/                   # Cau hinh RViz
|-- scripts/                # Node Python dieu khien va danh gia
|-- urdf/                   # Mo hinh URDF robot
`-- worlds/                 # World Gazebo
```

## Yeu cau moi truong

Du an duoc viet cho ROS 2 Humble tren Ubuntu, can cac goi chinh:

- `gazebo_ros`, `gazebo_plugins`, `gazebo_ros2_control`
- `robot_state_publisher`, `joint_state_publisher_gui`, `rviz2`
- `controller_manager`, `joint_state_broadcaster`
- `joint_trajectory_controller`, `position_controllers`, `velocity_controllers`
- `slam_toolbox`
- `nav2_bringup`, `nav2_map_server`
- Python packages cho danh gia map: `numpy`, `Pillow`, `scipy`, `matplotlib`, `pyyaml`

## Build workspace

Tu thu muc workspace:

```bash
cd ~/agv_ros
colcon build --symlink-install
source install/setup.bash
```

Neu chay nhieu terminal, moi terminal can source lai:

```bash
source /opt/ros/humble/setup.bash
source ~/agv_ros/install/setup.bash
export ROS_DOMAIN_ID=24
```

Package co env hook `env-hooks/fastdds_udp.sh.in` de uu tien FastDDS UDP va tranh loi shared memory trong mot so moi truong.

## Chay mo phong robot

Terminal 1: chay Gazebo va spawn robot:

```bash
ros2 launch agv_ros gazebo_display.launch.py
```

Terminal 2: mo RViz rieng de xem robot:

```bash
ros2 launch agv_ros display.launch.py
```

Chay world rieng:

```bash
ros2 launch agv_ros gazebo_display.launch.py world:=$(ros2 pkg prefix agv_ros)/share/agv_ros/worlds/hexagon.world
```

Thay doi vi tri spawn:

```bash
ros2 launch agv_ros gazebo_display.launch.py x_pose:=-4.0 y_pose:=-3.0 yaw:=0.0
```

## Dieu khien AGV mecanum

Sau khi Gazebo dang chay, mo terminal moi de chay teleop:

```bash
export ROS_DOMAIN_ID=24
source ~/agv_ros/install/setup.bash
ros2 run agv_ros mecanum_keyboard_teleop.py
```

Phim dieu khien:

```text
u  i  o   : cheo trai / tien / cheo phai
j  k  l   : trai / dung / phai
m  ,  .   : cheo lui trai / lui / cheo lui phai
a / d     : xoay trai / xoay phai
+ / -     : tang / giam toc do
r         : reset toc do
q         : thoat
```

Luong dieu khien:

```text
mecanum_keyboard_teleop.py
  -> /cmd_vel
  -> mecanum_drive_controller.py
  -> /wheel_velocity_controller/commands
  -> ros2_control trong Gazebo
```

## Dieu khien tay may

Chay mo phong voi controller tay may, sau do mo terminal moi:

```bash
export ROS_DOMAIN_ID=24
source ~/agv_ros/install/setup.bash
ros2 run agv_ros arm_teleop.py
```

Phim dieu khien:

```text
w / s : tang / giam goc Arm_joint2
a / d : tang / giam goc Arm_joint1
h     : ve vi tri home
q     : thoat
```

## SLAM Toolbox

Terminal 1: chay Gazebo + SLAM trong world `hexagon.world`:

```bash
ros2 launch agv_ros slam_hexagon.launch.py
```

Hoac chay Gazebo + SLAM trong world `house_scan.world`:

```bash
ros2 launch agv_ros slam_house_scan.launch.py
```

Terminal 2: mo RViz rieng de theo doi map, scan va TF:

```bash
ros2 launch agv_ros slam_rviz.launch.py
```

Sau khi dieu khien robot quet het moi truong, luu map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/agv_ros/maps/house_scan_map
```

File tham so SLAM nam o:

```text
config/slam_toolbox.yaml
```

Mot so tham so da khao sat:

- `minimum_travel_distance`
- `minimum_travel_heading`
- `resolution`
- `do_loop_closing`

## Navigation2

Terminal 1: chay Gazebo + Navigation2 voi map da luu:

```bash
ros2 launch agv_ros navigation_hexagon.launch.py map:=~/agv_ros/maps/house_mtd_030.yaml
```

Terminal 2: mo RViz rieng de dat goal va theo doi duong di:

```bash
ros2 launch agv_ros navigation_rviz.launch.py
```

Launch nay se:

- spawn robot trong Gazebo;
- nap map cho Nav2;
- chay AMCL voi `nav2_amcl::OmniMotionModel`;
- chay planner, controller va costmap.

File tham so Nav2:

```text
config/nav2_omni_params.yaml
```

## Danh gia ban do SLAM

Repo co ban do chuan:

```text
maps/house_scan_ground_truth.yaml
```

Va cac nhom map thu nghiem:

- `house_mtd_*`: khao sat `minimum_travel_distance`
- `house_mth_*`: khao sat `minimum_travel_heading`
- `house_res_*`: khao sat `resolution`
- `house_loop_on/off`: so sanh bat/tat loop closing

Chay danh gia:

```bash
python3 scripts/evaluate_slam_studies.py
python3 scripts/plot_slam_metrics.py
```

Ket qua:

- `reports/slam_map_metrics.csv`
- `reports/slam_map_metrics.md`
- `reports/figures/*.png`
- anh overlay so sanh trong `maps/*_paper_compare.png`

Chi so su dung:

- `RMSE`: sai so bien vat can theo khoang cach gan nhat hai chieu.
- `Error rate`: ti le o luoi khac nhau so voi map chuan.
- `Occupied IoU`: do trung khop vung vat can.
- `Free IoU`: do trung khop vung trong.
- `False occupied`: pixel bi danh dau vat can sai.
- `Missed occupied`: pixel vat can trong map chuan bi bo sot.

Theo bang hien co trong `reports/slam_map_metrics.md`, mot so nhan xet chinh:

- Bat loop closing tot hon ro ret so voi tat loop closing. Truong hop tat loop closing co RMSE lon va error rate cao.
- Nhom `resolution` cho thay `0.10 m` dat RMSE thap nhat trong cac map da thu.
- Khi tang `minimum_travel_distance` hoac `minimum_travel_heading` qua lon, chat luong map co xu huong giam vi robot cap nhat map thua hon.

## Cac file code quan trong

- `launch/gazebo_display.launch.py`: launch Gazebo, spawn robot va nap controller.
- `launch/display.launch.py`: mo robot_state_publisher, joint_state_publisher_gui va RViz de xem robot rieng.
- `launch/slam_hexagon.launch.py`: chay Gazebo + SLAM Toolbox trong world hexagon.
- `launch/slam_house_scan.launch.py`: chay SLAM trong world house scan.
- `launch/slam_rviz.launch.py`: mo RViz rieng cho SLAM.
- `launch/navigation_hexagon.launch.py`: chay Gazebo + Nav2 voi map da luu.
- `launch/navigation_rviz.launch.py`: mo RViz rieng cho Navigation2.
- `scripts/mecanum_drive_controller.py`: tinh toc do 4 banh mecanum tu `/cmd_vel`.
- `scripts/mecanum_keyboard_teleop.py`: teleop ban phim cho robot.
- `scripts/arm_teleop.py`: teleop ban phim cho tay may.
- `scripts/evaluate_maps.py`: tao overlay so sanh map voi map chuan.
- `scripts/evaluate_slam_studies.py`: tinh cac chi so SLAM cho tung nhom tham so.
- `scripts/plot_slam_metrics.py`: ve bieu do tong hop tu file CSV.

## Goi y quy trinh demo

1. Build workspace va source setup.
2. Chay `gazebo_display.launch.py` de mo Gazebo va spawn robot.
3. Chay `mecanum_keyboard_teleop.py` de dieu khien AGV.
4. Chay `arm_teleop.py` de dieu khien tay may.
5. Chay `display.launch.py`, `slam_rviz.launch.py` hoac `navigation_rviz.launch.py` khi can xem tren RViz.
6. Chay `slam_house_scan.launch.py` de quet map.
7. Luu map bang `map_saver_cli`.
8. Chay `navigation_hexagon.launch.py` voi map da luu.
9. Chay script danh gia map va xem ket qua trong `reports/`.

## Ghi chu

- Mac dinh cac launch SLAM/Nav2 dung `ROS_DOMAIN_ID=24`.
- Neu cac topic khong thay nhau, kiem tra lai `ROS_DOMAIN_ID` giua cac terminal.
- Neu Gazebo/RViz khong hien robot, build lai workspace va source `install/setup.bash`.
- Neu teleop khong co tac dung, kiem tra controller `/wheel_velocity_controller/commands` va topic `/cmd_vel`.
