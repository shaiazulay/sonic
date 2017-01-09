/* Copyright (c) 2016 Arista Networks, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * The AMD SB800 Register Reference Guide details the behavior of the
 * SB800 accesses: http://support.amd.com/TechDocs/45482.pdf
 */

#include <linux/module.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/platform_device.h>
#include <linux/leds.h>
#include "gpio-kversfix.h"

#define NUM_FANS 4
#define DRIVER_NAME "sb800-fans"

#define SB800_BASE 0xfed80000
#define SB800_GPIO_BASE (SB800_BASE + 0x0100)
#define SB800_GPIO_SIZE 0xff
#define SB800_PM2_BASE (SB800_BASE + 0x0400)
#define SB800_PM2_SIZE 0xff
#define SB800_IOSIZE 4

#define FAN_ID_BASE_ADDR 0xCB
#define FAN_ID_ADDR_OFFSET 6
#define NUM_FAN_ID_PINS 3

#define FAN1_PRESENT_ADDR 206
#define FAN2_PRESENT_ADDR 212
#define FAN3_PRESENT_ADDR 220
#define FAN4_PRESENT_ADDR 224

#define GREEN_RED_LED_ADDR_OFFSET 1
#define FAN1_GREEN_LED_ADDR 207
#define FAN2_GREEN_LED_ADDR 213
#define FAN3_GREEN_LED_ADDR 218
#define FAN4_GREEN_LED_ADDR 225

#define OFF 0
#define RED 1
#define YELLOW 2
#define GREEN 3

#define LED_ON_OFF_REG_OFFSET (1 << 6)
#define LED_DIR_REG_OFFSET (1 << 5)

#define FAN_TACH_BASE_ADDR 0x69
#define FAN_TACH_ADDR_OFFSET 0x05
#define FAN_TACH_LOW_HI_ADDR_OFFSET 0x1

#define FAN_CTRL_BASE_ADDR 1
#define FAN_FREQ_BASE_ADDR 2
#define FAN_DUTY_BASE_ADDR 3
#define FAN_CTRL_ADDR_OFFSET 0x10

#define FAN_DETECT_CTRL_BASE_ADDR 0x66
#define FAN_DETECT_ADDR_OFFSET 0x05

#define FAN_PWM_BASE_ADDR 3
#define FAN_PWM_ADDR_OFFSET 0x10

struct raven_pdata {
   struct device *hwmon_dev;
   u8 *gpio_base;
   u8 *pm2_base;
};

static struct platform_device *sb800_pdev = 0;

unsigned long const green_led_addrs[NUM_FANS] = {FAN1_GREEN_LED_ADDR,
                                                 FAN2_GREEN_LED_ADDR,
                                                 FAN3_GREEN_LED_ADDR,
                                                 FAN4_GREEN_LED_ADDR};

static ssize_t show_fan_present(struct device *dev, struct device_attribute *attr,
                                char *buf)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   unsigned long const fan_present_addrs[] = {FAN1_PRESENT_ADDR, FAN2_PRESENT_ADDR,
                                              FAN3_PRESENT_ADDR, FAN4_PRESENT_ADDR};
   u32 num_fan = sensor_attr->index - 1;
   u8 *fan_present_reg = pdata->gpio_base + fan_present_addrs[num_fan];
   u32 fan_present_val = ((~ioread8(fan_present_reg)) >> 7) & 0x1;
   return scnprintf(buf, 5, "%u\n", fan_present_val);
}

static ssize_t show_fan_id(struct device *dev, struct device_attribute *attr,
                           char *buf)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   u32 fan_id = sensor_attr->index - 1;
   int num_id;
   u32 id_vals[NUM_FAN_ID_PINS];
   u8 *reg_id = pdata->gpio_base + FAN_ID_BASE_ADDR + FAN_ID_ADDR_OFFSET * fan_id;
   for(num_id = 0; num_id < NUM_FAN_ID_PINS; num_id++) {
      reg_id += num_id;
      id_vals[num_id] = (ioread8(reg_id) >> 7) & 0x1;
   }
  return scnprintf(buf, 12, "%u %u %u\n", id_vals[2], id_vals[1], id_vals[0]);
}

