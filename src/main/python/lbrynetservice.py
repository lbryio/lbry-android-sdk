import asyncio
import certifi
import os

# Let cacert.pem be found
os.environ["SSL_CERT_FILE"] = certifi.where()

import keyring
import logging
import pathlib
import platform
import sys
import lbry.wallet

from aiohttp.web import GracefulExit

from jnius import autoclass
from keyring.backend import KeyringBackend
from lbry import __version__ as lbrynet_version, build_info
from lbry.conf import Config
from lbry.extras.daemon.components import DHT_COMPONENT, HASH_ANNOUNCER_COMPONENT, PEER_PROTOCOL_SERVER_COMPONENT
from lbry.extras.daemon.daemon import Daemon

import sqlite3
import ssl

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

lbrynet_android_utils = autoclass('io.lbry.lbrysdk.Utils')
service = autoclass('io.lbry.lbrysdk.LbrynetService').serviceInstance
platform.platform = lambda: 'Android %s (API %s)' % (lbrynet_android_utils.getAndroidRelease(), lbrynet_android_utils.getAndroidSdk())
build_info.BUILD = 'dev' if lbrynet_android_utils.isDebug() else 'release'

# Keyring backend
class LbryAndroidKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        self._keystore = lbrynet_android_utils.initKeyStore(service.getApplicationContext())

    def set_password(self, servicename, username, password):
        context = service.getApplicationContext()
        lbrynet_android_utils.setPassword(servicename, username, password, context, self._keystore)

    def get_password(self, servicename, username):
        context = service.getApplicationContext()
        return lbrynet_android_utils.getPassword(servicename, username, context, self._keystore)

    def delete_password(self, servicename, username):
        context = service.getApplicationContext()
        lbrynet_android_utils.deletePassword(servicename, username, context, self._keystore)

def ensure_directory_exists(path: str):
    if not os.path.isdir(path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def configure_logging(conf):
    default_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        conf.log_file_path, maxBytes=2097152, backupCount=5
    )
    file_handler.setFormatter(default_formatter)
    logging.getLogger('lbry').addHandler(file_handler)
    logging.getLogger('torba').addHandler(file_handler)

    handler = logging.StreamHandler()
    handler.setFormatter(default_formatter)

    log.addHandler(handler)
    logging.getLogger('lbry').addHandler(handler)
    logging.getLogger('torba').addHandler(handler)

    logging.getLogger('aioupnp').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.CRITICAL)
    logging.getLogger('lbry').setLevel(logging.DEBUG if lbrynet_android_utils.isDebug() else logging.INFO)
    logging.getLogger('torba').setLevel(logging.INFO)

def start():
    keyring.set_keyring(LbryAndroidKeyring())
    private_storage_dir = lbrynet_android_utils.getAppInternalStorageDir(service.getApplicationContext())
    configured_download_dir = lbrynet_android_utils.getConfiguredDownloadDirectory(service.getApplicationContext())
    components_to_skip = []

    # dht state
    dht_state = 'off'
    try:
        dht_path = f'{private_storage_dir}/dht';
        with open(dht_path, 'r') as file:
            dht_state = file.read()
    except:
        pass


    # share_usage_data state
    sud_state = 'false'
    try:
        sud_path = f'{private_storage_dir}/sud';
        with open(sud_path, 'r') as file:
            sud_state = file.read()
    except Exception:
        pass

    dht_enabled = dht_state == 'on'
    share_usage_data = sud_state == 'true'

    if not dht_enabled:
        components_to_skip = [DHT_COMPONENT, HASH_ANNOUNCER_COMPONENT, PEER_PROTOCOL_SERVER_COMPONENT]

    conf = Config(
        data_dir=f'{private_storage_dir}/lbrynet',
        wallet_dir=f'{private_storage_dir}/lbryum',
        download_dir=configured_download_dir,
        blob_lru_cache_size=32,
        components_to_skip=components_to_skip,
        save_blobs=False,
        save_files=False,
        share_usage_data=share_usage_data,
        use_upnp=False
    )

    for directory in (conf.data_dir, conf.download_dir, conf.wallet_dir):
        ensure_directory_exists(directory)

    configure_logging(conf)
    log.info('Starting lbry sdk {}'.format(lbrynet_version));
    log.info('openssl: {}, sqlite3: {}'.format(ssl.OPENSSL_VERSION, sqlite3.sqlite_version))
    loop = asyncio.get_event_loop()
    loop.set_debug(lbrynet_android_utils.isDebug())

    daemon = Daemon(conf)
    try:
        loop.run_until_complete(daemon.start())
        loop.run_forever()
    except (GracefulExit, asyncio.CancelledError):
        pass
    finally:
        loop.run_until_complete(daemon.stop())
        logging.shutdown()
    if hasattr(loop, 'shutdown_asyncgens'):
        loop.run_until_complete(loop.shutdown_asyncgens())

if __name__ == '__main__':
    start()
