#!/usr/bin/env python3
"""
Конвертер полных V2Ray/Xray конфигов в subscription-ссылки.

Использование:
    python scripts/convert_configs.py

Скрипт прочитает все .json файлы из configs/ и создаст servers.json
с VLESS-ссылками в формате, который понимает backend.
"""
import json
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode


def parse_vless_outbound(outbound: Dict[str, Any], remark: str = "") -> Optional[str]:
    """
    Конвертирует VLESS outbound в subscription-ссылку.

    Args:
        outbound: Outbound секция из V2Ray конфига
        remark: Название сервера (для отображения)

    Returns:
        VLESS-ссылка или None
    """
    try:
        if outbound.get("protocol") != "vless":
            return None

        settings = outbound.get("settings", {})
        vnext = settings.get("vnext", [])
        if not vnext:
            return None

        server = vnext[0]
        address = server.get("address")
        port = server.get("port")

        users = server.get("users", [])
        if not users:
            return None

        user = users[0]
        # Заменяем фиксированный UUID на плейсхолдер
        uuid = "{{UUID}}"  # Используем плейсхолдер для уникальных UUID
        encryption = user.get("encryption", "none")
        flow = user.get("flow", "")

        stream_settings = outbound.get("streamSettings", {})
        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "none")

        # Параметры запроса
        params = {
            "encryption": encryption,
            "type": network,
            "security": security,
        }

        if flow:
            params["flow"] = flow

        # Reality настройки
        if security == "reality":
            reality = stream_settings.get("realitySettings", {})
            if reality:
                params["sni"] = reality.get("serverName", "")
                params["fp"] = reality.get("fingerprint", "")
                params["pbk"] = reality.get("publicKey", "")
                params["sid"] = reality.get("shortId", "")
                params["spx"] = reality.get("spiderX", "/")

        # TLS настройки
        elif security == "tls":
            tls = stream_settings.get("tlsSettings", {})
            if tls:
                params["sni"] = tls.get("serverName", "")
                params["fp"] = tls.get("fingerprint", "chrome")
                if tls.get("alpn"):
                    params["alpn"] = ",".join(tls["alpn"])

        # WebSocket настройки
        if network == "ws":
            ws = stream_settings.get("wsSettings", {})
            if ws:
                params["path"] = ws.get("path", "/")
                headers = ws.get("headers", {})
                if headers.get("Host"):
                    params["host"] = headers["Host"]

        # gRPC настройки
        elif network == "grpc":
            grpc = stream_settings.get("grpcSettings", {})
            if grpc:
                params["serviceName"] = grpc.get("serviceName", "")

        # HTTP/2 настройки
        elif network == "h2" or network == "http":
            h2 = stream_settings.get("httpSettings", {})
            if h2:
                params["path"] = h2.get("path", "/")
                if h2.get("host"):
                    params["host"] = ",".join(h2["host"])

        # Удаляем пустые параметры
        params = {k: v for k, v in params.items() if v}

        # Формируем название с SHORT_ID для разнообразия
        if not remark:
            remark = f"Server-{address}"
        remark = f"{remark}-{{{{SHORT_ID}}}}"

        # Собираем ссылку
        query_string = urlencode(params)
        vless_url = f"vless://{uuid}@{address}:{port}?{query_string}#{remark}"

        return vless_url

    except Exception as e:
        print(f"❌ Ошибка при парсинге VLESS outbound: {e}")
        return None


def parse_vmess_outbound(outbound: Dict[str, Any], remark: str = "") -> Optional[str]:
    """
    Конвертирует VMess outbound в subscription-ссылку.

    Args:
        outbound: Outbound секция из V2Ray конфига
        remark: Название сервера

    Returns:
        VMess-ссылка или None
    """
    try:
        if outbound.get("protocol") != "vmess":
            return None

        settings = outbound.get("settings", {})
        vnext = settings.get("vnext", [])
        if not vnext:
            return None

        server = vnext[0]
        address = server.get("address")
        port = server.get("port")

        users = server.get("users", [])
        if not users:
            return None

        user = users[0]
        uuid = "{{UUID}}"  # Плейсхолдер
        alter_id = user.get("alterId", 0)

        stream_settings = outbound.get("streamSettings", {})
        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "none")

        # Формируем VMess JSON
        vmess_config = {
            "v": "2",
            "ps": remark or f"Server-{address}-{{{{SHORT_ID}}}}",
            "add": address,
            "port": str(port),
            "id": uuid,
            "aid": str(alter_id),
            "net": network,
            "type": "none",
            "host": "",
            "path": "",
            "tls": security if security == "tls" else "",
        }

        # WebSocket
        if network == "ws":
            ws = stream_settings.get("wsSettings", {})
            vmess_config["path"] = ws.get("path", "/")
            headers = ws.get("headers", {})
            vmess_config["host"] = headers.get("Host", "")

        # Кодируем в base64
        json_str = json.dumps(vmess_config, ensure_ascii=False)
        encoded = base64.b64encode(json_str.encode()).decode()

        return f"vmess://{encoded}"

    except Exception as e:
        print(f"❌ Ошибка при парсинге VMess outbound: {e}")
        return None


def convert_v2ray_config(config_path: Path) -> List[str]:
    """
    Конвертирует полный V2Ray конфиг в список subscription-ссылок.

    Args:
        config_path: Путь к .json файлу с V2Ray конфигом

    Returns:
        Список VLESS/VMess ссылок
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        remark = config.get("remarks", config_path.stem)
        outbounds = config.get("outbounds", [])

        urls = []
        for outbound in outbounds:
            protocol = outbound.get("protocol")

            if protocol == "vless":
                url = parse_vless_outbound(outbound, remark)
                if url:
                    urls.append(url)

            elif protocol == "vmess":
                url = parse_vmess_outbound(outbound, remark)
                if url:
                    urls.append(url)

        return urls

    except Exception as e:
        print(f"❌ Ошибка при чтении {config_path.name}: {e}")
        return []


def main():
    """Основная функция конвертации."""
    print("🔄 Конвертер V2Ray/Xray конфигов\n")

    # Директория с конфигами
    configs_dir = Path("configs")
    if not configs_dir.exists():
        print(f"❌ Директория {configs_dir} не найдена!")
        return

    # Находим все .json файлы (кроме servers.json)
    config_files = [
        f for f in configs_dir.glob("*.json")
        if f.name != "servers.json"
    ]

    if not config_files:
        print(f"❌ Не найдено .json файлов в {configs_dir}")
        return

    print(f"📁 Найдено файлов: {len(config_files)}\n")

    # Конвертируем все конфиги
    all_urls = []
    for config_file in config_files:
        print(f"⚙️  Обрабатываю: {config_file.name}...")
        urls = convert_v2ray_config(config_file)

        if urls:
            print(f"   ✅ Извлечено {len(urls)} ссылок")
            all_urls.extend(urls)
        else:
            print(f"   ⚠️  Не удалось извлечь ссылки")

    if not all_urls:
        print("\n❌ Не удалось извлечь ни одной ссылки!")
        return

    # Создаем servers.json
    servers_config = {
        "configs": all_urls
    }

    output_path = configs_dir / "servers.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(servers_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Успешно создан {output_path}")
    print(f"📊 Всего ссылок: {len(all_urls)}")
    print("\n📋 Первые 3 ссылки:")
    for i, url in enumerate(all_urls[:3], 1):
        # Показываем только начало (без параметров)
        display_url = url.split('?')[0][:80] + "..."
        print(f"   {i}. {display_url}")

    print(f"\n🎉 Готово! Теперь можете запустить backend.")


if __name__ == "__main__":
    main()
