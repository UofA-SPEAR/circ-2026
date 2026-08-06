# NEO-M9N-00B reference notes

This package targets the **u-blox NEO-M9N-00B** standard-precision GNSS
module. The implementation is based on these official u-blox documents:

- [NEO-M9N product page](https://www.u-blox.com/en/product/neo-m9n-module)
- [NEO-M9N-00B data sheet, UBX-19014285](https://content.u-blox.com/sites/default/files/NEO-M9N-00B_DataSheet_UBX-19014285.pdf)
- [NEO-M9N integration manual, UBX-19014286](https://content.u-blox.com/sites/default/files/NEO-M9N_Integrationmanual_UBX-19014286.pdf)
- [u-blox M9 SPG 4.04 interface description, UBX-21022436](https://content.u-blox.com/sites/default/files/u-blox-M9-SPG-4.04_InterfaceDescription_UBX-21022436.pdf)

Relevant factory defaults:

- UART: 38,400 baud, eight data bits, no parity, one stop bit.
- NMEA output: GGA, GLL, GSA, GSV, RMC, VTG and TXT.
- Input protocols: UBX, NMEA and RTCM 3.3.
- Default reception includes GPS, Galileo, GLONASS, BeiDou, QZSS and SBAS.
- The factory navigation rate is 1 Hz; the receiver supports up to 25 Hz.
- Typical multi-constellation position accuracy is specified as 2.0 m CEP.
- The bare module supply range is 2.7 V to 3.6 V.

The node intentionally consumes the factory NMEA stream and does not write
persistent receiver configuration. This prevents a failed host launch from
leaving the receiver in an unexpected competition configuration.
