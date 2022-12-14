import asyncio
import json
import os
import shutil
from typing import Tuple

import aiofiles

import GetterPriceBinance
import mail_handler


class main_app:
    def __new__(cls):
        """
        Singleton. Sorry, sometimes I'm stupid.
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(main_app, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._mail_client = mail_handler.factory_mail_handler(mode="gmail")
        self._binance_websocket = GetterPriceBinance.book_ticker_price_binance(
            symbol="BTCUAH"
        )
        self._file_with_emails = "subscribed_emails.json"
        return

    def stop_binance_websocket(self):
        self._binance_websocket.stop_ws()

    async def get_rate(self) -> float:
        task_get_price = asyncio.create_task(
            self._binance_websocket.get_price("BTCUAH")
        )
        await task_get_price
        return task_get_price.result()

    async def _read_file_with_emails(self):
        data = []
        if os.path.exists(self._file_with_emails):
            async with aiofiles.open(self._file_with_emails, "r") as subscribed_emails:
                raw_data = await subscribed_emails.read()
                # print(f"raw_data is : {raw_data}")
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    copy_destination = (
                        (".".join(((str(self._file_with_emails)).split("."))[:-1]))
                        + "__saved."
                        + str(self._file_with_emails).split(".")[-1]
                    )
                    print(
                        f"!!! File subscribed_emails is broken. Copying it to {copy_destination}"
                    )
                    shutil.copy2(self._file_with_emails, copy_destination)
        return data

    async def _write_file_with_emails(self, data):
        async with aiofiles.open(self._file_with_emails, "w") as subscribed_emails:
            await subscribed_emails.write(json.dumps(data))

    async def subscribe(self, email: str) -> Tuple[(int, str)]:
        print(f"foo subscribe got email: {email}")
        data = await self._read_file_with_emails()
        if not email in data:
            data.append(email)
            await self._write_file_with_emails(data)
            return (200, "E-mail added")
        return (409, "E-mail already subscribed")

    async def send_emails(self, subject_text, message_plain_text):
        async with aiofiles.open(self._file_with_emails, "r") as subscribed_emails:
            list_subscribed_emails = json.loads(await subscribed_emails.read())
            self._mail_client.send_plain_messages_to_emails(
                list_subscribed_emails=list_subscribed_emails,
                subject_text=subject_text,
                message_plain_text=message_plain_text,
            )
        return
