# CIRC 2026 GPS Subsystem Requirements and Delivery Plan

Status: proposed baseline

Date: 2026-08-04

Target: CIRC Summer 2026, August 7–10, Drumheller, Alberta

## 1. Purpose

Deliver a dependable, offline GPS subsystem for the rover that supports the
CIRC 2026 Refreshment Delivery and Exploration Proposal tasks, feeds the
operator GUI, records evidence, and provides a clean foundation for later
autonomous navigation.

This document treats GPS as a subsystem, not only a serial driver. It covers:

1. The Adafruit Ultimate GPS Breakout V3 hardware connection.
2. ROS 2 acquisition and health monitoring.
3. WGS-84 waypoint and route handling.
4. Operator display and competition workflows.
5. Data capture and export for the Exploration Proposal report.
6. A later localization/autonomy path.

## 2. Competition-derived requirements

The official CIRC 2026 rules and task descriptions establish these inputs:

- Waypoints are supplied as WGS-84 latitude/longitude in decimal degrees at
  task start.
- The rules use travel to within 3 m of a provided GPS waypoint as an example
  autonomous action.
- Refreshment Delivery has seven gates. Their coordinates and directions of
  travel are supplied during setup, gates must be visited in order, and each
  gate must be traversed front-to-back.
- The February 2026 Q&A says autonomous navigation is not considered in the
  scoring of Refreshment Delivery. Reliable operator guidance therefore has
  higher immediate value than rushed autonomy.
- Exploration Proposal requires the rover to visit three team-selected sites
  at least 10 m apart, record each site's GPS coordinates, record the route,
  and produce a report map showing the start, three sites, and other features.
- Rover communications cannot depend on cell, satellite communication, or
  another external service. Maps, conversion, recording, and export must work
  offline.
- Most operation is within 50 m of the base station, but a rover may need to
  travel 200–300 m and may be behind terrain.

Sources:

- https://circ.cstag.ca/2026/rules/
- https://circ.cstag.ca/2026/tasks/
- https://circ.cstag.ca/2026/questions/
- https://learn.adafruit.com/adafruit-ultimate-gps?view=all

## 3. Current repository baseline

The repository is a ROS 2 Humble-style workspace. It currently contains:

- `spear_gui`: an operator GUI with a map image, manually entered coordinate
  markers, bearing graphics, and an in-memory route trace.
- `ultimate_gps_ros2`: a newly implemented hardware driver package, pending a
  ROS 2 Humble build and validation with the final GPS/serial hardware.
- No live GPS subscription in the GUI.
- No GPS diagnostics, mission/session recorder, persistent route export,
  waypoint queue, or site-capture workflow.
- No rover-base wheel odometry, IMU driver, localization EKF,
  `navsat_transform_node`, or Nav2 integration in this repository.
- Map bounds are currently hard-coded. This is not safe for a competition map
  that is provided at setup time.

## 4. System boundary and proposed architecture

```text
Ultimate GPS V3 --TTL UART/USB--> ultimate_gps_ros2
                                      | /gps/fix
                                      | /gps/velocity
                                      | /gps/nmea
                                      | /diagnostics
                                      v
                                gps_mission_manager
                                  | waypoints
                                  | distance/bearing
                                  | site snapshots
                                  | route/session files
                                  +--------------------> spear_gui
                                  +--------------------> ROS bag/log export

Later:
GPS + IMU + wheel odometry --> robot_localization --> local pose --> Nav2
```

The driver must run onboard the rover. The GUI may run onboard or at the base
station and must tolerate loss and restoration of the radio link without
corrupting the onboard recording.

## 5. Requirements

Priority meanings:

- P0: required before leaving for CIRC.
- P1: competition robustness; implement if P0 is stable.
- P2: post-P0 localization/autonomy work.

