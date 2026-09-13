from mythic_container.C2ProfileBase import *
from pathlib import Path


class MSTeams(C2Profile):
    name = "msteams"
    description = "Uses the Microsoft Graph API to communicate through a Microsoft Teams channel"
    author = ""
    is_p2p = False
    is_server_routed = False
    server_folder_path = Path(".") / "msteams" / "c2_code"
    server_binary_path = server_folder_path / "server.py"
    parameters = [
        C2ProfileParameter(
            name="tenant_id",
            description="Azure AD Tenant ID (Directory ID) for the app registration",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="client_id",
            description="Application (client) ID from the Azure AD app registration",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="client_secret",
            description="Client secret value from the Azure AD app registration",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="team_id",
            description="The ID of the Teams team. Find it via Graph Explorer or Teams admin center",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="channel_id",
            description="The ID of the Teams channel to use for C2 messages. Use a dedicated private channel",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="webhook_url",
            description="Optional: Incoming Webhook or Workflow URL for sending messages. If empty, Graph API is used for sending",
            default_value="",
            required=False,
        ),
        C2ProfileParameter(
            name="callback_interval",
            description="Callback interval in seconds",
            default_value="60",
            verifier_regex="^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="callback_jitter",
            description="Callback jitter in percent",
            default_value="10",
            verifier_regex="^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="encrypted_exchange_check",
            description="Perform Key Exchange",
            choices=["T", "F"],
            parameter_type=ParameterType.ChooseOne,
            required=False,
        ),
        C2ProfileParameter(
            name="AESPSK",
            description="Crypto type",
            default_value="aes256_hmac",
            parameter_type=ParameterType.ChooseOne,
            choices=["aes256_hmac", "none"],
            required=False,
            crypto_type=True,
        ),
        C2ProfileParameter(
            name="killdate",
            description="Kill Date",
            parameter_type=ParameterType.Date,
            default_value=365,
            required=False,
        ),
        C2ProfileParameter(
            name="user_agent",
            description="User Agent",
            default_value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_host",
            description="Proxy Host",
            default_value="",
            required=False,
            verifier_regex="^$|^(http|https):\/\/[a-zA-Z0-9]+",
        ),
        C2ProfileParameter(
            name="proxy_port",
            description="Proxy Port",
            default_value="",
            verifier_regex="^$|^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_user",
            description="Proxy Username",
            default_value="",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_pass",
            description="Proxy Password",
            default_value="",
            required=False,
        ),
    ]
