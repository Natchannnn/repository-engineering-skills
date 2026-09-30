from pathlib import Path


class TransientError(Exception):
    pass


def publish_with_retry(event, publish):
    for attempt in range(3):
        try:
            return publish(event, idempotency_key=event["id"])
        except TransientError:
            if attempt == 2:
                raise


def receipt_path(root):
    return str(Path(root) / "receipt.json")


def receipt_label(root):
    return Path(receipt_path(root)).name


def retail_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid retail name")
    return value.strip()


def archive_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid archive name")
    return value.strip()
