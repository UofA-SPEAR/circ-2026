#ifndef SPEAR_DRIVE__DRIVE_CORE_HPP_
#define SPEAR_DRIVE__DRIVE_CORE_HPP_

#include <array>
#include <cstddef>
#include <string>

namespace spear_drive
{

constexpr std::size_t kDriveWheelCount = 6;
constexpr std::size_t kSteeringWheelCount = 4;

enum DriveWheel : std::size_t
{
  FRONT_LEFT = 0,
  FRONT_RIGHT = 1,
  MIDDLE_LEFT = 2,
  MIDDLE_RIGHT = 3,
  REAR_LEFT = 4,
  REAR_RIGHT = 5,
};

enum SteeringWheel : std::size_t
{
  STEER_FRONT_LEFT = 0,
  STEER_FRONT_RIGHT = 1,
  STEER_REAR_LEFT = 2,
  STEER_REAR_RIGHT = 3,
};

constexpr std::array<std::size_t, kSteeringWheelCount> kSteeringDriveIndexes = {
  FRONT_LEFT, FRONT_RIGHT, REAR_LEFT, REAR_RIGHT};

struct ChassisCommand
{
  double linear_x{0.0};
  double angular_z{0.0};
};

struct Geometry
{
  std::array<double, kDriveWheelCount> wheel_x{};
  std::array<double, kDriveWheelCount> wheel_y{};
  std::array<double, kDriveWheelCount> wheel_radius{};
  std::array<double, kDriveWheelCount> drive_gear_ratio{};
  std::array<double, kDriveWheelCount> drive_direction{};
  std::array<double, kSteeringWheelCount> steering_min{};
  std::array<double, kSteeringWheelCount> steering_max{};
  std::array<double, kSteeringWheelCount> steering_gear_ratio{};
  std::array<double, kSteeringWheelCount> steering_direction{};
  std::array<double, kSteeringWheelCount> steering_offset{};
};

struct MotionLimits
{
  double max_linear_speed{0.5};
  double max_yaw_rate{0.6};
  double max_wheel_angular_speed{10.0};
  double max_linear_acceleration{0.4};
  double max_linear_deceleration{0.8};
  double max_yaw_acceleration{0.8};
  double max_jerk{2.0};
  double steering_alignment_soft{0.08};
  double steering_alignment_hard{0.25};
  double minimum_linear_for_turn{0.03};
  bool allow_point_turn{false};
};

struct DriveSetpoint
{
  std::array<double, kDriveWheelCount> wheel_surface_speed{};
  std::array<double, kDriveWheelCount> wheel_angular_speed{};
  std::array<double, kSteeringWheelCount> steering_angle{};
  ChassisCommand applied_command{};
  bool saturated{false};
};

struct BodyTwistEstimate
{
  double linear_x{0.0};
  double linear_y{0.0};
  double angular_z{0.0};
  bool valid{false};
};

void validate_geometry(const Geometry & geometry);
void validate_limits(const MotionLimits & limits);

double encoder_counts_per_second_to_motor_velocity(
  double encoder_counts_per_second,
  double encoder_counts_per_motor_revolution);

DriveSetpoint compute_drive_setpoint(
  const Geometry & geometry,
  const MotionLimits & limits,
  const ChassisCommand & command);

double steering_alignment_scale(
  const std::array<double, kSteeringWheelCount> & measured,
  const std::array<double, kSteeringWheelCount> & requested,
  const std::array<bool, kSteeringWheelCount> & healthy,
  double soft_error,
  double hard_error);

BodyTwistEstimate estimate_body_twist(
  const Geometry & geometry,
  const std::array<double, kDriveWheelCount> & measured_motor_velocity,
  const std::array<double, kSteeringWheelCount> & measured_steering,
  const std::array<bool, kDriveWheelCount> & drive_healthy,
  const std::array<bool, kSteeringWheelCount> & steering_healthy);

class CommandLimiter
{
public:
  void reset();
  ChassisCommand limit(
    const ChassisCommand & requested,
    const MotionLimits & limits,
    double period_seconds);

private:
  double linear_{0.0};
  double yaw_{0.0};
  double linear_acceleration_{0.0};
  double yaw_acceleration_{0.0};
};

double bounded_axis(double value, double deadzone);

ChassisCommand map_drive_joystick(
  const std::array<double, 6> & axes,
  double max_linear_speed,
  double max_yaw_rate,
  double deadzone,
  double linear_sign,
  double yaw_sign);

}  // namespace spear_drive

#endif  // SPEAR_DRIVE__DRIVE_CORE_HPP_