### 5.1 Hardware and electrical

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-HW-001 | P0 | Power the breakout within its supported 3.0–5.5 V input range and share signal ground with the serial host. | Measured supply remains in range through rover startup, drive, and E-stop cycles. |
| GPS-HW-002 | P0 | Connect GPS TX to host RX. Connect GPS RX to host TX when software configuration is enabled. Use TTL UART levels, not RS-232. | Valid NMEA is received at 9600 baud; PMTK acknowledgement/configuration is observable when TX is connected. |
| GPS-HW-003 | P0 | Mount the patch antenna facing the sky, away from high-current wiring, radios, motor controllers, and metal obstruction. | Outdoor fix is acquired and retained while the rover drives. |
| GPS-HW-004 | P0 | Provide strain relief, keyed connectors, and weather protection without covering the antenna with conductive material. | Cable and fix survive a 30-minute terrain drive and light enclosure spray test. |
| GPS-HW-005 | P0 | Give the receiver a stable Linux device path. Prefer a USB-TTL adapter identified by USB serial number and a udev symlink such as `/dev/spear_gps`. | Rebooting or reconnecting USB does not change the configured device path. |
| GPS-HW-006 | P1 | Fit and verify the backup coin cell supported by the specific board revision. | Warm restart is faster than a cold start and receiver settings/time retention behave as documented. |
| GPS-HW-007 | P1 | Use a compatible active external antenna if the rover structure blocks the onboard patch antenna. | Field comparison shows equal or improved fix availability/HDOP in the final mounting location. |
| GPS-HW-008 | P2 | Connect the 1 PPS output if sub-second sensor time alignment is needed. | PPS timestamps are visible and bounded against system time. |

### 5.2 ROS 2 GPS driver

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-DRV-001 | P0 | Read NMEA 0183 from a configurable serial port and baud rate. Use 9600 baud and a stable `/dev/spear_gps` competition configuration. | Launch file starts without source edits on the rover. |
| GPS-DRV-002 | P0 | Verify NMEA checksums and parse at least talker-independent GGA and RMC sentences. | Recorded GP/GN GGA and RMC fixtures pass; malformed and bad-checksum fixtures are rejected. |
| GPS-DRV-003 | P0 | Publish `sensor_msgs/msg/NavSatFix` on `/gps/fix`, raw sentences on `/gps/nmea`, and horizontal ground velocity on `/gps/velocity`. | `ros2 topic hz` and sample-value checks pass outdoors. |
| GPS-DRV-004 | P0 | Represent no-fix and stale data explicitly. Invalid coordinates must never be presented as a valid rover location or recorded as a site. | Removing the antenna/view of sky changes status without generating a false valid point. |
| GPS-DRV-005 | P0 | Configure the receiver for RMC+GGA at 5 Hz. Preserve a parameter to disable configuration for receive-only wiring. | Receiver output remains below the capacity of 9600 baud and both sentences arrive at the intended rate. |
| GPS-DRV-006 | P0 | Recover automatically from disconnects, device resets, malformed input, and temporary read failures. | Unplug/replug restores publishing within 5 s without restarting ROS. |
| GPS-DRV-007 | P0 | Publish health through `diagnostic_msgs/msg/DiagnosticArray`: connection, fix state, fix age, satellites, HDOP, NMEA rate, checksum errors, and reconnect count. | Operator can distinguish no device, no fix, degraded fix, and healthy fix. |
| GPS-DRV-008 | P0 | Timestamp messages consistently and report the age of the last receiver fix. | Healthy data age is less than 0.5 s at 5 Hz; stale status occurs within 2 s of input loss. |
| GPS-DRV-009 | P1 | Parse GSA/GST when available and use receiver accuracy data for covariance instead of only an HDOP approximation. | Covariance source is documented and visible in diagnostics. |
| GPS-DRV-010 | P1 | Publish receiver UTC/GPS time separately and detect large system-clock disagreement. | A time discrepancy produces a diagnostic warning without changing coordinates. |
| GPS-DRV-011 | P1 | Rate-limit repeated errors so a loose cable cannot fill disk or saturate the radio. | A 10-minute fault produces bounded logs and the reconnect counter still advances. |

