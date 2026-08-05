#ifndef SPEAR_DRIVE__DRIVE_CONTROLLER_HPP_
#define SPEAR_DRIVE__DRIVE_CONTROLLER_HPP_

#include <array>
#include <atomic>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "controller_interface/controller_interface.hpp"
#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "hardware_interface/loaned_command_interface.hpp"
#include "hardware_interface/loaned_state_interface.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/subscription.hpp"
#include "rclcpp/timer.hpp"
#include "realtime_tools/realtime_buffer.h"
#include "sensor_msgs/msg/imu.hpp"
#include "std_srvs/srv/trigger.hpp"

#include "spear_drive/drive_core.hpp"
#include "spear_drive/fault_manager.hpp"

namespace spear_drive
{

class SpearDriveController : public controller_interface::ControllerInterface
{
public:
  SpearDriveController();

  controller_interface::InterfaceConfiguration command_interface_configuration() const override;
  controller_interface::InterfaceConfiguration state_interface_configuration() const override;

  controller_interface::CallbackReturn on_init() override;
  controller_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;
  controller_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;
  controller_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;
  controller_interface::CallbackReturn on_cleanup(
    const rclcpp_lifecycle::State & previous_state) override;
  controller_interface::CallbackReturn on_error(
    const rclcpp_lifecycle::State & previous_state) override;
  controller_interface::CallbackReturn on_shutdown(
    const rclcpp_lifecycle::State & previous_state) override;

  controller_interface::return_type update(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

private:
  struct StampedCommand
  {
    ChassisCommand command{};
    rclcpp::Time received{0, 0, RCL_ROS_TIME};
  };

  struct StampedImu
  {
    double yaw_rate{0.0};
    rclcpp::Time received{0, 0, RCL_ROS_TIME};
    bool valid{false};
  };

  bool load_parameters();
  bool bind_interfaces();
  void release_interfaces();
  void halt();
  void capture_steering_zero();
  void publish_status();
  void request_zero(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response);

  std::array<std::string, kDriveWheelCount> drive_joints_{};
  std::array<std::string, kSteeringWheelCount> steering_joints_{};
  Geometry geometry_{};
  MotionLimits limits_{};
  FaultPolicy fault_policy_{};

  double command_timeout_{0.30};
  double imu_timeout_{0.30};
  bool monitor_imu_{false};
  bool auto_zero_on_activate_{true};
  double velocity_kp_{0.35};
  double velocity_ki_{0.0};
  double velocity_feedforward_{0.0};
  double max_motor_effort_{2.0};
  double integral_limit_{1.0};
  double yaw_feedback_gain_{0.25};
  double slip_ratio_threshold_{0.30};
  double slip_reference_speed_{0.30};
  double minimum_traction_scale_{0.25};
  double publish_rate_{20.0};
  std::array<double, 6> pose_covariance_diagonal_{};
  std::array<double, 6> twist_covariance_diagonal_{};
  std::string imu_topic_{"~/imu"};
  std::string odom_frame_{"odom"};
  std::string base_frame_{"base_link"};

  std::array<hardware_interface::LoanedCommandInterface *, kDriveWheelCount>
  drive_commands_{};
  std::array<hardware_interface::LoanedStateInterface *, kDriveWheelCount>
  drive_states_{};
  std::array<hardware_interface::LoanedCommandInterface *, kSteeringWheelCount>
  steering_commands_{};
  std::array<hardware_interface::LoanedStateInterface *, kSteeringWheelCount>
  steering_states_{};

  std::array<double, kSteeringWheelCount> steering_zero_reference_{};
  std::array<double, kSteeringWheelCount> last_valid_steering_{};
  std::array<double, kDriveWheelCount> velocity_integral_{};
  std::array<double, kDriveWheelCount> last_traction_scale_{};
  CommandLimiter command_limiter_{};
  bool steering_zeroed_{false};
  std::atomic_bool zero_requested_{false};

  realtime_tools::RealtimeBuffer<StampedCommand> command_buffer_{};
  realtime_tools::RealtimeBuffer<StampedImu> imu_buffer_{};
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr command_subscriber_{};
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_subscriber_{};
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr zero_service_{};
  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr diagnostics_publisher_{};
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odometry_publisher_{};
  rclcpp::TimerBase::SharedPtr status_timer_{};

  std::atomic<int> mode_{static_cast<int>(OperatingMode::DISABLED)};
  std::atomic<double> estimated_linear_{0.0};
  std::atomic<double> estimated_yaw_rate_{0.0};
  std::atomic<double> odom_x_{0.0};
  std::atomic<double> odom_y_{0.0};
  std::atomic<double> odom_yaw_{0.0};
  std::atomic<double> last_motion_scale_{0.0};
  std::atomic<int> healthy_drive_count_{0};
  std::atomic<int> healthy_steering_count_{0};
  std::atomic_bool command_is_fresh_{false};
  std::atomic_bool imu_is_fresh_{false};
  std::atomic_bool motion_requested_{false};
};

}  // namespace spear_drive

#endif  // SPEAR_DRIVE__DRIVE_CONTROLLER_HPP_
