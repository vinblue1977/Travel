"""Infrastructure tests: the real app configuration synthesizes, is locked down and passes cdk-nag."""

import aws_cdk as cdk
import pytest
from aws_cdk import aws_s3 as s3
from aws_cdk.assertions import Annotations, Match, Template
from cdk_nag import AwsSolutionsChecks

from infra.app import build_app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> cdk.App:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    return build_app()


@pytest.fixture
def stack(app: cdk.App) -> cdk.Stack:
    child = app.node.find_child("Travel")
    assert isinstance(child, cdk.Stack)
    return child


def test_stack_is_pinned_to_us_east_2(stack: cdk.Stack) -> None:
    assert stack.region == "us-east-2"


def test_stack_has_termination_protection(stack: cdk.Stack) -> None:
    assert stack.termination_protection is True


def test_cdk_nag_is_attached_to_the_app(app: cdk.App) -> None:
    assert any(isinstance(aspect, AwsSolutionsChecks) for aspect in cdk.Aspects.of(app).all)


def test_no_cdk_nag_findings(stack: cdk.Stack) -> None:
    Template.from_stack(stack)  # runs the aspects
    annotations = Annotations.from_stack(stack)
    assert not annotations.find_error("*", Match.string_like_regexp("AwsSolutions-.*"))
    assert not annotations.find_warning("*", Match.string_like_regexp("AwsSolutions-.*"))


def test_cdk_nag_reports_a_noncompliant_resource() -> None:
    """Positive control: a bucket without SSL enforcement must raise a finding, proving the checks really run."""
    app = cdk.App()
    throwaway = cdk.Stack(app, "Throwaway")
    s3.Bucket(throwaway, "Bucket")
    cdk.Aspects.of(app).add(AwsSolutionsChecks())
    Template.from_stack(throwaway)
    assert Annotations.from_stack(throwaway).find_error("*", Match.string_like_regexp("AwsSolutions-.*"))
