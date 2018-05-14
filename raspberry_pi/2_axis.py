"""
	Release 1.0
	Feb. 16, 2018
	by Isaac Cormack
"""


from threading import Thread
from math import tan, cos, ceil
import RPi.GPIO as GPIO
import time


stepper_resolution = 200 # Steps per revolution
wrap_angle = 10 # Degrees
tow_width = 0.25 # Inches


class Mandrel():
    step_channel = 12
    encoder_switch_channel = 40
    radius = 0.875 # Inches
    length = 7 # Inches, This is the length of the wrap
    
    def __init__(self, c):
        self.freq = c.freq*c.pulley_teeth*c.pulley_pitch*tan(wrap_angle*3.14159/180)/(2*3.14159*self.radius)
    
    def start(self):
        """
            This function is ran on the t1 thread.
            Its purpose is to spin the mandrel at a calculated
            angular velocity according to the equation 2 while
            the carriage function is executing. After which point
            the both motors will stop.
        """
        step = GPIO.PWM(self.step_channel, self.freq)
        step.start(50)
        while True:
            pass


class Carriage():
    velocity = 3 # Inches per second
    step_channel = 16
    dir_channel = 18
    go_switch_channel = 36
    motor_switch_channel = 22
    far_end_switch_channel = 38
    pulley_teeth = 12
    pulley_pitch = 0.2 # Inches
    freq = velocity*stepper_resolution/(pulley_pitch*pulley_teeth)
    
    
    def home(self):
        home_step = GPIO.PWM(self.step_channel, 100)
        while GPIO.input(self.go_switch_channel) != 1:
            pass
        time.sleep(0.4) # debouncing button
        GPIO.output(self.dir_channel, 0) 
        home_step.start(50)
        while GPIO.input(self.motor_switch_channel) != 1:
            pass
        GPIO.output(self.dir_channel, 1)
        time.sleep(0.1) # to move carriage away from limit switch
        home_step.stop()
        time.sleep (0.4) # debouncing button
        while GPIO.input(self.go_switch_channel) != 1:
            pass


    def start(self, m):
        """
            This function is ran on the t2 thread.
            Its purpose is to give pulses to the carriages motor
            driver at a constant frequency as to translate the
            the mandrel horizontally at a constant velocity, then,
            after a certain amount of time, translate it in reverse.
        """
        step = GPIO.PWM(self.step_channel, self.freq)
        passes = 1; # The number of passes the carriage does
        passes_total = 2*3.14159*m.radius*cos(wrap_angle*3.14159/180)/tow_width # Total passes needed to cover mandrel once
        print("total passes")
        print(passes_total)
        wait = stepper_resolution*tow_width/(2*3.14159*m.radius*m.freq)
        count = 1
        GPIO.output(self.dir_channel, passes%2) # c_pass%2 to change direction
        while GPIO.input(m.encoder_switch_channel) != 1:
            pass
        step.start(50)
        while passes < 30: # + 1 because passes needs to start at 1 for dicerction
            if GPIO.input(self.motor_switch_channel) == 1:
                passes = passes + 1
                GPIO.output(self.dir_channel, passes%2) # c_pass%2 to change direction
                #the equation in sleep below is a linearization of .75 -> 0.09 and 3 -> 0.01s
                time.sleep(-velocity*0.03555555+0.1166666)
                step.ChangeDutyCycle(0)
                while GPIO.input(m.encoder_switch_channel) != 1:
                    pass
                time.sleep(wait*count)
                print("wait")
                count = count + 1
                step.ChangeDutyCycle(50)
                
            if GPIO.input(self.far_end_switch_channel) == 1:
                passes = passes + 1
                GPIO.output(self.dir_channel, passes%2) # c_pass%2 to change direction
                time.sleep(0.4)
        step.stop()
        

def main():

    """
	Notes:
	- Threading library: https://docs.python.org/2/library/threading.html
	- With wiring of stepper as documented on drive, the carriage travels
            toward the driving stepper when its pin is set to 0.
        - Mandrel and carriage steppers are assumed to have the same steps per
            revolution
		
    """
    c = Carriage()
    m = Mandrel(c)
        
    ### GPIO Setup ###
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD) # Use pin numbers for GPIO
    GPIO.setup(m.step_channel, GPIO.OUT)
    GPIO.setup(c.step_channel, GPIO.OUT)
    GPIO.setup(c.dir_channel, GPIO.OUT)
    GPIO.setup(c.motor_switch_channel, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(c.far_end_switch_channel, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(c.go_switch_channel, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.setup(m.encoder_switch_channel, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    
    ### Homing ###
    c.home()
    print("wrap angle")
    print(wrap_angle)
    print("mandrel freq")
    print(m.freq)
    print("carriage freq")
    print(c.freq)
    
    ### Winding ###
    t1 = Thread(target=m.start, args=())
    t2 = Thread(target=c.start, args=(m,))
    t2.start()
    t1.start()
    t2.join() # Wait until t2 is done executing then kill both threads

    GPIO.cleanup()


if __name__ == "__main__":
	main()
