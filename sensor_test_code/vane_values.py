# Vane Values
#
# A script for calculating the Vout values for each of 16 resistance values
# resulting from the position of the wind vane at 3.3V.
#
# The wind vane datasheet provides output voltages based off of a 5V reference
# voltage. The Raspberry Pi logic levels are 3.3V.
#
# This script is also used for finding a suitable R1 value that separates the
# readings sufficiently to differentiate between them.

vane_resistances = [
    33000,
    6570,
    8200,
    891,
    1000,
    688,
    2200,
    1410,
    3900,
    3140,
    16000,
    14120,
    120000,
    42120,
    64900,
    21880,
]

# Technically, vout should be = (vin * r2) / (r1 + r2)
# I've left it like this because the Raspberry Pi tutorial did it this way and
# with a resistor of 4.7kohms there are 16 different readings. This works fine
# with the sensor. However, be aware that this voltage divider equation is wrong.
def voltage_divider(r1, r2, vin):
    vout = (vin * r1) / (r1 + r2)
    return round(vout, 1)


for x in range(len(vane_resistances)):
    print(vane_resistances[x], voltage_divider(4.7 * 1000, vane_resistances[x], 3.3))
