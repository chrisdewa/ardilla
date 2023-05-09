import asyncio


from tests import async_test, sync_test


sync_test.test()
asyncio.run(async_test.test())
