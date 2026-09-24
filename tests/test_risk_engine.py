from risk_engine import analyse


def test_high_risk_scam_message():
    msg = "Dear candidate, no interview required. Contact us on WhatsApp and deposit $150 in USDT."
    result = analyse(msg)
    assert result["level"] == "High"
    assert result["score"] >= 70


def test_low_risk_formal_message():
    msg = "Please apply through our careers page. Shortlisted candidates will be invited to an interview."
    result = analyse(msg)
    assert result["level"] == "Low"


def test_domain_mismatch():
    msg = "Apply at https://fake-example.net/jobs or contact jobs@fake-example.net"
    result = analyse(msg, "realcompany.com")
    assert any("Domain mismatch" in label for _, label in result["signals"])
