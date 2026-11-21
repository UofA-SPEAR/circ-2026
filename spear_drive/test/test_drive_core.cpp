#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <string>

#include "spear_drive/drive_core.hpp"
#include "spear_drive/fault_manager.hpp"

namespace
{

int failures = 0;

void expect(bool condition, const std::string & message)
{
  if (!condition) {
    std::cerr << "FAIL: " << message << '\n';
    ++failures;
  }
}

void expect_near(double actual, double expected, double tolerance, const std::string & message)
{
  expect(std::abs(actual - expected) <= tolerance, message);
}

spear_drive::Geometry geometry()
{
  spear_drive::Geometry value;
  value.wheel_x = {0.5, 0.5, 0.0, 0.0, -0.5, -0.5};
  value.wheel_y = {0.35, -0.35, 0.35, -0.35, 0.35, -0.35};
  value.wheel_radius.fill(0.13);
  value.drive_gear_ratio.fill(2.0);
  value.drive_direction = {1.0, -1.0, 1.0, -1.0, 1.0, -1.0};
  value.steering_min.fill(-0.78);
  value.steering_max.fill(0.78);
  value.steering_gear_ratio.fill(1.0);
  value.steering_direction = {1.0, -1.0, 1.0, -1.0};
  value.steering_offset.fill(0.0);
  return value;
}

spear_drive::MotionLimits limits()
{
  spear_drive::MotionLimits value;
  value.max_linear_speed = 2.0;
  value.max_yaw_rate = 2.0;
  value.max_wheel_angular_speed = 50.0;
  return value;
}

void test_kinematics()
{
  const auto model = geometry();
  const auto constraints = limits();
  const auto straight = spear_drive::compute_drive_setpoint(
    model, constraints, {0.5, 0.0});
  for (double angle : straight.steering_angle) {
    expect_near(angle, 0.0, 1e-12, "straight command keeps steering at zero");
  }
  for (double speed : straight.wheel_surface_speed) {
    expect_near(speed, 0.5, 1e-12, "straight command gives equal wheel surface speed");
  }

  const auto turn = spear_drive::compute_drive_setpoint(
    model, constraints, {0.6, 0.4});
  expect(turn.wheel_surface_speed[spear_drive::FRONT_RIGHT] >
    turn.wheel_surface_speed[spear_drive::FRONT_LEFT],
    "outside front wheel is faster in a left turn");
  expect(turn.steering_angle[spear_drive::STEER_FRONT_LEFT] > 0.0,
    "front wheels steer into a left turn");
  expect(turn.steering_angle[spear_drive::STEER_REAR_LEFT] < 0.0,
    "rear wheels counter-steer for a left turn");

  std::array<double, spear_drive::kDriveWheelCount> motor_velocity{};
  for (std::size_t index = 0; index < motor_velocity.size(); ++index) {
    motor_velocity[index] = turn.wheel_angular_speed[index] *
      model.drive_gear_ratio[index] * model.drive_direction[index];
  }
  std::array<bool, spear_drive::kDriveWheelCount> drive_health{};
  std::array<bool, spear_drive::kSteeringWheelCount> steering_health{};
  drive_health.fill(true);
  steering_health.fill(true);
  const auto estimate = spear_drive::estimate_body_twist(
    model, motor_velocity, turn.steering_angle, drive_health, steering_health);
  expect(estimate.valid, "body twist estimate is valid with six encoders");
  expect_near(estimate.linear_x, turn.applied_command.linear_x, 1e-9,
    "odometry recovers commanded linear speed");
  expect_near(estimate.angular_z, turn.applied_command.angular_z, 1e-9,
    "odometry recovers commanded yaw rate");

  const auto blocked_point_turn = spear_drive::compute_drive_setpoint(
    model, constraints, {0.0, 1.0});
  expect_near(blocked_point_turn.applied_command.angular_z, 0.0, 1e-12,
    "point turns remain disabled by default");

  auto saturated_constraints = constraints;
  saturated_constraints.max_wheel_angular_speed = 1.0;
  const auto saturated = spear_drive::compute_drive_setpoint(
    model, saturated_constraints, {2.0, 0.0});
  expect(saturated.saturated, "wheel-speed limit reports command saturation");
  expect(std::all_of(
      saturated.wheel_angular_speed.begin(), saturated.wheel_angular_speed.end(),
      [](double speed) {return std::abs(speed) <= 1.0 + 1e-12;}),
    "wheel-speed limit bounds every drive wheel");
}

void test_encoder_scaling()
{
  constexpr double kPi = 3.14159265358979323846;
  expect_near(
    spear_drive::encoder_counts_per_second_to_motor_velocity(28.0, 28.0),
    2.0 * kPi, 1e-12,
    "one encoder revolution per second converts to two pi rad/s");
  expect(std::isnan(
      spear_drive::encoder_counts_per_second_to_motor_velocity(28.0, 0.0)),
    "invalid encoder scale produces a non-finite state");

  double stale_duration = 0.0;
  expect(spear_drive::update_encoder_feedback_health(
      true, false, 0.0, true, 0.4, 0.75, 0.5, stale_duration),
    "stationary encoder is healthy when no motion is requested");
  expect(spear_drive::update_encoder_feedback_health(
      true, false, 2.0, true, 0.4, 0.75, 0.5, stale_duration),
    "unchanged encoder remains healthy inside stale timeout");
  expect(!spear_drive::update_encoder_feedback_health(
      true, false, 2.0, true, 0.4, 0.75, 0.5, stale_duration),
    "unchanged encoder becomes unhealthy after stale timeout");
  expect(spear_drive::update_encoder_feedback_health(
      true, true, 2.0, true, 0.01, 0.75, 0.5, stale_duration),
    "encoder count movement immediately restores feedback health");
  expect(!spear_drive::update_encoder_feedback_health(
      false, false, 2.0, true, 0.01, 0.75, 0.5, stale_duration),
    "non-finite encoder feedback is unhealthy without throwing");
}

void test_alignment_and_limiter()
{
  std::array<double, spear_drive::kSteeringWheelCount> measured{};
  std::array<double, spear_drive::kSteeringWheelCount> requested{};
  std::array<bool, spear_drive::kSteeringWheelCount> healthy{};
  healthy.fill(true);
  requested.fill(0.30);
  expect_near(
    spear_drive::steering_alignment_scale(measured, requested, healthy, 0.08, 0.25),
    0.0, 1e-12, "drive current is blocked for badly misaligned steering");
  requested.fill(0.10);
  const double partial = spear_drive::steering_alignment_scale(
    measured, requested, healthy, 0.08, 0.25);
  expect(partial > 0.0 && partial < 1.0, "steering alignment tapers drive current");
  healthy.fill(false);
  expect_near(
    spear_drive::steering_alignment_scale(measured, requested, healthy, 0.08, 0.25),
    1.0, 1e-12,
    "missing steering feedback does not scale the drive command");

  spear_drive::CommandLimiter limiter;
  auto constraints = limits();
  constraints.max_linear_acceleration = 0.5;
  constraints.max_jerk = 1.0;
  const auto limited = limiter.limit({2.0, 0.0}, constraints, 0.1);
  expect(limited.linear_x > 0.0 && limited.linear_x < 0.05,
    "jerk limiter prevents a full-speed step");
}

void test_encoderless_current_fallback()
{
  std::array<double, spear_drive::kDriveWheelCount> desired{};
  desired.fill(4.0);
  const std::array<double, spear_drive::kDriveWheelCount> direction = {
    1.0, -1.0, 1.0, -1.0, 1.0, -1.0};
  std::array<double, spear_drive::kDriveWheelCount> current{};
  std::array<bool, spear_drive::kDriveWheelCount> encoder_healthy{};
  std::array<bool, spear_drive::kDriveWheelCount> drive_enabled{};
  drive_enabled.fill(true);

  encoder_healthy[spear_drive::MIDDLE_LEFT] = true;
  current[spear_drive::MIDDLE_LEFT] = 0.6;
  expect_near(
    spear_drive::encoderless_current_command(
      spear_drive::FRONT_LEFT, desired, direction, current,
      encoder_healthy, drive_enabled, 0.0, 0.0, 10.0, 0.8),
    0.6, 1e-12,
    "failed left encoder copies normalized effort from a healthy left peer");

  encoder_healthy.fill(false);
  expect_near(
    spear_drive::encoderless_current_command(
      spear_drive::FRONT_RIGHT, desired, direction, current,
      encoder_healthy, drive_enabled, 0.0, 0.0, 10.0, 0.8),
    -0.32, 1e-12,
    "all-encoder-loss fallback scales open-loop current with requested speed");

  expect_near(
    spear_drive::encoderless_current_command(
      spear_drive::FRONT_RIGHT, desired, direction, current,
      encoder_healthy, drive_enabled, -0.7, 4.0, 10.0, 0.8),
    -0.7, 1e-12,
    "total encoder loss retains prior operating current before open-loop fallback");
}

spear_drive::HealthSnapshot healthy_snapshot()
{
  spear_drive::HealthSnapshot health;
  health.drive_available.fill(true);
  health.drive_encoder_healthy.fill(true);
  health.steering_encoder_healthy.fill(true);
  health.master_healthy = true;
  health.imu_healthy = true;
  health.steering_zeroed = true;
  health.command_fresh = true;
  return health;
}

void test_fault_policy()
{
  const spear_drive::FaultPolicy policy;
  auto health = healthy_snapshot();
  auto decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::ACTIVE,
    "healthy drivetrain enters ACTIVE");

