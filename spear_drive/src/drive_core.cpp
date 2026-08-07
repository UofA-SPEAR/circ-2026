#include "spear_drive/drive_core.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace spear_drive
{
namespace
{

constexpr double kPi = 3.14159265358979323846;

double clamp_symmetric(double value, double limit)
{
  return std::clamp(value, -std::abs(limit), std::abs(limit));
}

bool finite_positive(double value)
{
  return std::isfinite(value) && value > 0.0;
}

double wrap_angle(double angle)
{
  return std::remainder(angle, 2.0 * kPi);
}

double limited_axis(
  double target,
  double & value,
  double & acceleration,
  double maximum_acceleration,
  double maximum_deceleration,
  double maximum_jerk,
  double period_seconds)
{
  if (!std::isfinite(period_seconds) || period_seconds <= 0.0) {
    return value;
  }

  const bool accelerating =
    std::abs(target) > std::abs(value) && target * value >= 0.0;
  const double acceleration_limit =
    accelerating ? maximum_acceleration : maximum_deceleration;
  double desired_acceleration = (target - value) / period_seconds;
  desired_acceleration = clamp_symmetric(desired_acceleration, acceleration_limit);

  const double acceleration_delta = clamp_symmetric(
    desired_acceleration - acceleration,
    maximum_jerk * period_seconds);
  acceleration += acceleration_delta;

  const double previous_error = target - value;
  const double proposed = value + acceleration * period_seconds;
  const double new_error = target - proposed;
  if (previous_error == 0.0 || previous_error * new_error <= 0.0) {
    value = target;
    acceleration = 0.0;
  } else {
    value = proposed;
  }
  return value;
}

std::size_t steering_index_for_drive(std::size_t drive_index)
{
  for (std::size_t index = 0; index < kSteeringDriveIndexes.size(); ++index) {
    if (kSteeringDriveIndexes[index] == drive_index) {
      return index;
    }
  }
  return kSteeringWheelCount;
}

}  // namespace

double encoder_counts_per_second_to_motor_velocity(
  double encoder_counts_per_second,
  double encoder_counts_per_motor_revolution)
{
  if (!std::isfinite(encoder_counts_per_second) ||
    !finite_positive(encoder_counts_per_motor_revolution))
  {
    return std::numeric_limits<double>::quiet_NaN();
  }
  return encoder_counts_per_second * 2.0 * kPi /
    encoder_counts_per_motor_revolution;
}

void validate_geometry(const Geometry & geometry)
{
  for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
    if (!std::isfinite(geometry.wheel_x[index]) ||
      !std::isfinite(geometry.wheel_y[index]))
    {
      throw std::invalid_argument("wheel coordinates must be finite");
    }
    if (!finite_positive(geometry.wheel_radius[index])) {
      throw std::invalid_argument("wheel radii must be positive");
    }
    if (!finite_positive(geometry.drive_gear_ratio[index])) {
      throw std::invalid_argument("drive gear ratios must be positive");
    }
    if (std::abs(std::abs(geometry.drive_direction[index]) - 1.0) > 1e-9) {
      throw std::invalid_argument("drive directions must be -1 or 1");
    }
  }

  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    if (!std::isfinite(geometry.steering_min[index]) ||
      !std::isfinite(geometry.steering_max[index]) ||
      geometry.steering_min[index] >= geometry.steering_max[index])
    {
      throw std::invalid_argument("steering limits are invalid");
    }
    if (std::abs(std::abs(geometry.steering_direction[index]) - 1.0) > 1e-9) {
      throw std::invalid_argument("steering directions must be -1 or 1");
    }
    if (!finite_positive(geometry.steering_gear_ratio[index])) {
      throw std::invalid_argument("steering gear ratios must be positive");
    }
    if (!std::isfinite(geometry.steering_offset[index])) {
      throw std::invalid_argument("steering offsets must be finite");
    }
  }
}

void validate_limits(const MotionLimits & limits)
{
  if (!finite_positive(limits.max_linear_speed) ||
    !finite_positive(limits.max_yaw_rate) ||
    !finite_positive(limits.max_wheel_angular_speed) ||
    !finite_positive(limits.max_linear_acceleration) ||
    !finite_positive(limits.max_linear_deceleration) ||
    !finite_positive(limits.max_yaw_acceleration) ||
    !finite_positive(limits.max_jerk))
  {
    throw std::invalid_argument("motion limits must be positive");
  }
  if (limits.steering_alignment_soft < 0.0 ||
    limits.steering_alignment_hard <= limits.steering_alignment_soft)
  {
    throw std::invalid_argument("steering alignment thresholds are invalid");
  }
}

