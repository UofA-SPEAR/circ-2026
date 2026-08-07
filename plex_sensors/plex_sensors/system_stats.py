"""Publish host system stats (CPU / GPU / memory / network / power) on ROS topics.

CPU, RAM and network come from psutil and are always available. GPU load, board
power and the NVENC/NVDEC/VIC engine utilisations come from jetson-stats (jtop),
which only exists on an NVIDIA Jetson. The jtop side is guarded end to end: if the
library is missing, the service isn't running, or a particular stat key isn't
present in the installed jetson-stats version, that metric is simply skipped
(logged once) rather than crashing the node. It can also be turned off wholesale
with the `enable_jtop` parameter.

Each metric is published on its own topic as a std_msgs/Float64 (repo convention),
at a configurable rate. Topic/channel names match the Jetson panel the GUI already
expects (see spear_gui/spear_gui/defs_07_info_display.py).
"""

import time

import psutil
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

# jetson-stats is Jetson-only and installed via pip, not rosdep. Guard the import
# so the node still builds and runs (psutil-only) on a dev machine.
try:
    from jtop import jtop
except ImportError:
    jtop = None


# Metrics sourced from psutil -- always published.
PSUTIL_METRICS = ('cpu_usage', 'ram_usage', 'network_usage')
# Metrics sourced from jtop -- only published when jtop is active.
JTOP_METRICS = ('gpu_usage', 'jetson_power', 'nvenc', 'nvdec', 'vic')


