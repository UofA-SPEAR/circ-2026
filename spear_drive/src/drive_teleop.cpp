#include <algorithm>
#include <chrono>
#include <cmath>
#include <memory>
#include <string>

#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "diagnostic_msgs/msg/diagnostic_status.hpp"
#include "diagnostic_msgs/msg/key_value.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"

#include "spear_drive/drive_core.hpp"

namespace spear_drive
{

class DriveTeleop : public rclcpp::Node
{
public:
  DriveTeleop()
  : Node("drive_teleop")
  {
    input_topic_ = declare_parameter<std::string>("input_topic", "/drive/joy");
    output_topic_ = declare_parameter<std::string>(
      "output_topic", "/spear_drive_controller/cmd_vel");
    linear_axis_ = declare_parameter<int>("linear_axis", 1);
    yaw_axis_ = declare_parameter<int>("yaw_axis", 2);
    linear_sign_ = declare_parameter<double>("linear_sign", -1.0);
    yaw_sign_ = declare_parameter<double>("yaw_sign", -1.0);
    deadman_button_ = declare_parameter<int>("deadman_button", 5);
    precision_button_ = declare_parameter<int>("precision_button", 4);
    max_linear_speed_ = declare_parameter<double>("max_linear_speed", 0.50);
    max_yaw_rate_ = declare_parameter<double>("max_yaw_rate", 0.60);
    precision_scale_ = declare_parameter<double>("precision_scale", 0.35);
    deadzone_ = declare_parameter<double>("deadzone", 0.08);
    neutral_threshold_ = declare_parameter<double>("neutral_threshold", 0.12);
    neutral_hold_seconds_ = declare_parameter<double>("neutral_hold_seconds", 0.20);
    joystick_timeout_ = declare_parameter<double>("joystick_timeout", 0.25);
    require_single_publisher_ = declare_parameter<bool>("require_single_publisher", true);

    command_publisher_ = create_publisher<geometry_msgs::msg::TwistStamped>(
      output_topic_, rclcpp::SystemDefaultsQoS());
    diagnostics_publisher_ = create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
      "~/diagnostics", rclcpp::SystemDefaultsQoS());
    joy_subscriber_ = create_subscription<sensor_msgs::msg::Joy>(
      input_topic_, rclcpp::SensorDataQoS(),
      std::bind(&DriveTeleop::on_joy, this, std::placeholders::_1));
    watchdog_timer_ = create_wall_timer(
      std::chrono::milliseconds(50), std::bind(&DriveTeleop::on_watchdog, this));

    RCLCPP_INFO(
      get_logger(),
      "Drive joystick isolated on %s; release deadman, hold neutral, then hold button %d",
      input_topic_.c_str(), deadman_button_);
  }

private:
  using SteadyClock = std::chrono::steady_clock;

  static bool valid_index(int index, std::size_t size)
  {
    return index >= 0 && static_cast<std::size_t>(index) < size;
  }

  double axis(const sensor_msgs::msg::Joy & message, int index) const
  {
    if (!valid_index(index, message.axes.size())) {
      return 0.0;
    }
    return bounded_axis(message.axes[static_cast<std::size_t>(index)], deadzone_);
  }

  bool button(const sensor_msgs::msg::Joy & message, int index) const
  {
    return valid_index(index, message.buttons.size()) &&
      message.buttons[static_cast<std::size_t>(index)] != 0;
  }

  void publish_command(double linear, double yaw)
  {
    geometry_msgs::msg::TwistStamped command;
    command.header.stamp = now();
    command.header.frame_id = "base_link";
    command.twist.linear.x = linear;
    command.twist.angular.z = yaw;
    command_publisher_->publish(command);
  }

  void publish_zero_once()
  {
    if (!zero_sent_) {
      publish_command(0.0, 0.0);
      zero_sent_ = true;
    }
  }

