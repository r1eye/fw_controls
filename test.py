from math import tan, cos, ceil
import RPi.GPIO as GPIO
import time


if __name__ == "__main__":
    
    m_step_channel = 12
    c_step_channel = 16
    c_dir_channel = 18
    close_switch_channel = 22
    far_switch_channel = 32
    
    stepper_resolution = 200
    wrap_angle = 80
    radius = 0.875
    length = 6
    velocity = 0.5
    pulley_teeth = 12
    pulley_pitch = 0.2
    
    c_freq = velocity*stepper_resolution/(pulley_pitch*pulley_teeth)
    m_freq = c_freq*pulley_pitch*pulley_teeth*tan(wrap_angle*3.14159/180)/(2*3.14159*radius)
    delay = length*stepper_resolution/(pulley_pitch*pulley_teeth*c_freq)
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(m_step_channel, GPIO.OUT)
    GPIO.setup(c_step_channel, GPIO.OUT)
    GPIO.setup(c_dir_channel, GPIO.OUT)
    GPIO.setup(close_switch_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(far_switch_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    m_step = GPIO.PWM(m_step_channel, m_freq)
    c_step = GPIO.PWM(c_step_channel, c_freq)
    GPIO.output(c_dir_channel, 1)
    
    while GPIO.input(close_switch_channel) != 1:
        pass
    time.sleep(0.4)
    
    m_step.start(50)
    c_step.start(50)
    
    dir = 1
    
    while True:
        if GPIO.input(close_switch_channel):
            dir = dir + 1
            GPIO.output(c_dir_channel, dir%2)
            time.sleep(0.4)
            
    
    m_step.stop()
    c_step.stop()