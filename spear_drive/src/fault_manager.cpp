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
  decision.drive_enabled = health.drive_available;

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

  const std::size_t total = static_cast<std::size_t>(std::count(
      decision.drive_enabled.begin(), decision.drive_enabled.end(), true));
  const std::size_t left = count_enabled(decision.drive_enabled, kLeftDriveIndexes);
  const std::size_t right = count_enabled(decision.drive_enabled, kRightDriveIndexes);
  if (total < policy.minimum_available_drive_wheels ||
    left < policy.minimum_available_wheels_per_side ||
    right < policy.minimum_available_wheels_per_side)
  {
    decision.drive_enabled.fill(false);
    decision.mode = OperatingMode::FAULT_STOP;
    decision.reason = "insufficient available drive actuators for bounded yaw control";
    return decision;
  }

  if (total < kDriveWheelCount - 1U) {
    decision.mode = OperatingMode::DEGRADED_4WD;
    decision.motion_scale = policy.degraded_4wd_scale;
    decision.reason = "multiple drive actuators isolated";
  } else if (total == kDriveWheelCount - 1U) {
    decision.mode = OperatingMode::DEGRADED_5WD;
    decision.motion_scale = policy.degraded_5wd_scale;
    decision.reason = "one drive actuator isolated";
  } else if (!std::all_of(
      health.drive_encoder_healthy.begin(), health.drive_encoder_healthy.end(),
      [](bool healthy) {return healthy;}) ||
    !std::all_of(
      health.steering_encoder_healthy.begin(), health.steering_encoder_healthy.end(),
      [](bool healthy) {return healthy;}) ||
    !health.imu_healthy)
  {
    decision.mode = OperatingMode::SENSOR_DEGRADED;
    decision.motion_scale = 1.0;
    decision.reason = "sensor feedback unavailable; continuing at commanded limits";
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
    case OperatingMode::SENSOR_DEGRADED: return "SENSOR_DEGRADED";
    case OperatingMode::FAULT_STOP: return "FAULT_STOP";
  }
  return "UNKNOWN";
}

}  // namespace spear_drive
