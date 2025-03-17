import asyncio
import websockets

async def test_websocket():
    uri = 'ws://localhost:8006/ws/96c14b1e-919e-4e14-88e4-20cce08e2ced/observer'
    print(f'尝试连接到 {uri}')
    try:
        async with websockets.connect(uri) as websocket:
            print('连接成功！')
            await asyncio.sleep(2)
            print('关闭连接')
    except Exception as e:
        print(f'连接失败: {e}')

if __name__ == "__main__":
    asyncio.run(test_websocket()) 