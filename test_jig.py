from threading import Thread
from math import tan, cos, ceil
import RPi.GPIO as GPIO
import time


stepper_resolution = 200 # Steps per revolution
wrap_angle = 70 # Degrees

class Pulse():
    def __init__(self, pin_out, freq):
        
    def start():
        


class Mandrel():
    step_channel = 12
    radius = 1.75 # Inches
    length = 8 # Inches
    
    def __init__(self, c):
        self.freq = c.freq*tan(wrap_angle*3.14159/180)\
                    /(2*3.14159*c.pulley_pitch*c.pulley_teeth) # Equation 2
    
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
    velocity = 1 # Inches per second
    distance = 5 # Inches
    step_channel = 16
    dir_channel = 18
    limit_switch_channel = 22
    pulley_teeth = 12
    pulley_pitch = 0.2 # Inches
    freq = velocity*stepper_resolution*pulley_pitch*pulley_teeth # Equation 1
    
    
    def home(self):
        home_step = GPIO.PWM(self.step_channel, 100)
        while GPIO.input(self.limit_switch_channel) != 1:
            pass
        time.sleep(0.4) # debouncing button
        GPIO.output(self.dir_channel, 1)
        home_step.start(50)
        while GPIO.input(self.limit_switch_channel) != 1:
            pass
        GPIO.output(self.dir_channel, 0)
        time.sleep(0.1) # to move carriage away from limit switch
        home_step.stop()
        time.sleep (0.4) # debouncing button
        while GPIO.input(self.limit_switch_channel) != 1:
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
        passes = 0; # The number of passes the carriage does
        passes_total = 2*3.14159*cos(wrap_angle)/0.25 # Total passes needed to cover mandrel once
        latency = 0.2 # Delay of mandrel between passes on not motor end in inches
        offset_length = (2*m.length*tan(wrap_angle) + latency)%(2*3.14159*m.radius) # Inches
        offset_steps = stepper_resolution*offset_length/(2*3.14159*m.radius)
        delay = 83.333*self.distance/self.freq # Time it takes to travel one pass
        step.start(50)
        while passes <= ceil(passes_total):
            GPIO.output(self.dir_channel, passes%2) # c_pass%2 to change direction
            time.sleep(delay)
            if passes%2 != 0:
                step.stop()
                time.sleep(2)
                step.start(50) # BROKEN
                # delay(time it takes for mandrel to rotate offset steps + filament toe offset step)
            passes = passes + 1
        step.stop()
        

def main():

    """
	Notes:
	- Threading library: https://docs.python.org/2/library/threading.html
	- With wiring of stepper as documented on drive, the carriage travels
            toward the driving stepper when its pin is set to 1.
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
    GPIO.setup(c.limit_switch_channel, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    
    ### Homing ###
    c.home()
    
    ### Winding ###
    t1 = Thread(target=m.start, args=())
    t2 = Thread(target=c.start, args=(m,))
    t2.start()
    t1.start()
    t2.join() # Wait until t2 is done executing then kill both threads

    GPIO.cleanup()


if __name__ == "__main__":
	main()