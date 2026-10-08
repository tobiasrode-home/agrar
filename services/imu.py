# ------------------------------------------------------------
# services/imu.py
# Tractor Board - MPU6050 Service
# ------------------------------------------------------------

import math

from kivy.clock import Clock
import smbus


# ------------------------------------------------------------
# MPU6050
# ------------------------------------------------------------

I2C_BUS = 1

MPU6050_ADDRESS = 0x68


# ------------------------------------------------------------
# Register
# ------------------------------------------------------------

WHO_AM_I = 0x75

PWR_MGMT_1 = 0x6B

ACCEL_CONFIG = 0x1C

GYRO_CONFIG = 0x1B

ACCEL_XOUT_H = 0x3B

TEMP_OUT_H = 0x41

GYRO_XOUT_H = 0x43


# ------------------------------------------------------------
# Messbereich
# ------------------------------------------------------------
#
# Accelerometer:
#
# ±2 g
# 16384 LSB / g
#
# Gyroskop:
#
# ±250 °/s
# 131 LSB / °/s
#
# ------------------------------------------------------------

ACCEL_SCALE = 16384.0

GYRO_SCALE = 131.0


# ------------------------------------------------------------
# Standard Update-Rate
# ------------------------------------------------------------

IMU_UPDATE_INTERVAL = 0.05
# 20 Hz


# ------------------------------------------------------------
# IMU Service
# ------------------------------------------------------------

