import RPi.GPIO as GPIO
import serial
import time
import struct
from enum import Enum

#https://www.irobot.com/filelibrary/pdfs/hrd/create/Create%20Open%20Interface_v2.pdf

#todo, maybe throw exception if not in the right mode
#todo, should add docstrings with types of arguments
#todo: low side drivers (both methods), send ir, song, play song, sensors, query list, stream, pause/resume stream, script, play script, show script, wait time, wait distance, wait angle
#todo: should document start and end state(mode) of each command
#todo: test the demo commands and see if they work
#todo: should write out the table of notes somewhere, not really sure how to represent this

class Roomba(object):
    class StartCodes(Enum):
        START = 129

    class Demos(Enum):
        ABORT = 255
        COVER = 0
        COVER_AND_DOCK = 1
        SPOT_COVER = 2
        MOUSE = 3
        DRIVE_FIGURE_EIGHT = 4
        WIMP = 5
        HOME = 6
        TAG = 7
        PALCHELBEL = 8
        BANJO = 9

    BAUD_RATE_OPTIONS = {
        300 : 0,
        600 : 1,
        1200 : 2,
        2400 : 3,
        4800 : 4,
        9600 : 5,
        14400: 6,
        19200: 7,
        28800: 8,
        38400: 9,
        57600: 10,
        115200: 11
    }

    #should probably have fields for led data so that you can just update 1 bit at a time

    SAFE_MODE = 131
    FULL_MODE = 132

    BAUD_RATES = [19200, 57600]
    SERIAL_FILES = {'linux': 'none_yet', 'windows': 'none_yet', 'rpi-zero': '/dev/ttyAMA0', 'rpi-3': '/dev/serial0'}

    def __init__(self, dd_pin=7, baud_rate=BAUD_RATES[0], time_out=3.0, serial_file=SERIAL_FILES['rpi-3']):
        self.dd_pin = dd_pin
        self.baud_rate = baud_rate
        self.port = serial.Serial(serial_file, baudrate=baud_rate, timeout=time_out)
        self.port.close()
        self.port.open()

        #GPIO.setmode(GPIO.BOARD)
        #GPIO.setup(self.dd_pin, GPIO.OUT)
        #GPIO.output(self.dd_pin, GPIO.LOW)


    def turn_on(self): 
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.dd_pin, GPIO.OUT)

        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(.1)
        GPIO.output(self.dd_pin, GPIO.LOW)
        time.sleep(.5)
        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(2)
        
    def start(self):
        self.turn_on()
        self.write_num(128)
        self.write_num(131)
        time.sleep(1)


    def set_mode(self, mode):
        self.write_num(mode)
        time.sleep(1)

    def passive_mode(self):
        self.start()

    def safe_mode(self):
       self.set_mode(SAFE)

    def full_mode(self):
        self.set_mode(FULL)

    def passive_mode(self):
        self.set_mode(PASSIVE)

    def set_digits(self, digit1, digit2, digit3, digit4):
        self.safe_mode()
        self.write_num(164)
        #todo, should probably convert this to write_num
        self.port.write(digit1)
        self.port.write(digit2)
        self.port.write(digit3)
        self.port.write(digit4)

    def set_digits_string(self, msg):
        self.set_digits(msg[0], msg[1], msg[2], msg[3])

    #starts cleaning
    def cover(self):
        self.turn_on()
        self.write_num(135)

    def cover_and_dock(self):
        self.turn_on()
        self.write_num(143)

    def spot(self):
        self.turn_on()
        self.write_num(134)

    def power(self):
        self.write_num(133)

    #I think this should change the baud rate, untested
    def change_baudrate(self):
        self.power()
        self.turn_on()
        time.sleep(2)
        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.LOW)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.LOW)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.LOW)
        time.sleep(0.250)
        GPIO.output(self.dd_pin, GPIO.HIGH)
        time.sleep(2)

    def set_baud_mode(self, mode):
        self.write_num(129)
        self.write_num()
        self.sleep(0.100) #have to wait at least 100ms before sending new commands at the new baud rate
        #todo should change the baud rate on the serial connection

    def set_baudrate(self, baudrate):
        #should throw exception if baudrate is invalid
        self.set_baud_mode(self.BAUD_RATE_OPTIONS[baudrate])

    def run_demo(self, demo):
        self.write_num(demo)

    def drive(self, velocity, radius):
        #todo have bounds and special cases
        #v: -500 to 500 m/s
        #r: -2000 to 2000 mm
        #Straight = 32768 or 32767 = hex 8000 or 7FFF
        #Turn in place clockwise = hex FFFF
        #Turn in place counter-clockwise = hex 0001

        self.write_num(137)
        self.write_num((velocity >> 8) & 0xff)
        self.write_num(velocity & 0xff)
        self.write_num((radius >> 8) & 0xff)
        self.write_num(radius & 0xff)

    def drive_direct(self, right_velocity, left_velocity):
        #v: -500 to 500 m/s
        self.write_num(145)
        self.write_num((right_velocity >> 8) & 0xff)
        self.write_num(right_velocity & 0xff)
        self.write_num((left_velocity >> 8) & 0xff)
        self.write_num(left_velocity & 0xff)

    def set_LEDs(self, LED_bits, power_color, power_intensity):
        self.write_num(139)
        self.write_num(LED_bits)
        self.write_num(power_color)
        self.write_num(power_intensity)

        self.led_bits = LED_bits
        self.power_color = power_color
        self.power_intensity = power_intensity

    def set_power_LED(self, power_color, power_intensity):
        self.set_LEDs(led_bits, power_color, power_intensity)

    def set_advance_LED(self, led_bit): 
        self.set_LEDS(led_bits & ((led_bit & 1) << 3), power_color, power_intensity)

    def set_play_LED(self, led_bit): 
        self.set_LEDS(led_bits & ((led_bit & 1) << 1), power_color, power_intensity)

    #not entirely sure how this works, should add more about it later
    def pwm_low_side_drivers(self, duty_cycle_0, duty_cycle_1, duty_cycle_2):
        #max duty cycle is 128, multiply the percent of battery 
        #voltage that you want to use on the motor by the max duty cycle
        #todo should verify that it's in the right range (0-128)
        self.write_num(144)
        self.write_num(duty_cycle_2)
        self.write_num(duty_cycle_1)
        self.write_num(duty_cycle_0)

    #can't control speed of motors with this method, should use pwm_low_side_drivers instead
    def low_side_drivers(self, low_side_driver_0, low_side_driver_1, side_driver):
        self.write_num(138)
        bits = (low_side_driver_0 & 1)
        bits |= (low_side_driver_1 & 1) << 1
        bits |= (side_driver & 1) << 2
        self.write_num(bits)

    #not exactly sure what this really does
    def send_IR(self, value):
        self.write_num(151)
        self.write_num(value)

    # Scores are lists of tuples with each tuple being (note_num, note_duration)
    # with the first tuple indicating (song_number, song_length)
    sample_score = [(0, 3), (71, 64), (69, 64), (67, 64)]
    def write_song(score):
        self.write_num(140)
        self.write_num(score[0][0])
        self.write_num(score[0][1])
        for note in score[1:]:
            self.write_num(note[0])
            self.write_num(note[1])

    def play_song(self, song_number):
        #song_number 0-15
        self.write_num(141)
        self.write_num(song_number)

    def sensors(self, packet_id):
        #ids 0-42
        self.write_num(142)
        self.write_num(packet_id)
        sleep(0.015) #sensors are only updated every 15ms
        #todo need to read the sensor data from the serial port

    def query_list(self, packet_ids):
        #ids 0-42
        self.write_num(149)
        self.write_num(len(packet_ids))
        for packet_id in packet_ids:
            self.write_num(packet_id)
        sleep(0.015) #sensors are only updated every 15ms
        #todo need to read the sensor data back from the serial port

    def stream(self):
        pass

    def write_num(self, num):
        self.port.write(struct.pack('!B', num))

        #need to wait at least 200microseconds between characters when at 115200 baud rate 
        if self.baud_rate == 115200:
            time.sleep(200e-9) 