  health.drive_encoder_healthy[spear_drive::FRONT_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::SENSOR_DEGRADED,
    "one failed drive encoder enters sensor-degraded mode");
  expect_near(decision.motion_scale, 1.0, 1e-12,
    "encoder loss does not reduce chassis commands");
  expect(decision.drive_enabled[spear_drive::FRONT_LEFT],
    "motor stays commanded when only its encoder is lost");

  health.drive_encoder_healthy.fill(false);
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::SENSOR_DEGRADED,
    "loss of every drive encoder remains a sensor fault");
  expect_near(decision.motion_scale, 1.0, 1e-12,
    "complete encoder loss retains the selected speed profile");
  expect(std::all_of(decision.drive_enabled.begin(), decision.drive_enabled.end(),
    [](bool enabled) {return enabled;}), "all working motors remain commanded");

  health = healthy_snapshot();
  health.drive_available[spear_drive::FRONT_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::DEGRADED_5WD,
    "an unavailable motor, unlike its encoder, enters five-wheel mode");
  expect(!decision.drive_enabled[spear_drive::FRONT_LEFT],
    "an unavailable motor controller is isolated");

  health.drive_available[spear_drive::REAR_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::FAULT_STOP,
    "one actually available wheel on a side cannot preserve bounded yaw control");

  health = healthy_snapshot();
  health.steering_encoder_healthy[spear_drive::STEER_FRONT_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::SENSOR_DEGRADED,
    "steering encoder loss remains a full-command sensor fault");
  expect_near(decision.motion_scale, 1.0, 1e-12,
    "steering encoder loss does not force crawl speed");

  health = healthy_snapshot();
  health.command_fresh = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::READY,
    "stale command returns to READY");
  expect(std::none_of(decision.drive_enabled.begin(), decision.drive_enabled.end(),
    [](bool enabled) {return enabled;}), "stale command disables all wheel commands");

  health = healthy_snapshot();
  health.master_healthy = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::FAULT_STOP,
    "EtherCAT master failure stops motion");

  health = healthy_snapshot();
  health.imu_healthy = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::SENSOR_DEGRADED,
    "IMU loss remains visible without disabling encoder-only driving");
  expect_near(decision.motion_scale, 1.0, 1e-12,
    "IMU loss does not reduce the selected speed profile");
}

void test_joystick_mapping()
{
  const std::array<double, 6> axes = {0.0, -1.0, -0.5, 0.0, 0.0, 0.0};
  const auto command = spear_drive::map_drive_joystick(
    axes, 0.5, 0.6, 0.08, -1.0, -1.0);
  expect_near(command.linear_x, 0.5, 1e-12, "joystick forward mapping");
  expect_near(command.angular_z, 0.3, 1e-12, "joystick yaw mapping");
}

}  // namespace

int main()
{
  test_kinematics();
  test_encoder_scaling();
  test_alignment_and_limiter();
  test_encoderless_current_fallback();
  test_fault_policy();
  test_joystick_mapping();
  if (failures != 0) {
    std::cerr << failures << " test(s) failed\n";
    return EXIT_FAILURE;
  }
  std::cout << "All spear_drive core tests passed\n";
  return EXIT_SUCCESS;
}