class IMUService:

    def __init__(
        self,
        callback=None,
        update_interval=IMU_UPDATE_INTERVAL
    ):

        self.callback = callback

        self.update_interval = update_interval

        self.running = False

        self._event = None

        self.bus = None


        # ----------------------------------------------------
        # Rohdaten
        # ----------------------------------------------------

        self.accel_x = 0.0
        self.accel_y = 0.0
        self.accel_z = 0.0

        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0

        self.temperature = 0.0


        # ----------------------------------------------------
        # Lage
        # ----------------------------------------------------

        self.roll = 0.0
        self.pitch = 0.0


        # ----------------------------------------------------
        # Relative Z-Rotation
        #
        # Achtung:
        #
        # Das ist KEIN absoluter Kompasskurs.
        #
        # Es handelt sich lediglich um eine aus dem
        # Gyroskop integrierte relative Rotation.
        #
        # Sie driftet über längere Zeit.
        #
        # ----------------------------------------------------

        self.yaw = 0.0


        # ----------------------------------------------------
        # Letzte Zeit
        # ----------------------------------------------------

        self._last_time = None


    # ========================================================
    # START
    # ========================================================

    def start(self):

        if self.running:

            return


        print(
            "Initialisiere MPU6050...",
            flush=True
        )


        try:

            # ------------------------------------------------
            # I2C öffnen
            # ------------------------------------------------

            self.bus = smbus.SMBus(
                I2C_BUS
            )


            # ------------------------------------------------
            # Sensor prüfen
            # ------------------------------------------------

            device_id = self.bus.read_byte_data(
                MPU6050_ADDRESS,
                WHO_AM_I
            )


            print(
                f"MPU6050 WHO_AM_I: "
                f"0x{device_id:02X}",
                flush=True
            )


            # ------------------------------------------------
            # Sensor aufwecken
            # ------------------------------------------------

            self.bus.write_byte_data(
                MPU6050_ADDRESS,
                PWR_MGMT_1,
                0x00
            )


            # ------------------------------------------------
            # Accelerometer ±2g
            # ------------------------------------------------

            self.bus.write_byte_data(
                MPU6050_ADDRESS,
                ACCEL_CONFIG,
                0x00
            )


            # ------------------------------------------------
            # Gyroskop ±250 °/s
            # ------------------------------------------------

            self.bus.write_byte_data(
                MPU6050_ADDRESS,
                GYRO_CONFIG,
                0x00
            )


            # ------------------------------------------------
            # Zeitbasis zurücksetzen
            # ------------------------------------------------

            self._last_time = None


            # ------------------------------------------------
            # Service starten
            # ------------------------------------------------

            self.running = True


            self._event = Clock.schedule_interval(
                self._update,
                self.update_interval
            )


            print(
                "MPU6050 Service gestartet.",
                flush=True
            )


        except Exception as error:

            print(
                f"Fehler beim Start des "
                f"MPU6050: {error}",
                flush=True
            )


            if self.bus is not None:

                try:

                    self.bus.close()

                except Exception:

                    pass


                self.bus = None


            self.running = False


    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        if self._event is not None:

            self._event.cancel()

            self._event = None


        self.running = False


        if self.bus is not None:

            try:

                self.bus.close()

            except Exception:

                pass


            self.bus = None


        self._last_time = None


        print(
            "MPU6050 Service gestoppt.",
            flush=True
        )


    # ========================================================
    # 16-BIT SIGNED VALUE
    # ========================================================

    def _read_word(self, register):

        high = self.bus.read_byte_data(
            MPU6050_ADDRESS,
            register
        )

        low = self.bus.read_byte_data(
            MPU6050_ADDRESS,
            register + 1
        )


        value = (
            (high << 8) |
            low
        )


        if value >= 0x8000:

            value -= 65536


        return value


    # ========================================================
    # UPDATE
    # ========================================================

    def _update(self, dt):

        if not self.running:

            return


        if self.bus is None:

            return


        try:

            # ------------------------------------------------
            # Beschleunigung
            # ------------------------------------------------

            accel_x_raw = self._read_word(
                ACCEL_XOUT_H
            )

            accel_y_raw = self._read_word(
                ACCEL_XOUT_H + 2
            )

            accel_z_raw = self._read_word(
                ACCEL_XOUT_H + 4
            )


            # ------------------------------------------------
            # Temperatur
            # ------------------------------------------------

            temperature_raw = self._read_word(
                TEMP_OUT_H
            )


            # ------------------------------------------------
            # Gyroskop
            # ------------------------------------------------

            gyro_x_raw = self._read_word(
                GYRO_XOUT_H
            )

            gyro_y_raw = self._read_word(
                GYRO_XOUT_H + 2
            )

            gyro_z_raw = self._read_word(
                GYRO_XOUT_H + 4
            )


            # ------------------------------------------------
            # Umrechnung Accelerometer
            # ------------------------------------------------

            self.accel_x = (
                accel_x_raw /
                ACCEL_SCALE
            )

            self.accel_y = (
                accel_y_raw /
                ACCEL_SCALE
            )

            self.accel_z = (
                accel_z_raw /
                ACCEL_SCALE
            )


            # ------------------------------------------------
            # Umrechnung Gyroskop
            # ------------------------------------------------

            self.gyro_x = (
                gyro_x_raw /
                GYRO_SCALE
            )

            self.gyro_y = (
                gyro_y_raw /
                GYRO_SCALE
            )

            self.gyro_z = (
                gyro_z_raw /
                GYRO_SCALE
            )


            # ------------------------------------------------
            # Temperatur
            # ------------------------------------------------

            self.temperature = (
                temperature_raw /
                340.0
            ) + 36.53


            # ------------------------------------------------
            # Roll / Pitch aus Accelerometer
            # ------------------------------------------------
            #
            # Diese Werte funktionieren auch im Stillstand,
            # weil die Erdgravitation als Referenz dient.
            #
            # ------------------------------------------------

            self.roll = math.degrees(
                math.atan2(
                    self.accel_y,
                    self.accel_z
                )
            )


            self.pitch = math.degrees(
                math.atan2(
                    -self.accel_x,
                    math.sqrt(
                        self.accel_y ** 2 +
                        self.accel_z ** 2
                    )
                )
            )


            # ------------------------------------------------
            # Zeitdifferenz
            # ------------------------------------------------

            current_time = (
                Clock.get_time()
            )


            if self._last_time is not None:

                delta_time = (
                    current_time -
                    self._last_time
                )


                # --------------------------------------------
                # Relative Yaw-Rotation
                # --------------------------------------------

                self.yaw += (
                    self.gyro_z *
                    delta_time
                )


            self._last_time = current_time


            # ------------------------------------------------
            # Callback
            # ------------------------------------------------

            if self.callback:

                self.callback(
                    self.accel_x,
                    self.accel_y,
                    self.accel_z,
                    self.gyro_x,
                    self.gyro_y,
                    self.gyro_z,
                    self.temperature,
                    self.roll,
                    self.pitch,
                    self.yaw
                )


        except Exception as error:

            print(
                f"Fehler beim Lesen des "
                f"MPU6050: {error}",
                flush=True
            )


    # ========================================================
    # YAW ZURÜCKSETZEN
    # ========================================================

    def reset_yaw(self):

        self.yaw = 0.0

        self._last_time = (
            Clock.get_time()
        )
