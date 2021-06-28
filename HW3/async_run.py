from concurrent.futures import ProcessPoolExecutor
import asyncio
from functools import partial

executor = ProcessPoolExecutor()


async def async_run(task_func, *args):
    """
    Run task in executor as async coroutine
    :param task_func: name of function
    :param args: arguments
    :return function call results
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor,
        partial(task_func, *args)
    )