"""
钉钉机器人通知客户端
支持 Webhook URL + HmacSHA256 加签安全验证
"""
import asyncio
import hashlib
import hmac
import base64
import time
import urllib.parse
from typing import Dict, Optional

import requests

from .base import NotificationClient


class DingTalkClient(NotificationClient):
    """钉钉机器人通知客户端"""

    channel_key = "dingtalk"
    display_name = "钉钉"

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None,
        pcurl_to_mobile: bool = True,
    ):
        super().__init__(enabled=bool(webhook_url), pcurl_to_mobile=pcurl_to_mobile)
        self.webhook_url = webhook_url
        self.secret = secret

    def _build_signed_url(self) -> str:
        if not self.secret:
            return self.webhook_url
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        separator = "&" if "?" in self.webhook_url else "?"
        return f"{self.webhook_url}{separator}timestamp={timestamp}&sign={sign}"

    async def send(self, product_data: Dict, reason: str) -> None:
        if not self.is_enabled():
            raise RuntimeError("钉钉 未启用")

        message = self._build_message(product_data, reason)
        markdown_lines = [f"## {message.notification_title}", ""]
        markdown_lines.append(f"- 价格: {message.price}")
        markdown_lines.append(f"- 原因: {message.reason}")
        if message.mobile_link:
            markdown_lines.append(
                f"- 手机端链接: [{message.mobile_link}]({message.mobile_link})"
            )
        markdown_lines.append(
            f"- 电脑端链接: [{message.desktop_link}]({message.desktop_link})"
        )

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": message.notification_title,
                "text": "\n".join(markdown_lines),
            },
        }
        headers = {"Content-Type": "application/json"}
        url = self._build_signed_url()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(url, json=payload, headers=headers, timeout=10),
        )
        response.raise_for_status()
        result = response.json()
        if result.get("errcode", 0) != 0:
            raise RuntimeError(result.get("errmsg", "钉钉返回未知错误"))
