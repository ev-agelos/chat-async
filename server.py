import asyncio
import signal


HOST, PORT = '127.0.0.1', 8888
clients = {}


async def shutdown():
    for address, writer in clients.items():
        writer.write('Server is shutting down.'.encode())

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks)


async def handle_client(reader, writer):
    address = writer.get_extra_info('peername')
    clients[address] = writer
    await send(f"connected.", address)
    print(f"Client {address} connected.")

    while 1:
        data = await reader.read(100)
        if not data:
            del clients[address]
            writer.close()
            await send(f"disconnected.", address)
            print(f"Client {address} disconnected.")
            break
        await send(data, address)


async def send(data, address_from):
    if isinstance(data, bytes):
        data = data.decode()
    data = f"{address_from[0]}:{address_from[1]}: {data.rstrip()}\n"
    for address, writer in clients.items():
        if address != address_from:
            writer.write(data.encode())
            await writer.drain()


async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(shutdown())
    )

    server = await asyncio.start_server(
        handle_client, HOST, PORT)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        pass