class SystemStats(Node):
    def __init__(self):
        super().__init__('system_stats')

        self.declare_parameter('publish_rate_hz', 1.0)
        self.declare_parameter('enable_jtop', True)
        self.declare_parameter('topic_prefix', 'system_stats')
        self.declare_parameter('network_interface', '')
        self.declare_parameter('network_max_mbps', 1000.0)

        rate = float(self.get_parameter('publish_rate_hz').value)
        self.enable_jtop = bool(self.get_parameter('enable_jtop').value)
        self.prefix = self.get_parameter('topic_prefix').value
        self.net_iface = self.get_parameter('network_interface').value
        self.net_max_mbps = float(self.get_parameter('network_max_mbps').value)

        if rate <= 0.0:
            self.get_logger().warn(f'publish_rate_hz={rate} is invalid; defaulting to 1.0')
            rate = 1.0

        self._warned = set()          # metric keys we've already logged a problem for
        self._pubs = {}

        # psutil publishers + priming.
        for name in PSUTIL_METRICS:
            self._pubs[name] = self.create_publisher(Float64, f'{self.prefix}/{name}', 10)
        psutil.cpu_percent(interval=None)   # first call primes the delta; discard it
        self._last_net = (self._net_bytes(), time.monotonic())

        # jtop setup -- guarded. Only create the Jetson publishers if it actually starts.
        self._jtop = None
        self._start_jtop()

        period = 1.0 / rate
        self.create_timer(period, self._publish_stats)
        self.get_logger().info(
            f'system_stats publishing under "{self.prefix}/" at {rate:g} Hz '
            f'(jtop {"on" if self._jtop else "off"})'
        )

    # ──────────────────────────── jtop lifecycle ────────────────────────────

    def _start_jtop(self):
        if not self.enable_jtop:
            self.get_logger().info('enable_jtop=false; Jetson (GPU/power/engine) metrics disabled')
            return
        if jtop is None:
            self.get_logger().warn(
                'jetson-stats (jtop) not installed; Jetson metrics disabled. '
                'Install with: sudo pip3 install -U jetson-stats'
            )
            return
        try:
            self._jtop = jtop()
            self._jtop.start()
            for name in JTOP_METRICS:
                self._pubs[name] = self.create_publisher(Float64, f'{self.prefix}/{name}', 10)
        except Exception as e:
            self.get_logger().warn(f'could not start jtop ({e}); Jetson metrics disabled')
            self._jtop = None

    def shutdown(self):
        if self._jtop is not None:
            try:
                self._jtop.close()
            except Exception:
                pass
            self._jtop = None

    # ──────────────────────────── publishing ────────────────────────────

    def _publish_stats(self):
        self._publish('cpu_usage', psutil.cpu_percent(interval=None))
        self._publish('ram_usage', psutil.virtual_memory().percent)
        self._publish('network_usage', self._network_usage())

        if self._jtop is not None and self._jtop.ok():
            self._publish('gpu_usage', self._read_gpu())
            self._publish('jetson_power', self._read_power())
            self._publish('nvenc', self._read_engine('NVENC'))
            self._publish('nvdec', self._read_engine('NVDEC'))
            self._publish('vic', self._read_engine('VIC'))

    def _publish(self, name, value):
        """Publish a Float64 on the metric's topic; None means 'not available this tick'."""
        if value is None:
            return
        self._pubs[name].publish(Float64(data=float(value)))

    def _warn_once(self, key, msg):
        if key not in self._warned:
            self._warned.add(key)
            self.get_logger().warn(msg)

    # ──────────────────────────── metric readers ────────────────────────────

    def _net_bytes(self):
        if self.net_iface:
            counters = psutil.net_io_counters(pernic=True).get(self.net_iface)
            if counters is None:
                self._warn_once('net_iface', f'network_interface "{self.net_iface}" not found')
                return 0
        else:
            counters = psutil.net_io_counters()
        return counters.bytes_sent + counters.bytes_recv

    def _network_usage(self):
        """Return network throughput as a percentage of network_max_mbps."""
        now = time.monotonic()
        total = self._net_bytes()
        last_total, last_t = self._last_net
        self._last_net = (total, now)

        dt = now - last_t
        if dt <= 0.0 or self.net_max_mbps <= 0.0:
            return None
        mbps = (total - last_total) * 8.0 / 1e6 / dt
        return max(0.0, min(100.0, mbps / self.net_max_mbps * 100.0))

    def _read_gpu(self):
        """GPU load as a percentage, tolerant of jetson-stats version differences."""
        try:
            gpu = self._jtop.gpu
            # jetson-stats 4.x: {'gpu0': {'status': {'load': <pct>}, ...}, ...}
            if isinstance(gpu, dict):
                for entry in gpu.values():
                    status = entry.get('status', {}) if isinstance(entry, dict) else {}
                    if 'load' in status:
                        return float(status['load'])
            # older versions expose it via stats
            val = self._jtop.stats.get('GPU')
            if val is not None:
                return float(val)
        except Exception as e:
            self._warn_once('gpu', f'could not read GPU load from jtop ({e})')
        else:
            self._warn_once('gpu', 'GPU load not found in jtop data; skipping gpu_usage')
        return None

    def _read_power(self):
        """Total board power in watts (jtop reports milliwatts)."""
        try:
            power = self._jtop.power
            tot = power[0] if isinstance(power, (list, tuple)) else power.get('tot')
            if isinstance(tot, dict) and tot.get('power') is not None:
                return float(tot['power']) / 1000.0
        except Exception as e:
            self._warn_once('power', f'could not read power from jtop ({e})')
            return None
        self._warn_once('power', 'total power not found in jtop data; skipping jetson_power')
        return None

    def _read_engine(self, name):
        """Utilisation (%) for a hardware engine (NVENC/NVDEC/VIC).

        jetson-stats does not expose a true load for these; approximate from a
        'load' key when present, else current/max frequency, else online state.
        """
        try:
            info = self._find_engine(name)
            if info is None:
                self._warn_once(name, f'{name} engine not found in jtop data; skipping')
                return None
            if 'load' in info:
                return float(info['load'])
            cur, mx = info.get('cur'), info.get('max')
            if cur is not None and mx:
                return max(0.0, min(100.0, float(cur) / float(mx) * 100.0))
            if 'online' in info:
                return 100.0 if info['online'] else 0.0
        except Exception as e:
            self._warn_once(name, f'could not read {name} from jtop ({e})')
            return None
        self._warn_once(name, f'no usable {name} field in jtop data; skipping')
        return None

    def _find_engine(self, name):
        """Depth-first search of jtop's (possibly grouped) engine dict for `name`."""
        stack = [self._jtop.engine]
        while stack:
            node = stack.pop()
            if not isinstance(node, dict):
                continue
            for key, val in node.items():
                if isinstance(val, dict):
                    if key.upper() == name.upper() and (
                        'online' in val or 'load' in val or 'cur' in val
                    ):
                        return val
                    stack.append(val)
        return None


def main():
    rclpy.init()
    node = SystemStats()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
