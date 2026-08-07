#include "spear_drive/drive_controller.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <limits>
#include <utility>

#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_msgs/msg/key_value.hpp"
#include "geometry_msgs/msg/quaternion.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace spear_drive
{
namespace
{

constexpr double kPi = 3.14159265358979323846;
constexpr double kDriveEnabledControlWord = 6.0;
constexpr double kConfiguredEmbeddedCurrentLimitAmps = 3.0;
constexpr std::uint32_t kDriveEnabledStatusBit = 1U << 2;
constexpr char kControlWordInterface[] = "control_word";
constexpr char kCurrentInterface[] = "current";
constexpr char kDutyCycleInterface[] = "duty_cycle";
constexpr char kEncoderCountsInterface[] = "encoder_counts";
constexpr char kEncoderCountsPerSecondInterface[] = "encoder_counts_per_second";
constexpr char kStatusWordInterface[] = "status_word";

template<std::size_t Size>
bool copy_vector(
  const std::vector<double> & source,
  std::array<double, Size> & destination)
{
  if (source.size() != Size) {
    return false;
  }
  std::copy(source.begin(), source.end(), destination.begin());
  return true;
}

template<std::size_t Size>
bool copy_vector(
  const std::vector<std::string> & source,
  std::array<std::string, Size> & destination)
{
  if (source.size() != Size) {
    return false;
  }
  std::copy(source.begin(), source.end(), destination.begin());
  return true;
}

double clamp_current(double value, double maximum)
{
  return std::clamp(value, -std::abs(maximum), std::abs(maximum));
}

bool is_left_wheel(std::size_t index)
{
  return index == FRONT_LEFT || index == MIDDLE_LEFT || index == REAR_LEFT;
}

geometry_msgs::msg::Quaternion yaw_quaternion(double yaw)
{
  geometry_msgs::msg::Quaternion quaternion;
  quaternion.z = std::sin(yaw * 0.5);
  quaternion.w = std::cos(yaw * 0.5);
  return quaternion;
}

diagnostic_msgs::msg::KeyValue diagnostic_value(
  const std::string & key,
  const std::string & value)
{
  diagnostic_msgs::msg::KeyValue output;
  output.key = key;
  output.value = value;
  return output;
}

}  // namespace

SpearDriveController::SpearDriveController()
{
  drive_joints_ = {
    "front_left_drive_joint", "front_right_drive_joint",
    "middle_left_drive_joint", "middle_right_drive_joint",
    "rear_left_drive_joint", "rear_right_drive_joint"};
  steering_joints_ = {
    "front_left_steer_joint", "front_right_steer_joint",
    "rear_left_steer_joint", "rear_right_steer_joint"};
  last_traction_scale_.fill(1.0);
  last_valid_steering_.fill(std::numeric_limits<double>::quiet_NaN());
}

controller_interface::CallbackReturn SpearDriveController::on_init()
{
  try {
    auto_declare<std::vector<std::string>>(
      "drive_joints",
      {"front_left_drive_joint", "front_right_drive_joint",
        "middle_left_drive_joint", "middle_right_drive_joint",
        "rear_left_drive_joint", "rear_right_drive_joint"});
    auto_declare<std::vector<std::string>>(
      "steering_joints",
      {"front_left_steer_joint", "front_right_steer_joint",
        "rear_left_steer_joint", "rear_right_steer_joint"});
    auto_declare<std::vector<double>>(
      "wheel_x", {0.50, 0.50, 0.0, 0.0, -0.50, -0.50});
    auto_declare<std::vector<double>>(
      "wheel_y", {0.35, -0.35, 0.35, -0.35, 0.35, -0.35});
    auto_declare<std::vector<double>>("wheel_radius", std::vector<double>(6, 0.13));
    auto_declare<std::vector<double>>("drive_gear_ratio", std::vector<double>(6, 1.0));
    auto_declare<std::vector<double>>(
      "encoder_counts_per_motor_revolution", std::vector<double>(6, 28.0));
    auto_declare<std::vector<double>>(
      "drive_direction", {1.0, -1.0, 1.0, -1.0, 1.0, -1.0});
    auto_declare<std::vector<double>>(
      "steering_min", std::vector<double>(4, -0.78));
    auto_declare<std::vector<double>>(
      "steering_max", std::vector<double>(4, 0.78));
    auto_declare<std::vector<double>>("steering_gear_ratio", std::vector<double>(4, 1.0));
    auto_declare<std::vector<double>>(
      "steering_direction", {1.0, -1.0, 1.0, -1.0});
    auto_declare<std::vector<double>>("steering_offset", std::vector<double>(4, 0.0));

    auto_declare<double>("max_linear_speed", 0.5);
    auto_declare<double>("max_yaw_rate", 0.6);
    auto_declare<double>("max_wheel_angular_speed", 10.0);
    auto_declare<double>("max_linear_acceleration", 0.4);
    auto_declare<double>("max_linear_deceleration", 0.8);
    auto_declare<double>("max_yaw_acceleration", 0.8);
    auto_declare<double>("max_jerk", 2.0);
    auto_declare<double>("steering_alignment_soft", 0.08);
    auto_declare<double>("steering_alignment_hard", 0.25);
    auto_declare<double>("minimum_linear_for_turn", 0.03);
    auto_declare<bool>("allow_point_turn", false);

    auto_declare<double>("command_timeout", 0.30);
    auto_declare<double>("imu_timeout", 0.30);
    auto_declare<bool>("monitor_imu", false);
    auto_declare<bool>("auto_zero_on_activate", true);
    auto_declare<double>("velocity_kp", 0.35);
    auto_declare<double>("velocity_ki", 0.0);
    auto_declare<double>("velocity_feedforward", 0.0);
    auto_declare<double>("max_motor_current", 2.0);
    auto_declare<double>("integral_limit", 1.0);
    auto_declare<double>("yaw_feedback_gain", 0.25);
    auto_declare<double>("slip_ratio_threshold", 0.30);
    auto_declare<double>("slip_reference_speed", 0.30);
    auto_declare<double>("minimum_traction_scale", 0.25);
    auto_declare<double>("publish_rate", 20.0);
    auto_declare<std::vector<double>>(
      "pose_covariance_diagonal", {0.04, 0.04, 1000000.0, 1000000.0, 1000000.0, 0.09});
    auto_declare<std::vector<double>>(
      "twist_covariance_diagonal", {0.04, 0.04, 1000000.0, 1000000.0, 1000000.0, 0.09});
    auto_declare<std::string>("imu_topic", "~/imu");
    auto_declare<std::string>("odom_frame", "odom");
    auto_declare<std::string>("base_frame", "base_link");

    auto_declare<int>("minimum_healthy_drive_wheels", 4);
    auto_declare<int>("minimum_healthy_wheels_per_side", 2);
    auto_declare<double>("degraded_5wd_scale", 0.65);
    auto_declare<double>("degraded_4wd_scale", 0.35);
    auto_declare<double>("steering_limp_scale", 0.20);
    auto_declare<double>("steering_straight_tolerance", 0.15);
  } catch (const std::exception & error) {
    RCLCPP_ERROR(get_node()->get_logger(), "Parameter declaration failed: %s", error.what());
    return controller_interface::CallbackReturn::ERROR;
  }
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::InterfaceConfiguration
SpearDriveController::command_interface_configuration() const
{
  controller_interface::InterfaceConfiguration configuration;
  configuration.type = controller_interface::interface_configuration_type::INDIVIDUAL;
  for (const auto & joint : drive_joints_) {
    configuration.names.push_back(joint + "/" + kCurrentInterface);
    configuration.names.push_back(joint + "/" + kControlWordInterface);
  }
  for (const auto & joint : steering_joints_) {
    configuration.names.push_back(joint + "/" + hardware_interface::HW_IF_POSITION);
  }
  return configuration;
}

controller_interface::InterfaceConfiguration
SpearDriveController::state_interface_configuration() const
{
  controller_interface::InterfaceConfiguration configuration;
  configuration.type = controller_interface::interface_configuration_type::INDIVIDUAL;
  for (const auto & joint : drive_joints_) {
    configuration.names.push_back(joint + "/" + kEncoderCountsPerSecondInterface);
    configuration.names.push_back(joint + "/" + kEncoderCountsInterface);
    configuration.names.push_back(joint + "/" + kCurrentInterface);
    configuration.names.push_back(joint + "/" + kStatusWordInterface);
    configuration.names.push_back(joint + "/" + kDutyCycleInterface);
  }
  for (const auto & joint : steering_joints_) {
    configuration.names.push_back(joint + "/" + hardware_interface::HW_IF_POSITION);
  }
  return configuration;
}

bool SpearDriveController::load_parameters()
{
  const auto node = get_node();
  if (!copy_vector(node->get_parameter("drive_joints").as_string_array(), drive_joints_) ||
    !copy_vector(node->get_parameter("steering_joints").as_string_array(), steering_joints_) ||
    !copy_vector(node->get_parameter("wheel_x").as_double_array(), geometry_.wheel_x) ||
    !copy_vector(node->get_parameter("wheel_y").as_double_array(), geometry_.wheel_y) ||
    !copy_vector(node->get_parameter("wheel_radius").as_double_array(), geometry_.wheel_radius) ||
    !copy_vector(
      node->get_parameter("drive_gear_ratio").as_double_array(), geometry_.drive_gear_ratio) ||
    !copy_vector(
      node->get_parameter("encoder_counts_per_motor_revolution").as_double_array(),
      encoder_counts_per_motor_revolution_) ||
    !copy_vector(
      node->get_parameter("drive_direction").as_double_array(), geometry_.drive_direction) ||
    !copy_vector(
      node->get_parameter("steering_min").as_double_array(), geometry_.steering_min) ||
    !copy_vector(
      node->get_parameter("steering_max").as_double_array(), geometry_.steering_max) ||
    !copy_vector(
      node->get_parameter("steering_gear_ratio").as_double_array(),
      geometry_.steering_gear_ratio) ||
    !copy_vector(
      node->get_parameter("steering_direction").as_double_array(),
      geometry_.steering_direction) ||
    !copy_vector(
      node->get_parameter("steering_offset").as_double_array(), geometry_.steering_offset))
  {
    RCLCPP_ERROR(
      node->get_logger(), "Joint/geometry parameter arrays have incorrect lengths (6 drive, 4 steer)");
    return false;
  }

  limits_.max_linear_speed = node->get_parameter("max_linear_speed").as_double();
  limits_.max_yaw_rate = node->get_parameter("max_yaw_rate").as_double();
  limits_.max_wheel_angular_speed =
    node->get_parameter("max_wheel_angular_speed").as_double();
  limits_.max_linear_acceleration =
    node->get_parameter("max_linear_acceleration").as_double();
  limits_.max_linear_deceleration =
    node->get_parameter("max_linear_deceleration").as_double();
  limits_.max_yaw_acceleration =
    node->get_parameter("max_yaw_acceleration").as_double();
  limits_.max_jerk = node->get_parameter("max_jerk").as_double();
  limits_.steering_alignment_soft =
    node->get_parameter("steering_alignment_soft").as_double();
  limits_.steering_alignment_hard =
    node->get_parameter("steering_alignment_hard").as_double();
  limits_.minimum_linear_for_turn =
    node->get_parameter("minimum_linear_for_turn").as_double();
  limits_.allow_point_turn = node->get_parameter("allow_point_turn").as_bool();

  command_timeout_ = node->get_parameter("command_timeout").as_double();
  imu_timeout_ = node->get_parameter("imu_timeout").as_double();
  monitor_imu_ = node->get_parameter("monitor_imu").as_bool();
  auto_zero_on_activate_ = node->get_parameter("auto_zero_on_activate").as_bool();
  velocity_kp_ = node->get_parameter("velocity_kp").as_double();
  velocity_ki_ = node->get_parameter("velocity_ki").as_double();
  velocity_feedforward_ = node->get_parameter("velocity_feedforward").as_double();
  max_motor_current_ = node->get_parameter("max_motor_current").as_double();
  integral_limit_ = node->get_parameter("integral_limit").as_double();
  yaw_feedback_gain_ = node->get_parameter("yaw_feedback_gain").as_double();
  slip_ratio_threshold_ = node->get_parameter("slip_ratio_threshold").as_double();
  slip_reference_speed_ = node->get_parameter("slip_reference_speed").as_double();
  minimum_traction_scale_ = node->get_parameter("minimum_traction_scale").as_double();
  publish_rate_ = node->get_parameter("publish_rate").as_double();
  if (!copy_vector(
      node->get_parameter("pose_covariance_diagonal").as_double_array(),
      pose_covariance_diagonal_) ||
    !copy_vector(
      node->get_parameter("twist_covariance_diagonal").as_double_array(),
      twist_covariance_diagonal_))
  {
    RCLCPP_ERROR(node->get_logger(), "Odometry covariance arrays must each contain six values");
    return false;
  }
  imu_topic_ = node->get_parameter("imu_topic").as_string();
  odom_frame_ = node->get_parameter("odom_frame").as_string();
  base_frame_ = node->get_parameter("base_frame").as_string();

  const int minimum_wheels = node->get_parameter("minimum_healthy_drive_wheels").as_int();
  const int minimum_per_side =
    node->get_parameter("minimum_healthy_wheels_per_side").as_int();
  if (minimum_wheels < 1 || minimum_wheels > 6 ||
    minimum_per_side < 1 || minimum_per_side > 3)
  {
    RCLCPP_ERROR(node->get_logger(), "Fault-policy wheel counts are invalid");
    return false;
  }
  fault_policy_.minimum_healthy_drive_wheels = static_cast<std::size_t>(minimum_wheels);
  fault_policy_.minimum_healthy_wheels_per_side = static_cast<std::size_t>(minimum_per_side);
  fault_policy_.degraded_5wd_scale = node->get_parameter("degraded_5wd_scale").as_double();
  fault_policy_.degraded_4wd_scale = node->get_parameter("degraded_4wd_scale").as_double();
  fault_policy_.steering_limp_scale = node->get_parameter("steering_limp_scale").as_double();
  fault_policy_.steering_straight_tolerance =
    node->get_parameter("steering_straight_tolerance").as_double();

  try {
    validate_geometry(geometry_);
    validate_limits(limits_);
  } catch (const std::exception & error) {
    RCLCPP_ERROR(node->get_logger(), "Invalid drive parameters: %s", error.what());
    return false;
  }

  const bool covariance_valid = std::all_of(
    pose_covariance_diagonal_.begin(), pose_covariance_diagonal_.end(),
    [](double value) {return std::isfinite(value) && value >= 0.0;}) &&
    std::all_of(
    twist_covariance_diagonal_.begin(), twist_covariance_diagonal_.end(),
    [](double value) {return std::isfinite(value) && value >= 0.0;});
  const bool encoder_scaling_valid = std::all_of(
    encoder_counts_per_motor_revolution_.begin(),
    encoder_counts_per_motor_revolution_.end(),
    [](double value) {return std::isfinite(value) && value > 0.0;});
  const bool scalars_valid = covariance_valid && encoder_scaling_valid && !imu_topic_.empty() &&
    std::isfinite(command_timeout_) && command_timeout_ > 0.0 &&
    std::isfinite(imu_timeout_) && imu_timeout_ > 0.0 &&
    std::isfinite(velocity_kp_) && velocity_kp_ >= 0.0 &&
    std::isfinite(velocity_ki_) && velocity_ki_ >= 0.0 &&
    std::isfinite(velocity_feedforward_) && velocity_feedforward_ >= 0.0 &&
    std::isfinite(yaw_feedback_gain_) && yaw_feedback_gain_ >= 0.0 &&
    std::isfinite(max_motor_current_) && max_motor_current_ > 0.0 &&
    max_motor_current_ <= kConfiguredEmbeddedCurrentLimitAmps &&
    std::isfinite(integral_limit_) && integral_limit_ >= 0.0 &&
    slip_ratio_threshold_ >= 0.0 && slip_reference_speed_ > 0.0 &&
    minimum_traction_scale_ >= 0.0 && minimum_traction_scale_ <= 1.0 &&
    publish_rate_ > 0.0 &&
    fault_policy_.degraded_5wd_scale >= 0.0 && fault_policy_.degraded_5wd_scale <= 1.0 &&
    fault_policy_.degraded_4wd_scale >= 0.0 && fault_policy_.degraded_4wd_scale <= 1.0 &&
    fault_policy_.steering_limp_scale >= 0.0 && fault_policy_.steering_limp_scale <= 1.0 &&
    fault_policy_.steering_straight_tolerance >= 0.0;
  if (!scalars_valid) {
    RCLCPP_ERROR(node->get_logger(), "One or more scalar controller parameters are invalid");
  }
  return scalars_valid;
}

controller_interface::CallbackReturn SpearDriveController::on_configure(
  const rclcpp_lifecycle::State &)
{
  if (!load_parameters()) {
    return controller_interface::CallbackReturn::ERROR;
  }

  StampedCommand stopped;
  stopped.received = get_node()->now();
  command_buffer_.writeFromNonRT(stopped);
  imu_buffer_.writeFromNonRT(StampedImu{});
  estimated_linear_.store(0.0);
  estimated_yaw_rate_.store(0.0);
  odom_x_.store(0.0);
  odom_y_.store(0.0);
  odom_yaw_.store(0.0);

  command_subscriber_ = get_node()->create_subscription<geometry_msgs::msg::TwistStamped>(
    "~/cmd_vel", rclcpp::SystemDefaultsQoS(),
    [this](geometry_msgs::msg::TwistStamped::SharedPtr message) {
      StampedCommand command;
      command.command.linear_x = message->twist.linear.x;
      command.command.angular_z = message->twist.angular.z;
      command.received = get_node()->now();
      command_buffer_.writeFromNonRT(command);
    });
  imu_subscriber_ = get_node()->create_subscription<sensor_msgs::msg::Imu>(
    imu_topic_, rclcpp::SensorDataQoS(),
    [this](sensor_msgs::msg::Imu::SharedPtr message) {
      StampedImu sample;
      sample.yaw_rate = message->angular_velocity.z;
      sample.valid = std::isfinite(sample.yaw_rate);
      sample.received = get_node()->now();
      imu_buffer_.writeFromNonRT(sample);
    });
  zero_service_ = get_node()->create_service<std_srvs::srv::Trigger>(
    "~/zero_steering",
    std::bind(
      &SpearDriveController::request_zero, this,
      std::placeholders::_1, std::placeholders::_2));
  diagnostics_publisher_ =
    get_node()->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
    "~/diagnostics", rclcpp::SystemDefaultsQoS());
  odometry_publisher_ = get_node()->create_publisher<nav_msgs::msg::Odometry>(
    "~/odom", rclcpp::SystemDefaultsQoS());
  const auto timer_period = std::chrono::duration<double>(1.0 / publish_rate_);
  status_timer_ = get_node()->create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(timer_period),
    std::bind(&SpearDriveController::publish_status, this));
  status_timer_->cancel();
  return controller_interface::CallbackReturn::SUCCESS;
}

