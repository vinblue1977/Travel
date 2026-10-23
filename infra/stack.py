"""The Travel stack. Empty for now: the table, API and deploy role arrive in later PRs."""

from aws_cdk import Stack
from constructs import Construct


class TravelStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
