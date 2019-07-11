# Copyright (c) 2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from .i2c import I2cKernelDriver

class Max6697KernelDriver(I2cKernelDriver):
   def __init__(self, name='max6697', module='max6697', **kwargs):
      super(Max6697KernelDriver, self).__init__(name=name, module=module, **kwargs)