  void on_joy(const sensor_msgs::msg::Joy::SharedPtr message)
  {
    const auto timestamp = SteadyClock::now();
    last_joy_time_ = timestamp;
    received_joy_ = true;
    timed_out_ = false;

    const bool indexes_valid =
      valid_index(linear_axis_, message->axes.size()) &&
      valid_index(yaw_axis_, message->axes.size()) &&
      valid_index(deadman_button_, message->buttons.size());
    if (!indexes_valid) {
      input_valid_ = false;
      armed_ = false;
      publish_zero_once();
      return;
    }

    const double linear_value = axis(*message, linear_axis_);
    const double yaw_value = axis(*message, yaw_axis_);
    const bool neutral = std::abs(linear_value) <= neutral_threshold_ &&
      std::abs(yaw_value) <= neutral_threshold_;
    const bool deadman = button(*message, deadman_button_);
    input_valid_ = true;

    if (!deadman) {
      deadman_was_released_ = true;
      armed_ = false;
      if (neutral) {
        if (!neutral_timing_) {
          neutral_since_ = timestamp;
          neutral_timing_ = true;
        }
      } else {
        neutral_timing_ = false;
      }
      zero_sent_ = false;
      publish_zero_once();
      return;
    }

    const double neutral_duration = neutral_timing_ ?
      std::chrono::duration<double>(timestamp - neutral_since_).count() : 0.0;
    if (!armed_ && deadman_was_released_ && neutral &&
      neutral_duration >= neutral_hold_seconds_)
    {
      armed_ = true;
    }
    if (!armed_) {
      publish_zero_once();
      return;
    }

    const double precision = button(*message, precision_button_) ? precision_scale_ : 1.0;
    publish_command(
      linear_value * linear_sign_ * max_linear_speed_ * precision,
      yaw_value * yaw_sign_ * max_yaw_rate_ * precision);
    zero_sent_ = false;
  }

  void on_watchdog()
  {
    const bool publisher_ok = !require_single_publisher_ ||
      count_publishers(input_topic_) == 1U;
    if (!publisher_ok) {
      armed_ = false;
      input_valid_ = false;
      publish_zero_once();
    }

    if (received_joy_) {
      const double age = std::chrono::duration<double>(
        SteadyClock::now() - last_joy_time_).count();
      if (age > joystick_timeout_) {
        timed_out_ = true;
        armed_ = false;
        publish_zero_once();
      }
    }
    publish_diagnostics(publisher_ok);
  }

  void publish_diagnostics(bool publisher_ok)
  {
    diagnostic_msgs::msg::DiagnosticArray array;
    array.header.stamp = now();
    diagnostic_msgs::msg::DiagnosticStatus status;
    status.name = get_fully_qualified_name() + std::string(": drive joystick");
    status.hardware_id = "drive_gamepad";
    if (!publisher_ok || timed_out_ || !input_valid_) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status.message = !publisher_ok ? "drive joystick publisher count is not one" :
        (timed_out_ ? "drive joystick timed out" : "drive joystick mapping invalid");
    } else if (!armed_) {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status.message = "disarmed: release deadman and hold axes neutral";
    } else {
      status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
      status.message = "armed while deadman is held";
    }
    diagnostic_msgs::msg::KeyValue topic;
    topic.key = "input_topic";
    topic.value = input_topic_;
    status.values.push_back(topic);
    diagnostic_msgs::msg::KeyValue armed;
    armed.key = "armed";
    armed.value = armed_ ? "true" : "false";
    status.values.push_back(armed);
    array.status.push_back(status);
    diagnostics_publisher_->publish(array);
  }

  std::string input_topic_;
  std::string output_topic_;
  int linear_axis_{1};
  int yaw_axis_{2};
  double linear_sign_{-1.0};
  double yaw_sign_{-1.0};
  int deadman_button_{5};
  int precision_button_{4};
  double max_linear_speed_{0.5};
  double max_yaw_rate_{0.6};
  double precision_scale_{0.35};
  double deadzone_{0.08};
  double neutral_threshold_{0.12};
  double neutral_hold_seconds_{0.2};
  double joystick_timeout_{0.25};
  bool require_single_publisher_{true};

  bool received_joy_{false};
  bool input_valid_{false};
  bool timed_out_{true};
  bool deadman_was_released_{false};
  bool neutral_timing_{false};
  bool armed_{false};
  bool zero_sent_{false};
  SteadyClock::time_point last_joy_time_{};
  SteadyClock::time_point neutral_since_{};

  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_subscriber_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr command_publisher_;
  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr diagnostics_publisher_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;
};

}  // namespace spear_drive

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<spear_drive::DriveTeleop>());
  rclcpp::shutdown();
  return 0;
}
