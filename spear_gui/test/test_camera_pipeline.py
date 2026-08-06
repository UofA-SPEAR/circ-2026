"""Tests for deterministic camera pipeline construction."""

import unittest

from spear_gui.camera_pipeline import build_pipeline


BASE_ARGS = {
    'camera_sn': 123456789,
    'receiver_ip': '192.168.10.11',
    'port': 5000,
    'bitrate': 4000000,
    'exposure': 10000,
    'gain': 30000,
}


class CameraPipelineTest(unittest.TestCase):
    """Verify source-specific properties in generated pipelines."""

    def test_zed_x_one_pipeline_pins_mode_and_names_payloader(self):
        pipeline = build_pipeline('zedxonesrc', **BASE_ARGS)

        self.assertIn('camera-resolution=2', pipeline)
        self.assertIn('camera-fps=30', pipeline)
        self.assertIn('rtph265pay name=pay', pipeline)
        self.assertIn('udpsink host=192.168.10.11 port=5000', pipeline)

    def test_stereo_pipeline_disables_depth_and_selects_left_image(self):
        pipeline = build_pipeline('zedsrc', **BASE_ARGS)

        self.assertIn('stream-type=0', pipeline)
        self.assertIn('depth-mode=0', pipeline)
        self.assertIn('camera-resolution=2', pipeline)
        self.assertIn('camera-fps=30', pipeline)

    def test_unknown_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported camera source'):
            build_pipeline('not-a-camera', **BASE_ARGS)


if __name__ == '__main__':
    unittest.main()
