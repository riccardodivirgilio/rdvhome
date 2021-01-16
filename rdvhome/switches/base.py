

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SWITCH

from rdvhome.switches.events import EventStream

from rpy.functions.asyncio import run_all
from rpy.functions.decorators import to_data
from rpy.functions.functional import iterate

class HomekitSwitch(Accessory):

    category = CATEGORY_SWITCH

    def __init__(self, driver, switch, event_name="on"):

        self.switch = switch
        self.event_name = event_name

        super().__init__(
            driver=driver,
            display_name=self.switch_name(),
            # aid=random_aid(self.switch_id())
        )
        run_all(self.switch.subscribe(self.on_event), loop=self.driver.loop)
        self.setup_services()

    def switch_name(self):
        return self.switch.name

    def perform_switch(self, *args, **opts):
        run_all(self.switch.switch(*args, **opts), loop=self.driver.loop)

    def set_on(self, value):
        self.perform_switch(value)

    def setup_services(self):
        service = self.add_preload_service("Switch")
        self.switch_service = service.configure_char(
            "On", setter_callback=self.set_on, value=None
        )

    async def on_event(self, event):
        try:
            self.switch_service.set_value(event[self.event_name])
        except KeyError:
            pass

class Switch(EventStream):

    kind = "switch"
    default_aliases = ["all"]

    homekit_class = HomekitSwitch

    def __init__(self, id, name=None, icon=None, visible=True, alias=(), ordering=0):
        self.id = id
        self.name = name or id
        self.alias = frozenset(iterate(self.id, alias, self.default_aliases, self.kind))
        self.ordering = ordering
        self.icon = icon

        self.visible = visible

        self.on = False

        self.hue = 1
        self.saturation = 0
        self.brightness = 1
        self.direction = None

        self.allow_on = False
        self.allow_hue = False
        self.allow_saturation = False
        self.allow_brightness = False
        self.allow_direction = False

        super().__init__()

    def create_homekit_accessory(self, driver):
        if self.homekit_class:
            return self.homekit_class(driver=driver, switch=self)

    @to_data
    def serialize(self):
        for attr in (
            "id",
            "name",
            "kind",
            "icon",
            "ordering",
            "allow_on",
            "allow_hue",
            "allow_saturation",
            "allow_brightness",
            "allow_direction",
            "direction",
            "on",
            "hue",
            "saturation",
            "brightness",
        ):
            yield attr, getattr(self, attr)

    async def update(self, **opts):

        changed = False

        for key, value in opts.items():
            if (not value is None) and (not getattr(self, key) == value):
                setattr(self, key, value)
                changed = True

                # print('changed %s: %s=%s' % (self.id, key, value))

        if changed:
            await self.send()

    async def send(self):
        event = self.serialize()
        await self.asend(event)
        return event

    async def switch(self, *args, **opts):
        raise NotImplementedError

    async def status(self):
        return await self.send()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.id)