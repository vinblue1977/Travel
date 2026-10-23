#!/usr/bin/env python3
"""CDK entry point. `cdk synth` also runs cdk-nag's AWS Solutions security checks."""

import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from infra.stack import TravelStack

app = cdk.App()
TravelStack(
    app,
    "Travel",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-2",  # fixed: the CDK CLI defaults to us-east-1 without credentials
    ),
    termination_protection=True,
    description="Personal travel planner: booking emails become trip cards, with push reminders",
)
cdk.Tags.of(app).add("project", "travel-planner")
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()
