from rpi_lcd import LCD


class LCDisplay:

    def __init__(self):
        self.lcd = LCD()

    def display_message(self, line1="", line2=""):
        """
        Muestra dos líneas en el LCD
        """

        self.lcd.clear()

        if line1:
            self.lcd.text(line1[:16], 1)

        if line2:
            self.lcd.text(line2[:16], 2)

    def clear(self):
        self.lcd.clear()