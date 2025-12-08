# lcd_driver.py
import time
from machine import I2C

LCD_ADDR = 0x3E

def lcd_cmd(i2c, cmd):
    i2c.writeto(LCD_ADDR, b'\x80' + bytes([cmd]))

def lcd_data(i2c, ch):
    i2c.writeto(LCD_ADDR, b'\x40' + bytes([ord(ch)]))

def pad_right(text, width=16):
    s = str(text)
    if len(s) > width:
        s = s[:width]
    if len(s) < width:
        s = s + (' ' * (width - len(s)))
    return s

def lcd_print(i2c, text, width=16):
    s = pad_right(text, width)
    for ch in s:
        b = ord(ch)
        if b < 32 or b > 126:
            b = ord('?')
        i2c.writeto(LCD_ADDR, b'\x40' + bytes([b]))

def lcd_write_line(i2c, line, text):
    addr = 0x80 if line == 0 else 0xC0
    lcd_cmd(i2c, addr)
    lcd_print(i2c, text)

def lcd_init(i2c):
    lcd_cmd(i2c, 0x38)  # Function set
    lcd_cmd(i2c, 0x0C)  # Display ON
    lcd_cmd(i2c, 0x01)  # Clear
    time.sleep_ms(2)




