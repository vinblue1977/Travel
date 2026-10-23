"""Infrastructure tests: the real app configuration synthesizes, is locked down and passes cdk-nag."""

import json
from pathlib import Path
from typing import cast

import aws_cdk as cdk
import jsii
import pytest
from aws_cdk import aws_s3 as s3
from aws_cdk.assertions import Annotations, Match, Template
from cdk_nag import AwsSolutionsChecks, INagLogger, NagLoggerNonComplianceData

from infra.app import build_app

# What `cdk synth` injects from cdk.json: the same feature flags and repo as a real deploy.
CDK_CONTEXT: dict[str, object] = json.loads((Path(__file__).parent.parent / "cdk.json").read_text())["context"]
REPO = "test-owner@1/test-repo@2"


@pytest.fixture(autouse=True)
def account(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")


def _stack(context: dict[str, object] | None = None) -> cdk.Stack:
    child = build_app(CDK_CONTEXT | (context or {})).node.find_child("Travel")
    assert isinstance(child, cdk.Stack)
    return child


def _template(context: dict[str, object] | None = None) -> Template:
    return Template.from_stack(_stack(context))


def test_stack_is_pinned_to_us_east_2() -> None:
    assert _stack().region == "us-east-2"


def test_stack_has_termination_protection() -> None:
    assert _stack().termination_protection is True


def test_cdk_nag_is_attached_to_the_app() -> None:
    app = build_app(CDK_CONTEXT)
    assert any(isinstance(aspect, AwsSolutionsChecks) for aspect in cdk.Aspects.of(app).all)


def test_no_cdk_nag_findings() -> None:
    stack = _stack()
    Template.from_stack(stack)  # runs the aspects
    annotations = Annotations.from_stack(stack)
    assert not annotations.find_error("*", Match.string_like_regexp("AwsSolutions-.*"))
    assert not annotations.find_warning("*", Match.string_like_regexp("AwsSolutions-.*"))


@jsii.implements(INagLogger)
class _FindingCollector:
    """Records cdk-nag findings through its logger hook (Annotations.find_error can fail to deserialize entries in jsii)."""

    def __init__(self) -> None:
        self.findings: list[str] = []

    def on_non_compliance(self, data: NagLoggerNonComplianceData) -> None:
        self.findings.append(data.rule_id)

    def on_compliance(self, data: object) -> None: ...

    def on_error(self, data: object) -> None: ...

    def on_not_applicable(self, data: object) -> None: ...

    def on_suppressed(self, data: object) -> None: ...

    def on_suppressed_error(self, data: object) -> None: ...


def test_cdk_nag_reports_a_noncompliant_resource() -> None:
    """Positive control: a bucket without SSL enforcement must raise a finding, proving the checks really run."""
    app = cdk.App()
    throwaway = cdk.Stack(app, "Throwaway")
    s3.Bucket(throwaway, "Bucket")
    collector = _FindingCollector()
    # jsii passes the loggers one data object, while the stubs declare keyword arguments; hence the cast.
    cdk.Aspects.of(app).add(AwsSolutionsChecks(additional_loggers=[cast(INagLogger, collector)]))
    Template.from_stack(throwaway)
    assert "AwsSolutions-S10" in collector.findings  # require SSL requests


def test_table_is_protected_and_on_demand() -> None:
    _template().has_resource(
        "AWS::DynamoDB::GlobalTable",
        {
            "DeletionPolicy": "Retain",
            "Properties": Match.object_like(
                {
                    "BillingMode": "PAY_PER_REQUEST",
                    "KeySchema": [{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
                    "Replicas": [
                        Match.object_like(
                            {
                                "DeletionProtectionEnabled": True,
                                "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
                            }
                        )
                    ],
                }
            ),
        },
    )


def test_deploy_role_trusts_only_this_repo_production_environment() -> None:
    template = _template({"githubRepo": REPO})
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": Match.object_like(
                {
                    "Statement": [
                        Match.object_like(
                            {
                                "Action": "sts:AssumeRoleWithWebIdentity",
                                "Condition": {
                                    "StringEquals": {
                                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                        "token.actions.githubusercontent.com:sub": f"repo:{REPO}:environment:production",
                                    }
                                },
                            }
                        )
                    ]
                }
            )
        },
    )
    # The provider is shared with other stacks in the account, so this stack must not create one.
    template.resource_count_is("Custom::AWSCDKOpenIdConnectProvider", 0)
    template.resource_count_is("AWS::IAM::OIDCProvider", 0)


def test_deploy_role_can_only_assume_three_cdk_roles_and_describe_the_table() -> None:
    statements = [
        statement
        for policy in _template({"githubRepo": REPO}).find_resources("AWS::IAM::Policy").values()
        for statement in policy["Properties"]["PolicyDocument"]["Statement"]
    ]
    assert sorted(s["Action"] if isinstance(s["Action"], str) else tuple(s["Action"]) for s in statements) == [
        "dynamodb:DescribeTable",
        "sts:AssumeRole",
    ]
    (assume,) = (s for s in statements if s["Action"] == "sts:AssumeRole")
    arns = [json.dumps(resource) for resource in assume["Resource"]]
    assert len(arns) == 3
    assert all("*" not in arn for arn in arns)  # no wildcard: only the deploy, file-publishing and lookup roles
    for kind in ("deploy", "file-publishing", "lookup"):
        assert any(f"-{kind}-role-" in arn for arn in arns)


def test_real_repo_setting_is_valid() -> None:
    assert CDK_CONTEXT["githubRepo"]
    _template()  # synthesizes with the real setting


def test_no_deploy_role_without_repo() -> None:
    web_identity = {
        "AssumeRolePolicyDocument": Match.object_like(
            {"Statement": [Match.object_like({"Action": "sts:AssumeRoleWithWebIdentity"})]}
        )
    }
    _template({"githubRepo": ""}).resource_properties_count_is("AWS::IAM::Role", web_identity, 0)


def test_malformed_repo_is_rejected() -> None:
    with pytest.raises(ValueError, match="githubRepo"):
        _stack({"githubRepo": "not a repo"})
