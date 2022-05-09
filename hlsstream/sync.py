from multiprocessing.managers import SyncManager
from typing import Any

SYNC_ADDR = "127.0.0.1"
SYNC_PORT = 5001
SYNC_PWD = b"password"


class CacheSyncManager(SyncManager):
    ...


_syncdict = {}


def _get_dict():
    return _syncdict


class Cache:
    def __init__(self) -> None:
        self.manager = CacheSyncManager((SYNC_ADDR, SYNC_PORT), authkey=SYNC_PWD)
        self.manager.connect()
        CacheSyncManager.register("syncdict")
        self.syndict = self.manager.syncdict()

    def set(self, key: str, value: Any):
        self.syndict.update([(key, value)])

    def get(self, key: str, default: Any = None) -> Any:
        return self.syndict.get(key, default)


if __name__ == "__main__":

    CacheSyncManager.register("syncdict", _get_dict)
    manager = CacheSyncManager((SYNC_ADDR, SYNC_PORT), authkey=SYNC_PWD)
    manager.get_server().serve_forever()
