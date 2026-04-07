import time

MPU6050_I2CADDR = 0x68

MPU6050_REGISTER_SMPLE_RATE_DIV = 0x19 #8 bit unsigned value, sample rate = 1/value
MPU6050_REGISTER_CONFIG = 0x1A #00 ext_sync_set (0-7) dlpf (0-7)
MPU6050_REGISTER_GYRO_CONFIG = 0x1B #self test x, y, z range (0-4)
MPU6050_REGISTER_ACCEL_CONFIG = 0x1C #self test x, y, z range (0-4)
MPU6050_REGISTER_INT_CONFIG = 0x37 #check docs
MPU6050_REGISTER_INT_ENABLE = 0x38 #check docs
MPU6050_REGISTER_ACCEL_X = 0x3B #2 bytes, 2's comp
MPU6050_REGISTER_ACCEL_Y = 0x3D #2 bytes, 2's comp
MPU6050_REGISTER_ACCEL_Z = 0x3F #2 bytes, 2's comp
MPU6050_REGISTER_TEMP = 0x41 #2 bytes, 2's comp
MPU6050_REGISTER_GYRO_X = 0x43 #2 bytes, 2'comp
MPU6050_REGISTER_GYRO_Y = 0x45 #2 bytes, 2'comp
MPU6050_REGISTER_GYRO_Z = 0x47 #2 bytes, 2'comp
MPU6050_REGISTER_START_ATEST = 0x1C #x, y, z, range, range, reserved...
MPU6050_REGISTER_START_GTEST = 0x1B #x, y, z, range, range, reserved...
MPU6050_REGISTER_XTEST_RESULTS = 0x0D #3 a, 5 g
MPU6050_REGISTER_YTEST_RESULTS = 0x0E #3 a, 5 g
MPU6050_REGISTER_ZTEST_RESULTS = 0x0F #3 a, 5 g
MPU6050_REGISTER_ALOW_RESULTS = 0x10 #3 reserved, 2 x a low, 2 y a low, 2 z a low
MPU6050_REGISTER_PATH_RESET = 0x68 #00000 gyro accel temp
MPU6050_REGISTER_USER_CONTROL = 0x6A #check docs
MPU6050_REGISTER_POWER_MGMNT1 = 0x6B #check docs
MPU6050_REGISTER_POWER_MGMNT2 = 0x6C #check docs

