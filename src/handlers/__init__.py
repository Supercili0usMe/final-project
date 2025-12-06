from aiogram import Router


def setup_routers() -> Router:
    from . import client_area, start, subscription, commands, keys_interaction

    router = Router()
    router.include_router(subscription.router)
    router.include_router(start.router)
    router.include_router(client_area.router)
    router.include_router(commands.router)
    router.include_router(keys_interaction.router)

    return router