bool SpearDriveController::bind_interfaces()
{
  release_interfaces();
  for (auto & interface : command_interfaces_) {
    for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
      if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kCurrentInterface)
      {
        drive_current_commands_[index] = &interface;
      } else if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kControlWordInterface)
      {
        drive_control_word_commands_[index] = &interface;
      }
    }
    for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
      if (interface.get_prefix_name() == steering_joints_[index] &&
        interface.get_interface_name() == hardware_interface::HW_IF_POSITION)
      {
        steering_commands_[index] = &interface;
      }
    }
  }
  for (auto & interface : state_interfaces_) {
    for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
      if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kEncoderCountsPerSecondInterface)
      {
        drive_encoder_velocity_states_[index] = &interface;
      } else if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kEncoderCountsInterface)
      {
        drive_encoder_position_states_[index] = &interface;
      } else if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kCurrentInterface)
      {
        drive_current_states_[index] = &interface;
      } else if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kStatusWordInterface)
      {
        drive_status_word_states_[index] = &interface;
      } else if (interface.get_prefix_name() == drive_joints_[index] &&
        interface.get_interface_name() == kDutyCycleInterface)
      {
        drive_duty_cycle_states_[index] = &interface;
      }
    }
    for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
      if (interface.get_prefix_name() == steering_joints_[index] &&
        interface.get_interface_name() == hardware_interface::HW_IF_POSITION)
      {
        steering_states_[index] = &interface;
      }
    }
  }

  return std::all_of(
    drive_current_commands_.begin(), drive_current_commands_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_control_word_commands_.begin(), drive_control_word_commands_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_encoder_velocity_states_.begin(), drive_encoder_velocity_states_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_encoder_position_states_.begin(), drive_encoder_position_states_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_current_states_.begin(), drive_current_states_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_status_word_states_.begin(), drive_status_word_states_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    drive_duty_cycle_states_.begin(), drive_duty_cycle_states_.end(),
    [](const auto * value) {return value;}) &&
    std::all_of(
    steering_commands_.begin(), steering_commands_.end(), [](const auto * value) {return value;}) &&
    std::all_of(
    steering_states_.begin(), steering_states_.end(), [](const auto * value) {return value;});
}

