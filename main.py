import robonomicsinterface as ri
from dotenv import load_dotenv
import os
import typing as tp
from robonomicsinterface.utils import ipfs_32_bytes_to_qm_hash
import threading
import logging

from ipfs import IPFSHelpder
from odoo import OdooHelper

load_dotenv()

ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS")
WSS_ENDPOINT = os.getenv("WSS_ENDPOINT")

odoo = OdooHelper()
ipfs = IPFSHelpder()

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def _is_subscription_alive(subscriber) -> None:
    if subscriber._subscription.is_alive():
        return
    _resubscribe(subscriber)
    threading.Timer(15, _is_subscription_alive)


def _resubscribe(subscriber) -> None:
    """Close the subscription and create a new" one"""

    subscriber.cancel()
    subscribe()


def _on_new_launch(data: tp.Tuple[tp.Union[str, tp.List[str]]]):
    """NewLaunch callback

    :param data: Data from the launch
    """
    try:
        print(data)
        if data[1] == ADMIN_ADDRESS:
            hash = ipfs_32_bytes_to_qm_hash(data[2])
            logger.info(f"Ipfs hash: {hash}")
            robonomics_address_from = data[0]
            email, phone, description = ipfs.parse_logs(hash)
            logger.info(f"Data from ipfs: {email}, {phone}, {description}")
            ticket_id = odoo.create_ticket(email, robonomics_address_from, phone, description)
            logger.info(f"Ticket id: {ticket_id}")

    except:
        pass


def subscribe() -> ri.Subscriber:
    account = ri.Account(remote_ws=WSS_ENDPOINT)
    subscriber = ri.Subscriber(
        account,
        ri.SubEvent.NewLaunch,
        subscription_handler=_on_new_launch,
    )


def main() -> None:
    subscribe()


if __name__ == "__main__":
    main()
