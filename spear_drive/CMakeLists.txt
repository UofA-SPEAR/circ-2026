cmake_minimum_required(VERSION 3.8)
project(spear_drive)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion)
endif()

find_package(ament_cmake REQUIRED)
find_package(controller_interface REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(realtime_tools REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)

add_library(spear_drive_core SHARED
  src/drive_core.cpp
  src/fault_manager.cpp
)
target_compile_features(spear_drive_core PUBLIC cxx_std_17)
target_include_directories(spear_drive_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

add_library(spear_drive_controller SHARED
  src/drive_controller.cpp
)
target_compile_features(spear_drive_controller PUBLIC cxx_std_17)
target_include_directories(spear_drive_controller PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(spear_drive_controller spear_drive_core)
ament_target_dependencies(spear_drive_controller
  controller_interface
  diagnostic_msgs
  geometry_msgs
  hardware_interface
  nav_msgs
  pluginlib
  rclcpp
  rclcpp_lifecycle
  realtime_tools
  sensor_msgs
  std_srvs
)

add_executable(drive_teleop src/drive_teleop.cpp)
target_compile_features(drive_teleop PUBLIC cxx_std_17)
target_include_directories(drive_teleop PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_link_libraries(drive_teleop spear_drive_core)
ament_target_dependencies(drive_teleop
  diagnostic_msgs
  geometry_msgs
  rclcpp
  sensor_msgs
)

pluginlib_export_plugin_description_file(
  controller_interface
  spear_drive_controller.xml
)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY config description launch DESTINATION share/${PROJECT_NAME})
install(FILES README.md DESTINATION share/${PROJECT_NAME})
install(
  TARGETS spear_drive_core spear_drive_controller drive_teleop
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  enable_testing()
  add_executable(test_drive_core test/test_drive_core.cpp)
  target_compile_features(test_drive_core PUBLIC cxx_std_17)
  target_include_directories(test_drive_core PRIVATE include)
  target_link_libraries(test_drive_core spear_drive_core)
  add_test(NAME test_drive_core COMMAND test_drive_core)
endif()

ament_export_include_directories(include)
ament_export_libraries(spear_drive_core)
ament_export_targets(export_${PROJECT_NAME})
ament_package()