void SpearDriveController::release_interfaces()
{
  drive_current_commands_.fill(nullptr);
  drive_control_word_commands_.fill(nullptr);
  drive_encoder_velocity_states_.fill(nullptr);
  drive_encoder_position_states_.fill(nullptr);
  drive_current_states_.fill(nullptr);
  drive_status_word_states_.fill(nullptr);
  drive_duty_cycle_states_.fill(nullptr);
  steering_commands_.fill(nullptr);
  steering_states_.fill(nullptr);
}

controller_interface::CallbackReturn SpearDriveController::on_activate(
  const rclcpp_lifecycle::State &)
{
  if (!bind_interfaces()) {
    RCLCPP_ERROR(
      get_node()->get_logger(),
      "Could not bind the verified brushed-DC and steering interfaces");
    return controller_interface::CallbackReturn::ERROR;
  }

  halt();
  command_limiter_.reset();
  StampedCommand stopped;
  stopped.received = get_node()->now();
  command_buffer_.writeFromNonRT(stopped);
  command_is_fresh_.store(false);
  motion_requested_.store(false);
  steering_zeroed_ = false;
  if (auto_zero_on_activate_) {
    capture_steering_zero();
  }
  set_drive_enable(true);
  mode_.store(static_cast<int>(
      steering_zeroed_ ? OperatingMode::READY : OperatingMode::NOT_ZEROED));
  status_timer_->reset();
  RCLCPP_WARN(
    get_node()->get_logger(),
    "Drive controller active. Steering zero was %s; keep the wheels physically straight before activation.",
    steering_zeroed_ ? "captured" : "not captured");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn SpearDriveController::on_deactivate(
  const rclcpp_lifecycle::State &)
{
  halt();
  status_timer_->cancel();
  mode_.store(static_cast<int>(OperatingMode::DISABLED));
  steering_zeroed_ = false;
  release_interfaces();
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn SpearDriveController::on_cleanup(
  const rclcpp_lifecycle::State &)
{
  if (status_timer_) {
    status_timer_->cancel();
  }
  command_subscriber_.reset();
  imu_subscriber_.reset();
  zero_service_.reset();
  diagnostics_publisher_.reset();
  odometry_publisher_.reset();
  status_timer_.reset();
  command_limiter_.reset();
  steering_zeroed_ = false;
  mode_.store(static_cast<int>(OperatingMode::DISABLED));
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn SpearDriveController::on_error(
  const rclcpp_lifecycle::State &)
{
  halt();
  if (status_timer_) {
    status_timer_->cancel();
  }
  steering_zeroed_ = false;
  mode_.store(static_cast<int>(OperatingMode::FAULT_STOP));
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn SpearDriveController::on_shutdown(
  const rclcpp_lifecycle::State &)
{
  halt();
  if (status_timer_) {
    status_timer_->cancel();
  }
  steering_zeroed_ = false;
  mode_.store(static_cast<int>(OperatingMode::DISABLED));
  return controller_interface::CallbackReturn::SUCCESS;
}

void SpearDriveController::halt()
{
  for (auto * interface : drive_current_commands_) {
    if (interface != nullptr) {
      interface->set_value(0.0);
    }
  }
  set_drive_enable(false);
  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    if (steering_commands_[index] != nullptr && steering_states_[index] != nullptr) {
      const double value = steering_states_[index]->get_value();
      steering_commands_[index]->set_value(std::isfinite(value) ? value : 0.0);
    }
  }
  velocity_integral_.fill(0.0);
}

void SpearDriveController::set_drive_enable(bool enabled)
{
  const double control_word = enabled ? kDriveEnabledControlWord : 0.0;
  for (auto * interface : drive_control_word_commands_) {
    if (interface != nullptr) {
      interface->set_value(control_word);
    }
  }
}

void SpearDriveController::capture_steering_zero()
{
  bool valid = true;
  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    const double raw = steering_states_[index] == nullptr ?
      std::numeric_limits<double>::quiet_NaN() : steering_states_[index]->get_value();
    if (!std::isfinite(raw)) {
      valid = false;
      continue;
    }
    steering_zero_reference_[index] = raw;
    last_valid_steering_[index] = 0.0;
  }
  steering_zeroed_ = valid;
  zero_requested_.store(false);
}

void SpearDriveController::request_zero(
  const std::shared_ptr<std_srvs::srv::Trigger::Request>,
  std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
  if (motion_requested_.load() ||
    std::abs(estimated_linear_.load()) > 0.02 ||
    std::abs(estimated_yaw_rate_.load()) > 0.05)
  {
    response->success = false;
    response->message = "Release the drive deadman and wait for the rover to stop before zeroing";
    return;
  }
  zero_requested_.store(true);
  response->success = true;
  response->message = "Steering zero capture requested; keep all four wheels physically straight";
}

controller_interface::return_type SpearDriveController::update(
  const rclcpp::Time & time,
  const rclcpp::Duration & period)
{
  const double dt = period.seconds();
  if (!std::isfinite(dt) || dt <= 0.0) {
    halt();
    return controller_interface::return_type::ERROR;
  }

  std::array<double, kDriveWheelCount> motor_velocity{};
  std::array<double, kSteeringWheelCount> steering_position{};
  HealthSnapshot health;
  health.master_healthy = true;
  set_drive_enable(true);
  double maximum_measured_current = 0.0;
  int enabled_drive_count = 0;
  for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
    const double raw_velocity = drive_encoder_velocity_states_[index]->get_value();
    const double status_value = drive_status_word_states_[index]->get_value();
    const double measured_current = drive_current_states_[index]->get_value();
    const bool status_valid = std::isfinite(status_value) && status_value >= 0.0;
    const std::uint32_t status_word = status_valid ?
      static_cast<std::uint32_t>(status_value) : 0U;
    const bool drive_enabled = status_valid &&
      (status_word & kDriveEnabledStatusBit) != 0U;
    if (drive_enabled) {
      ++enabled_drive_count;
    }
    if (std::isfinite(measured_current)) {
      maximum_measured_current = std::max(
        maximum_measured_current, std::abs(measured_current));
    }
    motor_velocity[index] = encoder_counts_per_second_to_motor_velocity(
      raw_velocity, encoder_counts_per_motor_revolution_[index]);
    health.drive_healthy[index] = std::isfinite(motor_velocity[index]) && drive_enabled;
  }
  enabled_drive_count_.store(enabled_drive_count);
  maximum_measured_current_.store(maximum_measured_current);
  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    const double raw = steering_states_[index]->get_value();
    if (steering_zeroed_ && std::isfinite(raw)) {
      steering_position[index] =
        geometry_.steering_direction[index] * (raw - steering_zero_reference_[index]) /
        geometry_.steering_gear_ratio[index] -
        geometry_.steering_offset[index];
      health.steering_healthy[index] = std::isfinite(steering_position[index]);
      if (health.steering_healthy[index]) {
        last_valid_steering_[index] = steering_position[index];
      }
    } else {
      steering_position[index] = std::numeric_limits<double>::quiet_NaN();
      health.steering_healthy[index] = false;
    }
  }

  if (zero_requested_.load()) {
    capture_steering_zero();
    for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
      steering_position[index] = 0.0;
      health.steering_healthy[index] = steering_zeroed_;
    }
  }

  const StampedCommand * command_sample = command_buffer_.readFromRT();
  ChassisCommand requested{};
  bool command_fresh = false;
  if (command_sample != nullptr) {
    const double age = (time - command_sample->received).seconds();
    command_fresh = age >= 0.0 && age <= command_timeout_;
    if (command_fresh) {
      requested = command_sample->command;
    }
  }
  command_is_fresh_.store(command_fresh);
  motion_requested_.store(
    std::abs(requested.linear_x) > 1e-3 || std::abs(requested.angular_z) > 1e-3);

  const StampedImu * imu_sample = imu_buffer_.readFromRT();
  bool imu_fresh = false;
  double measured_yaw_rate = 0.0;
  if (imu_sample != nullptr && imu_sample->valid) {
    const double age = (time - imu_sample->received).seconds();
    imu_fresh = age >= 0.0 && age <= imu_timeout_;
    measured_yaw_rate = imu_sample->yaw_rate;
  }
  imu_is_fresh_.store(imu_fresh);

  health.last_valid_steering = last_valid_steering_;
  health.steering_zeroed = steering_zeroed_;
  health.command_fresh = command_fresh;
  health.imu_healthy = !monitor_imu_ || imu_fresh;
  FaultDecision decision = evaluate_faults(health, fault_policy_);

  ChassisCommand limited{};
  if (decision.motion_scale > 0.0) {
    requested.linear_x *= decision.motion_scale;
    requested.angular_z *= decision.motion_scale;
    if (decision.force_straight) {
      requested.angular_z = 0.0;
    }
    limited = command_limiter_.limit(requested, limits_, dt);
  } else {
    command_limiter_.reset();
  }
  DriveSetpoint setpoint = compute_drive_setpoint(geometry_, limits_, limited);
  if (decision.force_straight) {
    setpoint.steering_angle.fill(0.0);
  }

  const double alignment_scale = steering_alignment_scale(
    steering_position, setpoint.steering_angle, health.steering_healthy,
    limits_.steering_alignment_soft, limits_.steering_alignment_hard);
  const double yaw_error = imu_fresh ? limited.angular_z - measured_yaw_rate : 0.0;

  for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
    if (!decision.drive_enabled[index] || decision.motion_scale <= 0.0) {
      drive_current_commands_[index]->set_value(0.0);
      velocity_integral_[index] = 0.0;
      last_traction_scale_[index] = 0.0;
      continue;
    }

    const double desired_motor_velocity = setpoint.wheel_angular_speed[index] *
      geometry_.drive_gear_ratio[index] * geometry_.drive_direction[index];
    const double velocity_error = desired_motor_velocity - motor_velocity[index];
    velocity_integral_[index] = std::clamp(
      velocity_integral_[index] + velocity_error * dt,
      -integral_limit_, integral_limit_);

    const double measured_output_velocity = motor_velocity[index] *
      geometry_.drive_direction[index] / geometry_.drive_gear_ratio[index];
    const double desired_output_velocity = setpoint.wheel_angular_speed[index];
    double traction_scale = 1.0;
    if (std::abs(desired_output_velocity) > 1e-3 &&
      measured_output_velocity * desired_output_velocity > 0.0)
    {
      const double excess = std::abs(measured_output_velocity) -
        std::abs(desired_output_velocity);
      const double slip_ratio = excess /
        std::max(std::abs(desired_output_velocity), slip_reference_speed_);
      if (slip_ratio > slip_ratio_threshold_) {
        traction_scale = std::max(
          minimum_traction_scale_,
          1.0 - (slip_ratio - slip_ratio_threshold_));
      }
    }
    last_traction_scale_[index] = traction_scale;

    const double side_sign = is_left_wheel(index) ? -1.0 : 1.0;
    const double yaw_current = side_sign * yaw_feedback_gain_ * yaw_error *
      geometry_.drive_direction[index];
    const double current_command =
      (velocity_feedforward_ * desired_motor_velocity +
      velocity_kp_ * velocity_error +
      velocity_ki_ * velocity_integral_[index]) * traction_scale + yaw_current;
    drive_current_commands_[index]->set_value(
      clamp_current(current_command * alignment_scale, max_motor_current_));
  }

  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    double desired = setpoint.steering_angle[index];
    if (!health.steering_healthy[index]) {
      desired = last_valid_steering_[index];
    }
    const double raw_command = steering_zero_reference_[index] +
      geometry_.steering_direction[index] * (desired + geometry_.steering_offset[index]) *
      geometry_.steering_gear_ratio[index];
    steering_commands_[index]->set_value(
      std::isfinite(raw_command) ? raw_command : steering_zero_reference_[index]);
  }

  const BodyTwistEstimate estimate = estimate_body_twist(
    geometry_, motor_velocity, steering_position,
    health.drive_healthy, health.steering_healthy);
  if (estimate.valid) {
    estimated_linear_.store(estimate.linear_x);
    estimated_yaw_rate_.store(estimate.angular_z);
    const double previous_yaw = odom_yaw_.load();
    odom_x_.store(odom_x_.load() + estimate.linear_x * std::cos(previous_yaw) * dt);
    odom_y_.store(odom_y_.load() + estimate.linear_x * std::sin(previous_yaw) * dt);
    odom_yaw_.store(std::remainder(previous_yaw + estimate.angular_z * dt, 2.0 * kPi));
  }

  mode_.store(static_cast<int>(decision.mode));
  last_motion_scale_.store(decision.motion_scale * alignment_scale);
  healthy_drive_count_.store(static_cast<int>(std::count(
      health.drive_healthy.begin(), health.drive_healthy.end(), true)));
  healthy_steering_count_.store(static_cast<int>(std::count(
      health.steering_healthy.begin(), health.steering_healthy.end(), true)));
  return controller_interface::return_type::OK;
}

