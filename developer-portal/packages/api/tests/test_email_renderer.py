"""Tests for branded email renderer (IN-46)."""
from app.services.email_renderer import body_text, render_email


def test_greeting_with_name():
    html = render_email(heading="T", body_html="<p>B</p>", recipient_name="Yi")
    assert "Hi Yi," in html

def test_greeting_fallback():
    assert "Hi there," in render_email(heading="T", body_html="<p>B</p>")

def test_greeting_none():
    assert "Hi there," in render_email(heading="T", body_html="<p>B</p>", recipient_name=None)

def test_brand_humanbased():
    assert 'alt="Humanbased"' in render_email(heading="T", body_html="<p>B</p>")

def test_logo_cdn():
    assert "raw.githubusercontent.com/codatta/brand-kit" in render_email(heading="T", body_html="<p>B</p>")

def test_logo_no_typemark():
    html = render_email(heading="T", body_html="<p>B</p>")
    assert "symbol_wordmark" not in html
    assert "symbol_black" in html

def test_dark_mode():
    assert "prefers-color-scheme: dark" in render_email(heading="T", body_html="<p>B</p>")

def test_light_mode():
    assert "prefers-color-scheme: light" in render_email(heading="T", body_html="<p>B</p>")

def test_sharp_corners():
    html = render_email(heading="T", body_html="<p>B</p>")
    assert "border-radius:0" in html
    assert "border-radius:12px" not in html

def test_cta_sharp():
    html = render_email(heading="T", body_html="<p>B</p>", cta_label="Go", cta_url="https://x.com")
    assert "999px" not in html

def test_footer_codatta_pte_ltd():
    assert "Codatta PTE LTD" in render_email(heading="T", body_html="<p>B</p>")

def test_footer_url_humanbased():
    html = render_email(heading="T", body_html="<p>B</p>")
    assert 'href="https://humanbased.ai"' in html

def test_no_purple_link():
    assert "#834DFB" not in render_email(heading="T", body_html="<p>B</p>")

def test_no_colored_bg():
    html = render_email(heading="T", body_html="<p>B</p>")
    assert "#E8E0F0" not in html
    assert "#F7F6F3" not in html

def test_heading():
    assert "Welcome" in render_email(heading="Welcome", body_html="<p>B</p>")

def test_cta_rendered():
    html = render_email(heading="T", body_html="<p>B</p>", cta_label="Go", cta_url="https://x.com")
    assert "Go" in html and "https://x.com" in html

def test_cta_omitted():
    assert "text-align:center;margin:28px" not in render_email(heading="T", body_html="<p>B</p>")

def test_body_text():
    h = body_text("A", "B")
    assert "A" in h and "B" in h
