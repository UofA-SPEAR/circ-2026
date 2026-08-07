#ifndef SPEAR_DRIVE__FAULT_MANAGER_HPP_
#define SPEAR_DRIVE__FAULT_MANAGER_HPP_

#include <array>
#include <string>

#include "spear_drive/drive_core.hpp"

namespace spear_drive
{

enum class OperatingMode
{
  DISABLED,
  NOT_ZEROED,
  READY,
  ACTIVE,
  DEGRADED_5WD,
  DEGRADED_4WD,
  SENSOR_DEGRADED,
  FAULT_STOP,
};

struct FaultPolicy
{
  std::size_t minimum_available_drive_wheels{4};
  std::size_t minimum_available_wheels_per_side{2};
  double degraded_5wd_scale{0.65};
  double degraded_4wd_scale{0.35};
};

struct HealthSnapshot
{
  std::array<bool, kDriveWheelCount> drive_available{};
  std::array<bool, kDriveWheelCount> drive_encoder_healthy{};
  std::array<bool, kSteeringWheelCount> steering_encoder_healthy{};
  bool master_healthy{true};
  bool imu_healthy{true};
  bool steering_zeroed{false};
  bool command_fresh{false};
};

struct FaultDecision
{
  OperatingMode mode{OperatingMode::DISABLED};
  std::array<bool, kDriveWheelCount> drive_enabled{};
  double motion_scale{0.0};
  std::string reason{"disabled"};
};

FaultDecision evaluate_faults(
  const HealthSnapshot & health,
  const FaultPolicy & policy);

const char * mode_name(OperatingMode mode);

}  // namespace spear_drive

#endif  // SPEAR_DRIVE__FAULT_MANAGER_HPP_