DriveSetpoint compute_drive_setpoint(
  const Geometry & geometry,
  const MotionLimits & limits,
  const ChassisCommand & command)
{
  validate_geometry(geometry);
  validate_limits(limits);

  DriveSetpoint output;
  output.applied_command.linear_x = clamp_symmetric(
    std::isfinite(command.linear_x) ? command.linear_x : 0.0,
    limits.max_linear_speed);
  output.applied_command.angular_z = clamp_symmetric(
    std::isfinite(command.angular_z) ? command.angular_z : 0.0,
    limits.max_yaw_rate);

  if (!limits.allow_point_turn &&
    std::abs(output.applied_command.linear_x) < limits.minimum_linear_for_turn)
  {
    output.applied_command.angular_z = 0.0;
  }

  output.saturated =
    output.applied_command.linear_x != command.linear_x ||
    output.applied_command.angular_z != command.angular_z;

  const double linear = output.applied_command.linear_x;
  const double yaw = output.applied_command.angular_z;

  for (std::size_t steering_index = 0;
    steering_index < kSteeringWheelCount; ++steering_index)
  {
    const std::size_t wheel_index = kSteeringDriveIndexes[steering_index];
    const double local_x = linear - yaw * geometry.wheel_y[wheel_index];
    const double local_y = yaw * geometry.wheel_x[wheel_index];
    double angle = std::atan2(local_y, local_x);

    if (angle > kPi / 2.0) {
      angle -= kPi;
    } else if (angle < -kPi / 2.0) {
      angle += kPi;
    }

    const double limited_angle = std::clamp(
      angle,
      geometry.steering_min[steering_index],
      geometry.steering_max[steering_index]);
    output.saturated = output.saturated || limited_angle != angle;
    output.steering_angle[steering_index] = limited_angle;

    output.wheel_surface_speed[wheel_index] =
      local_x * std::cos(limited_angle) +
      local_y * std::sin(limited_angle);
  }

  for (const std::size_t wheel_index : {MIDDLE_LEFT, MIDDLE_RIGHT}) {
    output.wheel_surface_speed[wheel_index] =
      linear - yaw * geometry.wheel_y[wheel_index];
  }

  double maximum_requested = 0.0;
  for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
    output.wheel_angular_speed[index] =
      output.wheel_surface_speed[index] / geometry.wheel_radius[index];
    maximum_requested = std::max(
      maximum_requested,
      std::abs(output.wheel_angular_speed[index]));
  }

  if (maximum_requested > limits.max_wheel_angular_speed) {
    const double scale = limits.max_wheel_angular_speed / maximum_requested;
    for (std::size_t index = 0; index < kDriveWheelCount; ++index) {
      output.wheel_surface_speed[index] *= scale;
      output.wheel_angular_speed[index] *= scale;
    }
    output.applied_command.linear_x *= scale;
    output.applied_command.angular_z *= scale;
    output.saturated = true;
  }

  return output;
}

double steering_alignment_scale(
  const std::array<double, kSteeringWheelCount> & measured,
  const std::array<double, kSteeringWheelCount> & requested,
  const std::array<bool, kSteeringWheelCount> & healthy,
  double soft_error,
  double hard_error)
{
  if (soft_error < 0.0 || hard_error <= soft_error) {
    return 0.0;
  }

  double largest_error = 0.0;
  bool any_healthy = false;
  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    if (!healthy[index] || !std::isfinite(measured[index])) {
      continue;
    }
    any_healthy = true;
    largest_error = std::max(
      largest_error,
      std::abs(wrap_angle(requested[index] - measured[index])));
  }

  if (!any_healthy || largest_error >= hard_error) {
    return 0.0;
  }
  if (largest_error <= soft_error) {
    return 1.0;
  }
  return (hard_error - largest_error) / (hard_error - soft_error);
}

