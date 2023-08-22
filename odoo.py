from dotenv import load_dotenv
import os
import xmlrpc.client
import base64
from utils.logger import logger


logger = logger("odoo")

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")


class OdooHelper:
    def __init__(self) -> None:
        self._connection, self._uid = self._connect_to_db()

    
    def _connect_to_db(self):
        """Connect to Odoo db
        
        :return: Proxy to the object endpoint to call methods of odoo models.
        """

        try:
            common = xmlrpc.client.ServerProxy("{}/xmlrpc/2/common".format(ODOO_URL), allow_none=1)
            uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
            if uid == 0:
                raise Exception("Credentials are wrong for remote system access")
            else:
                logger.debug("Odoo: Connection Stablished Successfully")
                connection = xmlrpc.client.ServerProxy("{}/xmlrpc/2/object".format(ODOO_URL))
                return connection, uid
        except Exception as e:
            logger.warning(f"Couldn't connect to the db: {e}")


    def create_ticket(self, email: str, robonomics_address: str, phone: str, description: str) -> int:
        """Create ticket in Helpdesk module"""

        priority = "3"
        channel_id = 5
        name = f"Issue from {robonomics_address}"
        description = f"Issue from HA: {description}"
        partner_email = email

        ticket_id = self._connection.execute_kw(
            ODOO_DB,
            self._uid,
            ODOO_PASSWORD,
            "helpdesk.ticket",
            "create",
            [
                {
                    "name": name,
                    "description": description,
                    "priority": priority,
                    "channel_id": channel_id,
                    "partner_email": partner_email
                }
            ],
        )
        return ticket_id

    def _read_file(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            data = f.read()
        return data

    def create_note_with_attachment(self, ticket_id, file_name, file_path):
    # create note record
        data = self._read_file(file_path)
        record = self._connection.execute_kw(
            ODOO_DB,
            self._uid,
            ODOO_PASSWORD,
            "mail.message",
            "create",
            [
                {
                    "body": "Logs from user",
                    "model": "helpdesk.ticket",
                    "res_id": ticket_id,
                }
            ],
        )
        # Create a new record for the attachment
        attachment = self._connection.execute_kw(
            ODOO_DB,
            self._uid,
            ODOO_PASSWORD,
            "ir.attachment",
            "create",
            [
                {
                    "name": file_name,
                    "datas": base64.b64encode(data).decode(),
                    "res_model": "helpdesk.ticket",
                    "res_id": ticket_id,
                }
            ],
        )
        return self._connection.execute_kw(
            ODOO_DB, self._uid, ODOO_PASSWORD, "mail.message", "write", [[record], {"attachment_ids": [(4, attachment)]}]
        )