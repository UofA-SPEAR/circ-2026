import math
import unittest

from ultimate_gps_ros2.nmea import (
    NmeaChecksumError,
    NmeaError,
    add_checksum,
    checksum_ok,
    parse_gga,
    parse_pmtk_ack,
    parse_rmc,
    sentence_type,
)


class TestNmea(unittest.TestCase):
    def test_parse_gga_reference_sentence(self):
        sentence = (
            "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,"
            "545.4,M,46.9,M,,*47"
        )
        fix = parse_gga(sentence)

        self.assertTrue(fix.valid)
        self.assertEqual(fix.talker, "GP")
        self.assertAlmostEqual(fix.latitude, 48.1173)
        self.assertAlmostEqual(fix.longitude, 11.5166666667)
        self.assertAlmostEqual(fix.altitude_ellipsoid, 592.3)
        self.assertEqual(fix.quality, 1)
        self.assertEqual(fix.satellites, 8)

    def test_parse_gn_talker(self):
        sentence = add_checksum(
            "GNGGA,120000.50,5128.2420,N,11245.1620,W,1,10,0.8,"
            "700.0,M,-15.0,M,,"
        ).decode("ascii")
        fix = parse_gga(sentence)

        self.assertEqual(fix.talker, "GN")
        self.assertAlmostEqual(fix.latitude, 51.4707)
        self.assertAlmostEqual(fix.longitude, -112.7527)
        self.assertAlmostEqual(fix.altitude_ellipsoid, 685.0)

    def test_parse_no_fix_gga(self):
        sentence = add_checksum(
            "GPGGA,120000.00,,,,,0,00,99.99,,,,,,"
        ).decode("ascii")
        fix = parse_gga(sentence)

        self.assertFalse(fix.valid)
        self.assertEqual(fix.quality, 0)
        self.assertTrue(math.isnan(fix.latitude))
        self.assertTrue(math.isnan(fix.longitude))

    def test_parse_rmc_reference_sentence(self):
        sentence = (
            "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,"
            "084.4,230394,003.1,W*6A"
        )
        fix = parse_rmc(sentence)

        self.assertTrue(fix.valid)
        self.assertAlmostEqual(fix.speed_mps, 11.5235456)
        self.assertAlmostEqual(fix.course_deg, 84.4)
        self.assertEqual(
            fix.timestamp.isoformat(),
            "1994-03-23T12:35:19+00:00",
        )

    def test_parse_void_rmc(self):
        sentence = add_checksum(
            "GPRMC,120000.00,V,,,,,,,040826,,,N"
        ).decode("ascii")
        fix = parse_rmc(sentence)

        self.assertFalse(fix.valid)
        self.assertEqual(fix.timestamp.isoformat(), "2026-08-04T12:00:00+00:00")

    def test_pmtk_acknowledgement(self):
        sentence = add_checksum("PMTK001,220,3").decode("ascii")
        acknowledgement = parse_pmtk_ack(sentence)

        self.assertEqual(acknowledgement.command, 220)
        self.assertTrue(acknowledgement.successful)
        self.assertEqual(sentence_type(sentence), "PMTK001")

    def test_add_checksum(self):
        command = add_checksum("PMTK220,200")
        self.assertEqual(command, b"$PMTK220,200*2C\r\n")
        self.assertTrue(checksum_ok(command.decode("ascii")))

    def test_rejects_bad_checksum(self):
        with self.assertRaises(NmeaChecksumError):
            parse_gga("$GPGGA,broken*00")

    def test_rejects_invalid_coordinate_minutes(self):
        sentence = add_checksum(
            "GPGGA,120000,4861.000,N,01131.000,E,1,08,0.9,"
            "545.4,M,46.9,M,,"
        ).decode("ascii")
        with self.assertRaises(NmeaError):
            parse_gga(sentence)

    def test_rejects_wrong_latitude_hemisphere(self):
        sentence = add_checksum(
            "GPGGA,120000,4807.000,E,01131.000,E,1,08,0.9,"
            "545.4,M,46.9,M,,"
        ).decode("ascii")
        with self.assertRaises(NmeaError):
            parse_gga(sentence)


if __name__ == "__main__":
    unittest.main()
