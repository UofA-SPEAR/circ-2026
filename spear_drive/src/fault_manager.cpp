#include "spear_drive/fault_manager.hpp"

#include <algorithm>
#include <cmath>

namespace spear_drive
{
namespace
{

constexpr std::array<std::size_t, 3> kLeftDriveIndexes = {
  FRONT_LEFT, MIDDLE_LEFT, REAR_LEFT};
constexpr std::array<std::size_t, 3> kRightDriveIndexes = {
  FRONT_RIGHT, MIDDLE_RIGHT, REAR_RIGHT};

std::size_t count_enabled(
  const std::array<bool, kDriveWheelCount> & enabled,
  const std::array<std::size_t, 3> & indexes)
{
  return static_cast<std::size_t>(std::count_if(
      indexes.begin(), indexes.end(),
      [&enabled](std::size_t index) {return enabled[index];}));
}

}  // namespace

FaultDecision evaluate_faults(
  const HealthSnapshot & health,
  const FaultPolicy & policy)
{
  FaultDecision decision;
  decision.drive_enabled = health.drive_healthy;

  if (!health.master_healthy) {
    decision.drive_enabled.fill(false);
    decision.mode = OperatingMode::FAULT_STOP;
    decision.reason = "EtherCAT master is not healthy";
    return decision;
  }
  if (!health.steering_zeroed) {
    decision.drive_enabled.fill(false);
    decision.mode = OperatingMode::NOT_ZEROED;
    decision.reason = "relative steering encoders are not zeroed";
    return decision;
  }
  if (!health.command_fresh) {
    decision.drive_enabled.fill(false);
    decision.mode = OperatingMode::READY;
    decision.reason = "waiting for a fresh drive command";
    return decision;
  }

  bool steering_limp = false;
  for (std::size_t index = 0; index < kSteeringWheelCount; ++index) {
    if (health.steering_healthy[index]) {
      continue;
    }
    const std::size_t drive_index = kSteeringDriveIndexes[index];
    decision.drive_enabled[drive_index] = false;
    if (!std::isfinite(health.last_valid_steering[index]) ||
      std::abs(health.last_valid_steering[index]) >
      policy.steering_straight_tolerance)
    {
      decision.drive_enabled.fill(false);
      decision.mode = OperatingMode::FAULT_STOP;
      decision.reason = "failed steering wheel is not known to be near straight";
      return decision;
    }
    steering_limp = true;
  }

  const std::size_t total = static_cast<std::size_t>(std::count(
      decision.drive_enabled.begin(), decision.drive_enabled.end(), true));
  const std::size_t left = count_enabled(decision.drive_enabled, kLeftDriveIndexes);
  const std::size_t right = count_enabled(decision.drive_enabled, kRightDriveIndexes);
  if (total < policy.minimum_healthy_drive_wheels ||
    left < policy.minimum_healthy_wheels_per_side ||
    right < policy.minimum_healthy_wheels_per_side)
  {
    decision.drive_enabled.fill(false);
    decision.mode = OperatingMode::FAULT_STOP;
    decision.reason = "insufficient healthy drive wheels for bounded yaw control";
    return decision;
  }

  if (steering_limp) {
    decision.mode = OperatingMode::STEER_LIMP;
    decision.motion_scale = policy.steering_limp_scale;
    decision.force_straight = true;
    decision.reason = "steering feedback lost near straight; corner drive isolated";
  } else if (total == 4) {
    decision.mode = OperatingMode::DEGRADED_4WD;
    decision.motion_scale = policy.degraded_4wd_scale;
    decision.reason = "two drive actuators isolated";
  } else if (total == 5) {
    decision.mode = OperatingMode::DEGRADED_5WD;
    decision.motion_scale = policy.degraded_5wd_scale;
    decision.reason = "one drive actuator isolated";
  } else if (!health.imu_healthy) {
    decision.mode = OperatingMode::IMU_DEGRADED;
    decision.motion_scale = policy.degraded_5wd_scale;
    decision.reason = "IMU unavailable; yaw stabilization and traction confidence reduced";
  } else {
    decision.mode = OperatingMode::ACTIVE;
    decision.motion_scale = 1.0;
    decision.reason = "all required feedback is healthy";
  }
  return decision;
}

const char * mode_name(OperatingMode mode)
{
  switch (mode) {
    case OperatingMode::DISABLED: return "DISABLED";
    case OperatingMode::NOT_ZEROED: return "NOT_ZEROED";
    case OperatingMode::READY: return "READY";
    case OperatingMode::ACTIVE: return "ACTIVE";
    case OperatingMode::DEGRADED_5WD: return "DEGRADED_5WD";
    case OperatingMode::DEGRADED_4WD: return "DEGRADED_4WD";
    case OperatingMode::STEER_LIMP: return "STEER_LIMP";
    case OperatingMode::IMU_DEGRADED: return "IMU_DEGRADED";
    case OperatingMode::FAULT_STOP: return "FAULT_STOP";
  }
  return "UNKNOWN";
}

}  // namespace spear_drive
