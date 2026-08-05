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
    0.0, 1e-12, "drive torque is blocked for badly misaligned steering");
  requested.fill(0.10);
  const double partial = spear_drive::steering_alignment_scale(
    measured, requested, healthy, 0.08, 0.25);
  expect(partial > 0.0 && partial < 1.0, "steering alignment tapers drive torque");

  spear_drive::CommandLimiter limiter;
  auto constraints = limits();
  constraints.max_linear_acceleration = 0.5;
  constraints.max_jerk = 1.0;
  const auto limited = limiter.limit({2.0, 0.0}, constraints, 0.1);
  expect(limited.linear_x > 0.0 && limited.linear_x < 0.05,
    "jerk limiter prevents a full-speed step");
}

spear_drive::HealthSnapshot healthy_snapshot()
{
  spear_drive::HealthSnapshot health;
  health.drive_healthy.fill(true);
  health.steering_healthy.fill(true);
  health.last_valid_steering.fill(0.0);
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

  health.drive_healthy[spear_drive::FRONT_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::DEGRADED_5WD,
    "one failed drive enters five-wheel limp mode");
  expect(!decision.drive_enabled[spear_drive::FRONT_LEFT],
    "failed wheel is isolated");

  health.drive_healthy[spear_drive::REAR_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::FAULT_STOP,
    "one remaining wheel on a side cannot preserve bounded yaw control");
  expect(std::none_of(decision.drive_enabled.begin(), decision.drive_enabled.end(),
    [](bool enabled) {return enabled;}), "fault stop disables all wheel commands");

  health = healthy_snapshot();
  health.steering_healthy[spear_drive::STEER_FRONT_LEFT] = false;
  decision = spear_drive::evaluate_faults(health, policy);
  expect(decision.mode == spear_drive::OperatingMode::STEER_LIMP,
    "near-straight steering failure enters steer limp mode");
  expect(decision.force_straight, "steer limp forces a straight crawl");
  expect(!decision.drive_enabled[spear_drive::FRONT_LEFT],
    "drive behind failed steering is isolated");

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
  test_alignment_and_limiter();
  test_fault_policy();
  test_joystick_mapping();
  if (failures != 0) {
    std::cerr << failures << " test(s) failed\n";
    return EXIT_FAILURE;
  }
  std::cout << "All spear_drive core tests passed\n";
  return EXIT_SUCCESS;
}
