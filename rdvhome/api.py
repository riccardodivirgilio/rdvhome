

from rdvhome.signals import dispatch_status, dispatch_switch

from rpy.functions.datastructures import data

def api_response(status=200, **opts):
    return data(opts, status=status, success=status == 200)

async def status(*args, **opts):
    target = await dispatch_status(*args, **opts)

    return api_response(
        mode="status",
        status=target and 200 or 404,
        switches={serialized.id: serialized for serialized in target},
    )

async def switch(*args, **opts):
    target = await dispatch_switch(*args, **opts)

    return api_response(
        mode="switch",
        status=target and 200 or 404,
        switches=[obj.id for obj in target],
        **opts,
    )