BodyTwistEstimate estimate_body_twist(
  const Geometry & geometry,
  const std::array<double, kDriveWheelCount> & measured_motor_velocity,
  const std::array<double, kSteeringWheelCount> & measured_steering,
  const std::array<bool, kDriveWheelCount> & drive_healthy,
  const std::array<bool, kSteeringWheelCount> & steering_healthy)
{
  BodyTwistEstimate estimate;
  double normal_00 = 0.0;
  double normal_01 = 0.0;
  double normal_11 = 0.0;
  double rhs_0 = 0.0;
  double rhs_1 = 0.0;
  std::size_t samples = 0;

  for (std::size_t wheel_index = 0; wheel_index < kDriveWheelCount; ++wheel_index) {
    if (!drive_healthy[wheel_index] ||
      !std::isfinite(measured_motor_velocity[wheel_index]))
    {
      continue;
    }

    double steering_angle = 0.0;
    const std::size_t steering_index = steering_index_for_drive(wheel_index);
    if (steering_index < kSteeringWheelCount) {
      if (!steering_healthy[steering_index] ||
        !std::isfinite(measured_steering[steering_index]))
      {
        continue;
      }
      steering_angle = measured_steering[steering_index];
    }

    const double output_velocity =
      measured_motor_velocity[wheel_index] *
      geometry.drive_direction[wheel_index] /
      geometry.drive_gear_ratio[wheel_index];
    const double surface_speed =
      output_velocity * geometry.wheel_radius[wheel_index];
    const double cosine = std::cos(steering_angle);
    const double sine = std::sin(steering_angle);
    const double yaw_coefficient =
      -geometry.wheel_y[wheel_index] * cosine +
      geometry.wheel_x[wheel_index] * sine;

    normal_00 += cosine * cosine;
    normal_01 += cosine * yaw_coefficient;
    normal_11 += yaw_coefficient * yaw_coefficient;
    rhs_0 += cosine * surface_speed;
    rhs_1 += yaw_coefficient * surface_speed;
    ++samples;
  }

  const double determinant = normal_00 * normal_11 - normal_01 * normal_01;
  if (samples < 2 || std::abs(determinant) < 1e-9) {
    return estimate;
  }

  estimate.linear_x = (rhs_0 * normal_11 - rhs_1 * normal_01) / determinant;
  estimate.angular_z = (normal_00 * rhs_1 - normal_01 * rhs_0) / determinant;
  estimate.valid = std::isfinite(estimate.linear_x) &&
    std::isfinite(estimate.angular_z);
  return estimate;
}

void CommandLimiter::reset()
{
  linear_ = 0.0;
  yaw_ = 0.0;
  linear_acceleration_ = 0.0;
  yaw_acceleration_ = 0.0;
}

ChassisCommand CommandLimiter::limit(
  const ChassisCommand & requested,
  const MotionLimits & limits,
  double period_seconds)
{
  validate_limits(limits);
  const double linear_target = clamp_symmetric(
    std::isfinite(requested.linear_x) ? requested.linear_x : 0.0,
    limits.max_linear_speed);
  const double yaw_target = clamp_symmetric(
    std::isfinite(requested.angular_z) ? requested.angular_z : 0.0,
    limits.max_yaw_rate);

  limited_axis(
    linear_target,
    linear_,
    linear_acceleration_,
    limits.max_linear_acceleration,
    limits.max_linear_deceleration,
    limits.max_jerk,
    period_seconds);
  limited_axis(
    yaw_target,
    yaw_,
    yaw_acceleration_,
    limits.max_yaw_acceleration,
    limits.max_yaw_acceleration,
    limits.max_jerk,
    period_seconds);
  return {linear_, yaw_};
}

double bounded_axis(double value, double deadzone)
{
  if (!std::isfinite(value)) {
    return 0.0;
  }
  const double bounded = std::clamp(value, -1.0, 1.0);
  return std::abs(bounded) < std::max(0.0, deadzone) ? 0.0 : bounded;
}

ChassisCommand map_drive_joystick(
  const std::array<double, 6> & axes,
  double max_linear_speed,
  double max_yaw_rate,
  double deadzone,
  double linear_sign,
  double yaw_sign)
{
  return {
    bounded_axis(axes[1], deadzone) * max_linear_speed * linear_sign,
    bounded_axis(axes[2], deadzone) * max_yaw_rate * yaw_sign};
}

}  // namespace spear_drive
