"""Infrastructure tests: the stack synthesizes and passes cdk-nag."""

import aws_cdk as cdk
from aws_cdk.assertions import Annotations, Match
from cdk_nag import AwsSolutionsChecks

from infra.stack import TravelStack


def _stack() -> TravelStack:
    app = cdk.App()
    stack = TravelStack(app, "Travel", env=cdk.Environment(account="123456789012", region="us-east-2"))
    cdk.Aspects.of(app).add(AwsSolutionsChecks())
    return stack


def test_stack_is_in_the_expected_region() -> None:
    assert _stack().region == "us-east-2"


def test_no_cdk_nag_findings() -> None:
    stack = _stack()
    cdk.assertions.Template.from_stack(stack)  # runs the aspects
    assert not Annotations.from_stack(stack).find_error("*", Match.string_like_regexp("AwsSolutions-.*"))
    assert not Annotations.from_stack(stack).find_warning("*", Match.string_like_regexp("AwsSolutions-.*"))