### 5.3 Waypoints and operator guidance

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-MSN-001 | P0 | Accept WGS-84 decimal-degree latitude/longitude with at least 7 decimal places, validate ranges, and make swapped latitude/longitude difficult. | Known good coordinates round-trip without precision loss; invalid values are rejected with a clear message. |
| GPS-MSN-002 | P0 | Support quick entry/import of at least seven ordered gate waypoints during the 15-minute setup window. | An operator enters a seven-gate mission, including names and order, in under 3 minutes. |
| GPS-MSN-003 | P0 | Store a required direction-of-travel or approach heading for each gate. | GUI shows both the target bearing and required front-to-back gate direction. |
| GPS-MSN-004 | P0 | Compute geodesic distance and initial bearing from the current valid fix to the active waypoint. | Unit tests agree with trusted reference cases; live display updates at least once per second. |
| GPS-MSN-005 | P0 | Advance waypoints only by explicit operator action by default; optional radius-based arrival is advisory. | GPS jitter cannot silently skip a gate. |
| GPS-MSN-006 | P0 | Show GPS state, coordinates, fix age, satellites, HDOP/accuracy, active target, distance, bearing, and waypoint order in the GUI. | All fields can be demonstrated while the rover moves and while GPS is disconnected. |
| GPS-MSN-007 | P0 | Keep waypoint calculation and mission state onboard or otherwise functional without internet access. | Full workflow passes with all external networking disabled. |
| GPS-MSN-008 | P1 | Warn when a waypoint is implausibly far from the current competition area or duplicates another waypoint. | A sign error or copied coordinate outside a configurable radius produces a confirmation warning. |
| GPS-MSN-009 | P1 | Save and reload mission waypoint sets as human-readable YAML/CSV. | A saved seven-gate mission loads with identical order, names, coordinates, and headings. |

### 5.4 Exploration route and site recording

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-DAT-001 | P0 | Start a named session that records all valid fixes onboard, independent of GUI/radio availability. | A radio disconnect does not create a gap in the onboard track. |
| GPS-DAT-002 | P0 | Record UTC time, latitude, longitude, ellipsoid/MSL altitude when available, fix quality, satellites, HDOP/accuracy, speed, and course. | Exported rows contain the documented schema and no invalid fixes. |
| GPS-DAT-003 | P0 | Provide one-action capture for start, Site 1, Site 2, Site 3, and named landmarks. | Each capture is timestamped, labeled, and displayed on the route map. |
| GPS-DAT-004 | P0 | For a site snapshot, average a configurable window of valid stationary fixes and retain spread/quality values. | Default 10-second capture reports mean coordinates, sample count, horizontal spread, satellites, and HDOP. |
| GPS-DAT-005 | P0 | Warn if selected exploration sites are less than 10 m apart using conservative uncertainty handling. | Reference points at 9 m warn and points at 12 m pass under a good fix. |
| GPS-DAT-006 | P0 | Persist session data atomically in CSV and GeoJSON. Include a route line and labeled start/sites/landmarks. | Files remain readable after process termination and open in a standard offline GIS/viewer. |
| GPS-DAT-007 | P0 | Produce a report-ready PNG/PDF route map offline with a legend, north indication, scale, coordinate grid, route, and labeled sites. | Team can generate the map within 2 minutes after a field session. |
| GPS-DAT-008 | P0 | Preserve raw NMEA and a ROS bag option for forensic debugging. | A failed run can be replayed without the physical GPS. |
| GPS-DAT-009 | P1 | Add session notes and reason-for-route-change markers for the Exploration report. | Notes appear at the correct timestamp/location in export. |
| GPS-DAT-010 | P1 | Compute total distance, elapsed time, moving time, and per-leg distances. | Summary agrees within 2% of a known reference track. |