static ssize_t show_led_color(struct device *dev, struct device_attribute *attr,
                              char *buf)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   u32 fan_id = sensor_attr->index - 1;
   unsigned long const green_led_addr = green_led_addrs[fan_id];
   u8 *reg_g = pdata->gpio_base + green_led_addr;
   u8 *reg_r = reg_g + GREEN_RED_LED_ADDR_OFFSET;
   u32 val_g = ioread8(reg_g);
   u32 val_r = ioread8(reg_r);

   int color_index = OFF;

   if (!(val_g & LED_ON_OFF_REG_OFFSET) && (val_r & LED_ON_OFF_REG_OFFSET)) {
      color_index = GREEN;
   }
   else if ((val_g & LED_ON_OFF_REG_OFFSET) && !(val_r & LED_ON_OFF_REG_OFFSET)) {
      color_index = RED;
   }
   else if (!(val_g & LED_ON_OFF_REG_OFFSET) && !(val_r & LED_ON_OFF_REG_OFFSET)) {
      color_index = YELLOW;
   }
   return scnprintf(buf, 3, "%u\n", color_index);
}

static ssize_t store_led_color(struct device * dev, struct device_attribute * attr,
                               const char * buf, size_t count)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   u32 fan_id = sensor_attr->index - 1;
   int ret = 0;
   unsigned long value;
   unsigned long const green_led_addr = green_led_addrs[fan_id];
   u8 *reg_g = pdata->gpio_base + green_led_addr;
   u8 *reg_r = reg_g + GREEN_RED_LED_ADDR_OFFSET;
   u32 val_g = ioread8(reg_g);
   u32 val_r = ioread8(reg_r);

   ret = kstrtoul(buf, 10, &value);
   if (ret) {
      return ret;
   }
   // Enable output
   val_g &= ~LED_DIR_REG_OFFSET;
   val_r &= ~LED_DIR_REG_OFFSET;

   switch ((int)value) {
   case OFF:
      val_g |= LED_ON_OFF_REG_OFFSET;
      val_r |= LED_ON_OFF_REG_OFFSET;
      break;
   case RED:
      val_r &= ~LED_ON_OFF_REG_OFFSET;
      val_g |= LED_ON_OFF_REG_OFFSET;
      break;
   case YELLOW:
      val_g &= ~LED_ON_OFF_REG_OFFSET;
      val_r &= ~LED_ON_OFF_REG_OFFSET;
      break;
   default: // Green
      val_g &= ~LED_ON_OFF_REG_OFFSET;
      val_r |= LED_ON_OFF_REG_OFFSET;
      break;
   }
   iowrite8(val_g, reg_g);
   iowrite8(val_r, reg_r);
   return count;
}

static ssize_t show_fan_input(struct device *dev, struct device_attribute *attr,
                              char *buf)
{
   u32 tach = 0;
   u32 tach_lo;
   u32 tach_lo_1;
   u32 tach_hi;
   u32 tach_hi_1;
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   u32 fan_id = sensor_attr->index - 1;
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   unsigned long tach_lo_addr = FAN_TACH_BASE_ADDR +
                              (fan_id * FAN_TACH_ADDR_OFFSET );
   u8 *tach_lo_reg = pdata->pm2_base + tach_lo_addr;
   u8 *tach_hi_reg = tach_lo_reg + FAN_TACH_LOW_HI_ADDR_OFFSET;
   tach_lo = ioread8(tach_lo_reg);
   tach_hi = ioread8(tach_hi_reg);
   tach_lo_1 = ioread8(tach_lo_reg);
   tach_hi_1 = ioread8(tach_hi_reg);
   if (tach_lo_1 == tach_lo) {
      tach = (tach_hi << 8) + tach_lo;
   } else {
      tach = (tach_hi_1 << 8) + tach_lo_1;
   }
   tach = (22700 * 60) / ((tach ?: 1) * 2);
   return scnprintf(buf, 12, "%u\n", tach);
}

static ssize_t show_pwm(struct device *dev, struct device_attribute *attr, char *buf)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   u32 fan_id = sensor_attr->index - 1;
   u8 * reg = pdata->pm2_base + FAN_PWM_BASE_ADDR + (fan_id * FAN_PWM_ADDR_OFFSET);
   u32 pwm = ioread8(reg);
   return scnprintf(buf, 5, "%u\n", pwm);
}

