"""Tests for the eight-camera process topology."""

import unittest

from spear_gui.camera_groups import CAMERA_GROUPS, get_camera_group


class CameraGroupsTest(unittest.TestCase):
    """Guard the hardware inventory and native-process resource budget."""

    def test_four_groups_contain_all_eight_unique_cameras(self):
        cameras = [camera for group in CAMERA_GROUPS for camera in group]

        self.assertEqual(4, len(CAMERA_GROUPS))
        self.assertTrue(all(len(group) == 2 for group in CAMERA_GROUPS))
        self.assertEqual(8, len(cameras))
        self.assertEqual(8, len({camera["camera_sn"] for camera in cameras}))
        self.assertEqual(list(range(5000, 5008)), sorted(
            camera["port"] for camera in cameras
        ))

    def test_stereo_cameras_share_the_final_group(self):
        self.assertEqual(
            ["zedsrc", "zedsrc"],
            [camera["source"] for camera in CAMERA_GROUPS[-1]],
        )

    def test_invalid_group_index_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "group_index"):
            get_camera_group(len(CAMERA_GROUPS))


if __name__ == "__main__":
    unittest.main()