### 5.5 Maps and GUI behavior

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-GUI-001 | P0 | Replace hard-coded map bounds with a map configuration containing image path and WGS-84 bounds/control points. | A new competition map can be installed without changing Python. |
| GPS-GUI-002 | P0 | Subscribe to `/gps/fix` and diagnostics rather than moving the rover marker with keyboard test values. | Rover marker follows live/replayed GPS and freezes/changes style on stale data. |
| GPS-GUI-003 | P0 | Draw the actual route from persisted geographic samples rather than only in-memory screen pixels. | Pan/zoom or GUI restart does not distort or erase a loaded track. |
| GPS-GUI-004 | P0 | Show an accuracy circle and avoid presenting excessive coordinate precision as accuracy. | Display distinguishes stored precision from estimated uncertainty. |
| GPS-GUI-005 | P0 | Make failure states visually obvious but non-blocking: disconnected, searching, degraded, stale, recording, and storage error. | Each simulated failure has a distinct visible state and operator instruction. |
| GPS-GUI-006 | P1 | Provide copy/export buttons for current fix, selected site, mission list, and session files. | Operator can transfer values without manual retyping. |

### 5.6 Localization and autonomy foundation

| ID | Priority | Requirement | Acceptance criterion |
| --- | --- | --- | --- |
| GPS-AUT-001 | P2 | Add calibrated wheel odometry and IMU topics with correct frames and covariances. | TF and sensor streams pass `robot_localization` preparation checks. |
| GPS-AUT-002 | P2 | Fuse wheel odometry and IMU locally; use `navsat_transform_node` and GPS for global correction. | Local pose remains smooth between GPS updates and global drift is bounded outdoors. |
| GPS-AUT-003 | P2 | Define `map -> odom -> base_link -> gps_link` transforms and measure the GPS antenna lever arm. | TF tree has one authority per transform and no frame discontinuities. |
| GPS-AUT-004 | P2 | Add a supervised go-to-WGS84 action with pause/cancel, speed limits, geofence, stale-fix stop, and operator takeover. | Rover stops safely on cancel, GPS loss, localization fault, or boundary violation. |
| GPS-AUT-005 | P2 | Validate any autonomous claim under CIRC's no-operator-input rules and make autonomy mode visible to judges. | A documented drill completes without touching control computers during the declared interval. |

## 6. Performance and quality targets

- Receiver output: RMC+GGA at 5 Hz over 9600-baud TTL serial.
- Healthy ROS fix publication: 4–6 Hz, no unbounded backlog.
- Healthy data age: less than 0.5 s; stale threshold: 2 s.
- Serial recovery: less than 5 s after the device becomes available.
- Cold outdoor acquisition target: valid fix within 2 minutes under clear sky.
- Field position target: demonstrate a 95th-percentile horizontal error below
  3 m under open sky if a surveyed/reference position is available. This is a
  validation target, not an assumption; the receiver's advertised accuracy is
  close to CIRC's example 3 m autonomy radius.
- Coordinate storage: double precision; at least 7 decimal places on export.
- Route persistence: flush at least every second and on clean shutdown.
- No internet dependency at runtime.

## 7. Delivery plan for August 4–7

### Phase 0 — Hardware bring-up (August 4, 1–2 hours)

1. Identify the exact board revision, onboard computer, USB/UART adapter, and
   final mounting position.
2. Wire power, ground, TX/RX, add strain relief, and inspect raw 9600-baud NMEA.
3. Obtain an outdoor fix and record cold/warm acquisition time, satellites,
   HDOP, and dropouts while motors and radios operate.
4. Create `/dev/spear_gps` using the adapter's stable USB identity.

Exit criterion: raw valid GGA/RMC is stable on the final rover hardware.

### Phase 1 — Implement and harden the GPS driver (August 4, 3–5 hours)