static ssize_t store_pwm(struct device *dev, struct device_attribute *attr,
                         const char *buf, size_t count)
{
   struct raven_pdata *pdata = dev_get_drvdata(dev->parent);
   struct sensor_device_attribute *sensor_attr = to_sensor_dev_attr(attr);
   unsigned long pwm;
   int ret = 0;
   u32 fan_id = sensor_attr->index - 1;
   u8 * reg = pdata->pm2_base + FAN_PWM_BASE_ADDR + (fan_id * FAN_PWM_ADDR_OFFSET);
   ret = kstrtoul(buf, 10, &pwm);
   if (ret) {
      return ret;
   }
   iowrite8(pwm & 0xff, reg);
   return count;
}

#define FAN_DEVICE_ATTR(_numfan)                                                    \
static SENSOR_DEVICE_ATTR(fan##_numfan##_input, S_IRUGO,                            \
                          show_fan_input, NULL, _numfan);                           \
static SENSOR_DEVICE_ATTR(pwm##_numfan, S_IRUGO|S_IWUSR|S_IWGRP,                    \
                          show_pwm, store_pwm, _numfan);                            \
static SENSOR_DEVICE_ATTR(fan##_numfan##_present, S_IRUGO,                          \
                          show_fan_present, NULL, _numfan);                         \
static SENSOR_DEVICE_ATTR(fan##_numfan##_id, S_IRUGO,                               \
                          show_fan_id, NULL, _numfan);                              \
static SENSOR_DEVICE_ATTR(fan##_numfan##_led_color, S_IRUGO|S_IWUSR|S_IWGRP,        \
                          show_led_color, store_led_color, _numfan);

FAN_DEVICE_ATTR(1);
FAN_DEVICE_ATTR(2);
FAN_DEVICE_ATTR(3);
FAN_DEVICE_ATTR(4);

static struct attribute *fan_attrs[] = {
    &sensor_dev_attr_fan1_input.dev_attr.attr,
    &sensor_dev_attr_pwm1.dev_attr.attr,
    &sensor_dev_attr_fan1_led_color.dev_attr.attr,
    &sensor_dev_attr_fan1_present.dev_attr.attr,
    &sensor_dev_attr_fan1_id.dev_attr.attr,
    &sensor_dev_attr_fan2_input.dev_attr.attr,
    &sensor_dev_attr_pwm2.dev_attr.attr,
    &sensor_dev_attr_fan2_led_color.dev_attr.attr,
    &sensor_dev_attr_fan2_present.dev_attr.attr,
    &sensor_dev_attr_fan2_id.dev_attr.attr,
    &sensor_dev_attr_fan3_input.dev_attr.attr,
    &sensor_dev_attr_pwm3.dev_attr.attr,
    &sensor_dev_attr_fan3_led_color.dev_attr.attr,
    &sensor_dev_attr_fan3_present.dev_attr.attr,
    &sensor_dev_attr_fan3_id.dev_attr.attr,
    &sensor_dev_attr_fan4_input.dev_attr.attr,
    &sensor_dev_attr_pwm4.dev_attr.attr,
    &sensor_dev_attr_fan4_led_color.dev_attr.attr,
    &sensor_dev_attr_fan4_present.dev_attr.attr,
    &sensor_dev_attr_fan4_id.dev_attr.attr,
    NULL,
};

ATTRIBUTE_GROUPS(fan);

static void set_led_init_state(struct device * dev)
{
   int num_fan;
   u8 *reg_g = NULL;
   u8 *reg_r = NULL;
   unsigned long green_led_addr;
   u8 val_g, val_r;
   struct raven_pdata *pdata = dev_get_drvdata(dev);

   for(num_fan = 0; num_fan < NUM_FANS; num_fan++) {
      green_led_addr = green_led_addrs[num_fan];
      reg_g = pdata->gpio_base + green_led_addr;
      reg_r = reg_g + GREEN_RED_LED_ADDR_OFFSET;
      val_g = ioread8(reg_g);
      val_r = ioread8(reg_r);
      val_g &= ~LED_DIR_REG_OFFSET;
      val_r &= ~LED_DIR_REG_OFFSET;
      val_g |= LED_ON_OFF_REG_OFFSET;
      val_r |= LED_ON_OFF_REG_OFFSET;
      iowrite8(val_g, reg_g);
      iowrite8(val_r, reg_r);
   }
}

