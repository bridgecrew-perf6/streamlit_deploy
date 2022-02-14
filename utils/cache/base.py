import abc
import math
import os
import pickle
import threading
import time
from typing import Optional, Any, cast

from cachetools import TTLCache
from streamlit import util
from streamlit.caching.cache_errors import CacheKeyNotFoundError, CacheError
from streamlit.file_util import (
    streamlit_read,
    streamlit_write,
)
from streamlit.logger import get_logger

_LOGGER = get_logger(__name__)

_TTL_CACHE_TIMER = time.monotonic


class MemoCache:
    """Manages cached values for a single st.memorized function."""

    cache_name: str = "_default"

    def __init__(
            self,
            persist: Optional[str] = "disk",
            ttl: float = math.inf,
            max_entries: float = math.inf,
    ):
        self.persist = persist
        self._mem_cache = TTLCache(maxsize=max_entries, ttl=ttl, timer=_TTL_CACHE_TIMER)
        self._mem_cache_lock = threading.Lock()

    @property
    def max_entries(self) -> float:
        return cast(float, self._mem_cache.maxsize)

    @property
    def ttl(self) -> float:
        return cast(float, self._mem_cache.ttl)

    @abc.abstractmethod
    def query(self, key):
        pass

    def read_value(self, key: str) -> Any:
        """Read a value from the cache. Raise `CacheKeyNotFoundError` if the
        value doesn't exist, and `CacheError` if the value exists but can't
        be unpickled.
        """
        key = f"{self.cache_name}:{key}"
        try:
            pickled_value = self._read_from_mem_cache(key)

        except CacheKeyNotFoundError as e:
            if self.persist == "disk":
                try:
                    pickled_value = self._read_from_disk_cache(key)
                    self._write_to_mem_cache(key, pickled_value)
                except CacheKeyNotFoundError:
                    value = self.query(key)
                    pickled_value = self._write_value(key, value)
            else:
                raise e

        try:
            return pickle.loads(pickled_value)
        except pickle.UnpicklingError as exc:
            raise CacheError(f"Failed to unpickle {key}") from exc

    def _write_value(self, key: str, value: Any):
        """Write a value to the cache. It must be pickleable."""
        try:
            pickled_value = pickle.dumps(value)
        except pickle.PicklingError as exc:
            raise CacheError(f"Failed to pickle {key}") from exc

        self._write_to_mem_cache(key, pickled_value)
        if self.persist == "disk":
            self._write_to_disk_cache(key, pickled_value)
        return pickled_value

    def clear(self) -> None:
        with self._mem_cache_lock:
            # We keep a lock for the entirety of the clear operation to avoid
            # disk cache race conditions.
            for key in self._mem_cache.keys():
                self._remove_from_disk_cache(key)

            self._mem_cache.clear()

    def _read_from_mem_cache(self, key: str) -> bytes:
        with self._mem_cache_lock:
            if key in self._mem_cache:
                entry = bytes(self._mem_cache[key])
                _LOGGER.debug("Memory cache HIT: %s", key)
                return entry

            else:
                _LOGGER.debug("Memory cache MISS: %s", key)
                raise CacheKeyNotFoundError("Key not found in mem cache")

    def _read_from_disk_cache(self, key: str) -> bytes:
        path = self._get_file_path(key)
        try:
            with streamlit_read(path, binary=True) as input_file:
                value = input_file.read()
                _LOGGER.debug("Disk cache HIT: %s", key)
                return bytes(value)
        except FileNotFoundError:
            raise CacheKeyNotFoundError("Key not found in disk cache")
        except BaseException as e:
            _LOGGER.error(e)
            raise CacheError("Unable to read from cache") from e

    def _write_to_mem_cache(self, key: str, pickled_value: bytes) -> None:
        with self._mem_cache_lock:
            self._mem_cache[key] = pickled_value

    def _write_to_disk_cache(self, key: str, pickled_value: bytes) -> None:
        path = self._get_file_path(key)
        try:
            with streamlit_write(path, binary=True) as output:
                output.write(pickled_value)
        except util.Error as e:
            _LOGGER.debug(e)
            # Clean up file so we don't leave zero byte files.
            try:
                os.remove(path)
            except (FileNotFoundError, IOError, OSError):
                pass
            raise CacheError("Unable to write to cache") from e

    def _remove_from_disk_cache(self, key: str) -> None:
        """Delete a cache file from disk. If the file does not exist on disk,
        return silently. If another exception occurs, log it. Does not throw.
        """
        path = self._get_file_path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except BaseException as e:
            _LOGGER.exception("Unable to remove a file from the disk cache", e)

    @staticmethod
    def _get_file_path(value_key: str) -> str:
        """Return the path of the disk cache file for the given value."""
        _dir, file_name = value_key.split(":", 1)
        cache_dir = os.path.join(os.environ.get("CACHE_PATH", "./cache"), _dir)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # absolute path to the file in the cache directory for the given key value pair (dir:file_name)
        return os.path.abspath(os.path.join(cache_dir, f"{file_name}.memo"))
