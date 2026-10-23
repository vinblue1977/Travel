"""Infrastructure tests: the real app configuration synthesizes, is locked down and passes cdk-nag."""

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Annotations, Match, Template

from infra.app import build_app


@pytest.fixture
def stack(monkeypatch: pytest.MonkeyPatch) -> cdk.Stack:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    return build_app().node.find_child("Travel")  # type: ignore[return-value]


def test_stack_is_pinned_to_us_east_2(stack: cdk.Stack) -> None:
    assert stack.region == "us-east-2"


def test_stack_has_termination_protection(stack: cdk.Stack) -> None:
    assert stack.termination_protection is True


def test_no_cdk_nag_findings(stack: cdk.Stack) -> None:
    Template.from_stack(stack)  # runs the aspects
    annotations = Annotations.from_stack(stack)
    assert not annotations.find_error("*", Match.string_like_regexp("AwsSolutions-.*"))
    assert not annotations.find_warning("*", Match.string_like_regexp("AwsSolutions-.*"))
