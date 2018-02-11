from threading import Thread
from math import tan
import RPi.GPIO as GPIO
import time


def mandrel(m_step_channel, m_freq):
    """
        Important Note: Thread contents (such as PWM)only
        execute while the function is being used, ie stuck
        in a loop.
        
        Need to get carriage to terminate this when it is
        finished executing
    """
    m_step = GPIO.PWM(m_step_channel, m_freq)
    m_step.start(50)
    while True:
        pass

def carriage(c_step_channel, c_dir_channel, c_freq, c_distance):
    """
	This function is ran on the t2 thread.
	Its purpose is to give pulses to the carriages motor
	driver at a constant frequency as to translate the
	the mandrel horizontally at a constant velocity, then,
	after a certain amount of time, translate it in reverse.
    """
    c_step = GPIO.PWM(c_step_channel, c_freq)
    c_pass = 0; # the number of passes the carriage does
    c_step.start(50) # 50% duty cycle
    while c_pass < 50:
        GPIO.output(c_dir_channel, c_pass%2) # c_pass%2 to change direction
        delay = 83.333*c_distance/c_freq
        time.sleep(delay)
        c_pass = c_pass + 1
    c_step.stop()


def home(c_step_channel, c_dir_channel, c_limit_switch_channel):
    """
        
    """
    home_step = GPIO.PWM(c_step_channel, 60)
    while GPIO.input(c_limit_switch_channel) != 1:
        pass
    time.sleep(0.4) # debouncing button
    GPIO.output(c_dir_channel, 1)
    home_step.start(50)
    while GPIO.input(c_limit_switch_channel) != 1:
        pass
    GPIO.output(c_dir_channel, 0)
    time.sleep(0.1) # to move carriage away from limit switch
    home_step.stop()
    time.sleep (0.4) # debouncing button
    while GPIO.input(c_limit_switch_channel) != 1:
        pass


def main():

    """
	Notes:
	- Threading library: https://docs.python.org/2/library/threading.html
	- With wiring of stepper as documented on drive, the carriage travels
            toward the driving stepper when its pin is set to 1.
        - Mandrel and carriage steppers are assumed to have the same steps per
            revolution
		
    """
    ### Variable Input Parameters ###
    c_velocity = 1 # Inches per second
    wrap_angle = 70 # Degrees
    c_distance = 5 # Inches
    
    ### Output Channels ###
    m_step_channel = 12
    c_step_channel = 16
    c_dir_channel = 18
    c_limit_switch = 22
    
    ### Physical System Constants ###
    stepper_resolution = 200 # Steps per revolution
    m_radius = 1.75 # Inches
    c_pulley_teeth = 12
    c_pulley_pitch = 0.2 # Inches
    
    ### Governing Equations ###
    c_freq = c_velocity*stepper_resolution*c_pulley_pitch*c_pulley_teeth
    print(c_freq)
    m_freq = c_freq*tan(wrap_angle*3.14159/180)/(2*3.14159*c_pulley_pitch*c_pulley_teeth)
    print(m_freq)
    
    ### GPIO Setup ###
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD) # Use pin numbers for GPIO
    GPIO.setup(m_step_channel, GPIO.OUT)
    GPIO.setup(c_step_channel, GPIO.OUT)
    GPIO.setup(c_dir_channel, GPIO.OUT)
    GPIO.setup(c_limit_switch, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    
    ### Homing ###
    home(c_step_channel, c_dir_channel, c_limit_switch)
    
    ### Winding ###
    t1 = Thread(target=mandrel, args=(m_step_channel, m_freq))
    t2 = Thread(target=carriage, args=(c_step_channel, c_dir_channel, c_freq, c_distance))
    t2.start()
    t1.start()
    t2.join()

    GPIO.cleanup()


if __name__ == "__main__":
	main()