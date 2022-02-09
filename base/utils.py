from aiohttp import ClientSession, ClientResponse


__all__ = ['close_session']


async def close_session(client: ClientSession | None, session: ClientResponse | None) -> None:
    if client:
        await client.__aexit__(None, None, None)
    if session:
        await session.__aexit__(None, None, None)
