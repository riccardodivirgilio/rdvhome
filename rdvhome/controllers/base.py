
class Controller(object):

    def __init__(self, id, power_control = {}, color_control = {}, direction_control = {}, **opts):
        self.id = id

        self.power_control = power_control
        self.color_control = color_control
        self.direction_control = direction_control

    def filter_switches_for(self, switches, command):
        return switches.filter(
            tuple(getattr(self, '%s_control' % command).keys())
        )

    async def switch(self, switches, command, value):
        return await getattr(self, 'switch_%s' % command)(switches, value)

    async def switch_power(self, switches, power):
        print('%s switching power for %s to %s' % (self, switches, power))

    async def switch_direction(self, switches, direction):
        print('%s switching direction for %s to %s' % (self, switches, direction))

    async def switch_color(self, switches, color):
        print('%s switching color for %s to %s' % (self, switches, color))