1. Create the `ultimate_gps_ros2` package with serial acquisition, GGA/RMC
   parsing, ROS topics, diagnostics, stale-data handling, receiver ACK/rate
   verification, reconnect behavior, and bounded logging.
2. Add recorded NMEA fixtures for no-fix, valid fix, checksum failure,
   disconnect/reconnect, and both GP/GN talker IDs.
3. Add a hardware smoke-test command and a competition launch configuration.

Exit criterion: driver passes replay tests and unplug/replug recovery.

### Phase 2 — Mission and evidence recorder (August 4–5, 4–6 hours)

1. Implement session lifecycle, route persistence, site averaging, landmark
   capture, and CSV/GeoJSON export.
2. Implement waypoint import, ordered gate state, distance/bearing, and the
   10 m exploration-site separation warning.
3. Generate a report-ready offline route map.

Exit criterion: replayed NMEA produces complete files for a mock three-site
exploration and a seven-gate mission.

### Phase 3 — GUI integration (August 5, 4–8 hours)

1. Connect live fix and diagnostics to the existing map.
2. Make map georeferencing configurable.
3. Add fix-health, recording, waypoint, distance/bearing, site-capture, and
   export controls.
4. Remove demo/keyboard position behavior from the competition launch path.

Exit criterion: an operator completes both mock task workflows without a
terminal and understands every simulated failure state.

### Phase 4 — Field validation (August 5–6)

1. Perform cold boot, warm boot, USB reconnect, rover power cycle, radio loss,
   GUI restart, and disk interruption tests.
2. Drive a measured 200–300 m route over representative terrain.
3. Capture three known sites more than 10 m apart and generate the final
   report artifacts.
4. Enter and follow seven mock gates in order, including gate approach
   headings.
5. Replay the recorded run in the lab and fix only P0 defects.

Exit criterion: two consecutive end-to-end field runs complete with usable
exports and no manual code edits.

### Phase 5 — Competition readiness (August 6–7)

1. Freeze the working configuration and tag/commit the tested revision.
2. Prepare a spare cable/adapter, printed wiring diagram, launch cheat sheet,
   and known-good NMEA replay file.
3. Rehearse the 15-minute setup workflow and a GPS-failure fallback to manual
   camera driving plus written coordinate capture.
4. Assign one operator to mission/recording state and one person to verify
   exported evidence before teardown.

## 8. Explicitly deferred work

Do not spend the pre-event window building unsupervised waypoint autonomy from
this repository. It currently lacks the prerequisite base odometry, IMU fusion,
TF tree, local planning, obstacle detection, and safety validation. Complete P0
operator guidance and Exploration evidence first. Begin P2 only after two
consecutive P0 field passes or after CIRC.

## 9. Decisions needed from the team

These do not block the architecture, but must be resolved during Phase 0:

1. Exact onboard computer and operating system.
2. Direct UART versus a USB-to-TTL adapter, including adapter USB identity.
3. Exact GPS board marking: PA6H V3 or PA1616S/newer revision.
4. Whether an active external antenna and backup coin cell are available.
5. Final antenna location and measured offset from `base_link`.
6. Available wheel odometry, IMU model/topic, and base drive command interface.
7. Whether the immediate goal is competition telemetry/evidence only or also
   an experimental supervised autonomy demonstration.

## 10. Definition of done for CIRC P0

P0 is done only when all of the following are demonstrated on the final rover:

- Stable `/dev/spear_gps`, valid outdoor fix, and automatic serial recovery.
- Live position and honest health state in the GUI.
- Seven ordered waypoints can be entered quickly with gate direction, distance,
  and bearing.
- A session continues recording onboard through radio/GUI loss.
- Start, three sites, and landmarks can be captured; the 10 m check works.
- CSV, GeoJSON, raw/replay data, and a labeled route map are produced offline.
- Two consecutive field runs pass, including a power/reconnect fault.
- The team has a documented manual fallback if GPS fails at the task site.