void SpearDriveController::publish_status()
{
  const auto stamp = get_node()->now();
  const auto mode = static_cast<OperatingMode>(mode_.load());

  diagnostic_msgs::msg::DiagnosticArray diagnostics;
  diagnostics.header.stamp = stamp;
  diagnostic_msgs::msg::DiagnosticStatus status;
  const std::string node_namespace = get_node()->get_namespace();
  status.name = (node_namespace == "/" ? std::string() : node_namespace) + "/" +
    get_node()->get_name() + ": drivetrain";
  status.hardware_id = "spear_6wd_4ws";
  if (mode == OperatingMode::FAULT_STOP || mode == OperatingMode::NOT_ZEROED) {
    status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
  } else if (mode == OperatingMode::DEGRADED_5WD ||
    mode == OperatingMode::DEGRADED_4WD ||
    mode == OperatingMode::STEER_LIMP || mode == OperatingMode::IMU_DEGRADED)
  {
    status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
  } else {
    status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
  }
  status.message = mode_name(mode);
  status.values.push_back(diagnostic_value("mode", mode_name(mode)));
  status.values.push_back(diagnostic_value(
      "healthy_drive_wheels", std::to_string(healthy_drive_count_.load())));
  status.values.push_back(diagnostic_value(
      "enabled_drive_controllers", std::to_string(enabled_drive_count_.load())));
  status.values.push_back(diagnostic_value(
      "maximum_measured_current_A", std::to_string(maximum_measured_current_.load())));
  status.values.push_back(diagnostic_value(
      "healthy_steering", std::to_string(healthy_steering_count_.load())));
  status.values.push_back(diagnostic_value(
      "command_fresh", command_is_fresh_.load() ? "true" : "false"));
  status.values.push_back(diagnostic_value(
      "imu_fresh", imu_is_fresh_.load() ? "true" : "false"));
  status.values.push_back(diagnostic_value(
      "motion_scale", std::to_string(last_motion_scale_.load())));
  diagnostics.status.push_back(status);
  diagnostics_publisher_->publish(diagnostics);

  nav_msgs::msg::Odometry odometry;
  odometry.header.stamp = stamp;
  odometry.header.frame_id = odom_frame_;
  odometry.child_frame_id = base_frame_;
  odometry.pose.pose.position.x = odom_x_.load();
  odometry.pose.pose.position.y = odom_y_.load();
  odometry.pose.pose.orientation = yaw_quaternion(odom_yaw_.load());
  odometry.twist.twist.linear.x = estimated_linear_.load();
  odometry.twist.twist.angular.z = estimated_yaw_rate_.load();
  for (std::size_t index = 0; index < pose_covariance_diagonal_.size(); ++index) {
    const std::size_t diagonal = index * 6U + index;
    odometry.pose.covariance[diagonal] = pose_covariance_diagonal_[index];
    odometry.twist.covariance[diagonal] = twist_covariance_diagonal_[index];
  }
  odometry_publisher_->publish(odometry);
}

}  // namespace spear_drive

PLUGINLIB_EXPORT_CLASS(
  spear_drive::SpearDriveController,
  controller_interface::ControllerInterface)