static void set_fan_init_state(struct device * dev)
{
   int num_fan;
   struct raven_pdata *pdata = dev_get_drvdata(dev);
   u8 *reg = pdata->pm2_base;
   unsigned long fan_ctrl_offset;
   for (num_fan = 0; num_fan < NUM_FANS; num_fan++) {
      fan_ctrl_offset = FAN_CTRL_ADDR_OFFSET * num_fan;
      iowrite8(0x06, reg + fan_ctrl_offset); /*FanInputControl*/
      iowrite8(0x04, reg + FAN_CTRL_BASE_ADDR + fan_ctrl_offset);
      iowrite8(0x01, reg + FAN_FREQ_BASE_ADDR + fan_ctrl_offset);
      iowrite8(0xff, reg + FAN_DUTY_BASE_ADDR + fan_ctrl_offset);

      iowrite8(0x01, reg + FAN_DETECT_CTRL_BASE_ADDR + (FAN_DETECT_ADDR_OFFSET *
               num_fan));
   }
}

static s32 sb_fan_probe(struct platform_device *pdev)
{
   int ret = 0;
   struct raven_pdata *pdata = devm_kzalloc(&pdev->dev, sizeof(struct raven_pdata),
                                            GFP_KERNEL);

   if (!request_mem_region(SB800_PM2_BASE, SB800_PM2_SIZE, "SB800_PM2")) {
      dev_err(&pdev->dev, "failed request_mem_region in SB fan initialization\n");
      ret = -EBUSY;
      goto fail_request_pm_region;
   }
   pdata->pm2_base = ioremap(SB800_PM2_BASE, SB800_PM2_SIZE );

   if (!request_mem_region(SB800_GPIO_BASE, SB800_GPIO_SIZE, "SB800_GPIO")) {
      dev_err(&pdev->dev, "Failed request_mem_region in SB GPIO initialization");
      ret = -EBUSY;
      goto fail_request_gpio_region;
   }
   pdata->gpio_base = ioremap(SB800_GPIO_BASE, SB800_GPIO_SIZE);

   pdata->hwmon_dev = hwmon_device_register_with_groups(&pdev->dev, "fans", NULL,
                                                        fan_groups);
   if (IS_ERR(pdata->hwmon_dev)) {
      dev_err(&pdev->dev, "failed to create hwmon sysfs entries\n");
      ret = PTR_ERR(pdata->hwmon_dev);
      goto fail_hwmon_register;
   }
   platform_set_drvdata(pdev, pdata);
   set_led_init_state(&pdev->dev);
   set_fan_init_state(&pdev->dev);

   return ret;

fail_hwmon_register:
   release_mem_region(SB800_GPIO_BASE, SB800_GPIO_SIZE);
   iounmap(pdata->gpio_base);
fail_request_gpio_region:
   release_mem_region(SB800_PM2_BASE, SB800_PM2_SIZE);
   iounmap(pdata->pm2_base);
fail_request_pm_region:
   return ret;
}

static int sb_fan_remove(struct platform_device *pdev)
{
   int err = 0;
   struct raven_pdata *pdata = platform_get_drvdata(pdev);
   iounmap(pdata->gpio_base);
   iounmap(pdata->pm2_base);
   release_mem_region(SB800_PM2_BASE, SB800_PM2_SIZE);
   release_mem_region(SB800_GPIO_BASE, SB800_GPIO_SIZE);
   hwmon_device_unregister(pdata->hwmon_dev);
   return err;
}

static int __init sb_fan_init(void)
{
    int err;
    struct platform_device *pdev = NULL;

    pdev = platform_device_register_simple(DRIVER_NAME, -1, NULL, 0);

    if (IS_ERR(pdev)) {
        printk(KERN_ERR "failed to register " DRIVER_NAME);
        return PTR_ERR(pdev);
    }

    err = sb_fan_probe(pdev);

    if (err) {
        dev_err(&pdev->dev, "failed to init device ");
        platform_device_unregister(pdev);
        return err;
    }

    sb800_pdev = pdev;

    return err;
}

static void __exit sb_fan_exit(void)
{
    if (!sb800_pdev) {
        return;
    }

    sb_fan_remove(sb800_pdev);
    platform_device_unregister(sb800_pdev);

    sb800_pdev = 0;
}

module_init(sb_fan_init);
module_exit(sb_fan_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("Raven Fan Driver");
