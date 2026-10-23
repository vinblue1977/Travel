"""The Travel stack. Empty for now: the table, API and deploy role arrive in later PRs."""

import aws_cdk as cdk
from constructs import Construct


class TravelStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env: cdk.Environment,
        termination_protection: bool = False,
        description: str | None = None,
    ) -> None:
        super().__init__(scope, construct_id, env=env, termination_protection=termination_protection, description=description)
