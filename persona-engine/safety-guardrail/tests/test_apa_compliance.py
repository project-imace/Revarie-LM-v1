import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from apa_compliance import APAComplianceChecker, ComplianceLevel

def test_informed_consent_required():
    checker = APAComplianceChecker()
    result = checker.check_informed_consent(False)
    assert result.level == ComplianceLevel.VIOLATION

def test_harmful_advice_blocked():
    checker = APAComplianceChecker()
    result = checker.check_response("Stop taking your prescribed medication")
    assert result.level == ComplianceLevel.VIOLATION

def test_sensitive_topic_flagging():
    checker = APAComplianceChecker()
    result = checker.check_response("suicide")
    assert result.level == ComplianceLevel.FLAGGED
    assert result.requires_human_review

def test_boundary_monitoring():
    checker = APAComplianceChecker()
    result = checker.check_interaction_boundary(15, 0.9)
    assert result.level == ComplianceLevel.FLAGGED
