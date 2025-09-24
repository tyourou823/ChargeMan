import asyncio
import threading
import psutil
from switchbot import Switchbot
from pystray import Icon, MenuItem as item, Menu
from PIL import Image, ImageDraw
import sys
from bleak import BleakScanner
from bleak import BleakClient

DEVICE_MAC = "XX:XX:XX:XX:XX:XX"  # PlugのMACアドレス
WRITE_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b" # UUID

CMD_ON  = bytearray([0x57, 0x01, 0x01])
CMD_OFF = bytearray([0x57, 0x01, 0x00])

charging = None  # 初期状態

async def turn_plug(on: bool):
    async with BleakClient(DEVICE_MAC) as client:
        if client.is_connected:
            print("接続成功")
            cmd = CMD_ON if on else CMD_OFF
            await client.write_gatt_char(WRITE_UUID, cmd)
            print("送信成功" if on else "電源OFFしました")
        else:
            print("接続失敗")

# タスクトレイアイコン生成（黒い電源アイコン）
def create_image():
    image = Image.new("RGB", (64, 64), "white")
    d = ImageDraw.Draw(image)
    d.rectangle([24, 16, 40, 48], fill="black")
    d.line([32, 0, 32, 16], fill="black", width=4)
    return image

# BLE制御関数（非同期）
async def control_plug(turn_on: bool):
    try:
        if turn_on:
            print("🔌 ON")
            await turn_plug(True)
        else:
            print("🔌 OFF")
            await turn_plug(False)

    except Exception as e:
        print(f"⚠ エラー: {e}")

# バッテリー監視ループ
async def monitor_battery():
    global charging
    while True:
        battery = psutil.sensors_battery()
        percent = battery.percent
        plugged = battery.power_plugged
        print(f"⚡ バッテリー: {percent}% / {'充電中' if plugged else '未接続'}")

        charging = plugged

        if percent >= 81 and charging:
            await control_plug(False)
        elif percent <= 78 and not charging:
            await control_plug(True)

        await asyncio.sleep(60)

# モニターを別スレッドで動かす
def start_monitoring():
    asyncio.run(monitor_battery())

# アプリ終了処理
def on_exit(icon, item):
    icon.stop()
    sys.exit()

# トレイアプリ開始
def setup_tray():
    image = create_image()
    menu = Menu(item("終了", on_exit))
    icon = Icon("Battery Monitor", image, menu=menu)
    threading.Thread(target=start_monitoring, daemon=True).start()
    icon.run()

if __name__ == "__main__":
    setup_tray()