#big endian register storage
class MPU6050:
    
    def __init__(self, address=MPU6050_I2CADDR, i2c=None):
        if i2c is None:
            raise ValueError('An I2C object is required.')
        print(i2c)
        self._i2c = i2c
        self._i2caddr = 0x68
        #self._set_defaults()
        self._accel_scale = [1.0/16384.0, 1.0/8192.0, 1.0/4096.0, 1.0/2048.0]
        self._gyro_scale = [1.0/131, 1.0/65.5, 1.0/32.8, 1.0/16.4]
        self._arange = 3
        self._grange = 0
        #do a calibration_test() for new values
        self._driftAX = 1.06016
        self._driftAY = 0.049388168
        self._driftAZ = -0.039845625
        self._driftGX = -0.37136308
        self._driftGY = -2.7224848
        self._driftGZ = 0.0016828046
        self._inv = 0b0

        
        
    def _set_defaults(self):
        self.wake()
        self.set_sample_rate(0)
        self._set_power_defaults1(True, 0)
        self._set_power_defaults2(0b111000)
        self.set_accel_range(self._arange)
        self.set_gyro_range(self._grange)
        self._disable_fifo()
        self._disable_interrupts()
        self._set_config(0, 1)
        self._set_mot_det(0)
    #sample rate is set as 1/recip_value, 0 for max samples, 255 for min
    def set_sample_rate(self, recip_value):
        if recip_value < 0 or recip_value > 255:
            return ValueError('parameter must be within 0-255')
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_SMPLE_RATE_DIV, bytes([recip_value]))
    
    def _set_config(self, fsync, dlpf):
        if fsync < 0 or fsync > 7 or dlpf < 0 or dlpf > 7:
            return ValueError('parameter must be within 0-7')
        write = (fsync << 4) | dlpf
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_CONFIG, bytes([write]))
        
    def set_accel_range(self, arange):
        if arange < 0 or arange > 4:
            return ValueError('parameter must be within 0-3')
        self._arange = arange
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_ACCEL_CONFIG, bytes([arange << 3]))
        
    def set_gyro_range(self, grange):
        if grange < 0 or grange > 4:
            return ValueError('parameter must be within 0-3')
        self._grange = grange
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_CONFIG, bytes([grange << 3]))
        
    def _set_mot_det(self, msens):
        if msens < 0 or msens > 255:
            return ValueError('parameter must be within 0-255')
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_CONFIG, bytes([msens]))
        
    def _bytes_to_int(self, data):
        if not data[0] & 0x80:
            return data[0] << 8 | data[1]  # +ve
        return - (((data[0] ^ 255) << 8) | (data[1] ^ 255) + 1)
        
    def get_accelX(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_ACCEL_X, 2))
                                 *self._accel_scale[self._arange], self._driftAX, (self._inv >> 5) & 1)
        
    def get_accelY(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_ACCEL_Y, 2))
                                 *self._accel_scale[self._arange], self._driftAY, (self._inv >> 4) & 1)
        
    def get_accelZ(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_ACCEL_Z, 2))
                                 *self._accel_scale[self._arange], self._driftAZ, (self._inv >> 3) & 1)
        
    def get_gyroX(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_X, 2))
                                 *self._gyro_scale[self._grange], self._driftGX, (self._inv >> 2) & 1)
        
    def get_gyroY(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_Y, 2))
                                 *self._gyro_scale[self._grange], self._driftGY (self._inv >> 1) & 1)
        
    def get_gyroZ(self):
        return self._apply_drift(self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_Z, 2))
                                 *self._gyro_scale[self._grange], self._driftGZ, (self._inv >> 0) & 1)
    def set_inv_measures(self, invMeasure):
        if invMeasure < 0 or invMeasure > 63:
            return ValueError("pass in valid sensors to have measurements inverted as bits (ax, ay, az, gx, gy, gz)")
        self._inv = invMeasure
    #calibrates so readings return 0 when resting
    def calibration_test(self, activeSensors, invMeasure):
        if activeSensors < 0 or activeSensors > 63:
            return ValueError("pass in valid sensors to be calibrated as bits (ax, ay, az, gx, gy, gz)")
        if invMeasure < 0 or invMeasure > 63:
            return ValueError("pass in valid sensors to have measurements inverted as bits (ax, ay, az, gx, gy, gz)")
        self._inv = 0b0
        self._driftAX = 0.0
        self._driftAY = 0.0
        self._driftAZ = 0.0
        self._driftGX = 0.0
        self._driftGY = 0.0
        self._driftGZ = 0.0
        driftVals = [0]*6
        #set sensors
        self._set_power_defaults2(activeSensors)
        time.sleep(1)
        input("enter when the MPU is in a resting position")
        #to get an average
        start = time.ticks_ms()
        #time.ticks_diff would give a nonsense number without this sleep
        time.sleep(0.001)
        count = 0.0
        tempVals = [0]*6
        zVal = 0
        while time.ticks_diff(time.ticks_ms(), start) < 1000:
            measVals = []
            count += 1
            measVals.extend(self.get_accel())
            measVals.extend(self.get_gyro())
            print(measVals)
            print(tempVals)
            for i in range(0, 6):
                if not ((activeSensors >> i) & 1):
                    tempVals[i] += measVals[i]
        self._driftAX = tempVals[0] / count
        self._driftAY = tempVals[1] / count
        self._driftAZ = tempVals[2] / count
        self._driftGX = tempVals[3] / count
        self._driftGY = tempVals[4] / count
        self._driftGZ = tempVals[5] / count
        print("ax\t\tay\t\taz\t\tgx\t\tgy\t\tgz")
        print(self._driftAX, self._driftAY, self._driftAZ, self._driftGX, self._driftGY, self._driftGZ, sep="\t")
        self.set_inv_measures(invMeasure)
        
    #inv should be boolean true of false, 1 or 0.
    def _apply_drift(self, val, drift, inv):
        return (val - drift) * (inv * 2 + 1)

    def get_temp(self):
        return self._bytes_to_int(self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_TEMP, 2))/340 + 36.53
    
    def get_accel(self):
        data = self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_ACCEL_X, 6)
        x = self._bytes_to_int(data[0:2])*self._accel_scale[self._arange]
        y = self._bytes_to_int(data[2:4])*self._accel_scale[self._arange]
        z = self._bytes_to_int(data[4:6])*self._accel_scale[self._arange]
        fx = self._apply_drift(x, self._driftAX, (self._inv >> 5) * 1)
        fy = self._apply_drift(y, self._driftAY, (self._inv >> 4) * 1)
        fz = self._apply_drift(z, self._driftAZ, (self._inv >> 3) * 1)
        return fx, fy, fz
    
    def get_gyro(self):
        data = self._i2c.readfrom_mem(MPU6050_I2CADDR, MPU6050_REGISTER_GYRO_X, 6)
        x = self._bytes_to_int([data[0], data[1]])*self._gyro_scale[self._grange]
        y = self._bytes_to_int([data[2], data[3]])*self._gyro_scale[self._grange]
        z = self._bytes_to_int([data[4], data[5]])*self._gyro_scale[self._grange]
        fx = self._apply_drift(x, self._driftGX, (self._inv >> 2) * 1)
        fy = self._apply_drift(y, self._driftGY, (self._inv >> 1) * 1)
        fz = self._apply_drift(z, self._driftGZ, (self._inv >> 0) * 1)
        return fx, fy, fz
    
    def reset(self):
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_POWER_MGMNT1, bytes([(1 << 7)]))
        
    def wake(self):
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_POWER_MGMNT1, bytes([0]))

    def _set_power_defaults1(self, temp, clock):
        if not temp or not clock:
            return ValueError('temp must be true/false, clock must be 0-7')
        data = (temp << 3) | clock
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_POWER_MGMNT1, bytes([data]))
    
    def _set_power_defaults2(self, sensors):
        if sensors < 0 or sensors > 63:
            return ValueError('6 bits, on or off')
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_POWER_MGMNT2, bytes([sensors]))
    
    def _disable_interrupts(self):
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_INT_CONFIG, bytes([0]))
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_INT_ENABLE, bytes([0]))
        
    def _reset_sens(self, gyro=False, accel=False, temp=False):
        data = (gyro << 2) | (accel << 1) | temp
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_PATH_RESET, bytes([data]))
        
    def _disable_fifo(self):
        self._i2c.writeto_mem(MPU6050_I2CADDR, MPU6050_REGISTER_USER_CONTROL, bytes([0]))