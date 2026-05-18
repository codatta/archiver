"""Branded email HTML renderer — Humanbased Developer Portal."""

LOGO_HEADER_URL = "https://raw.githubusercontent.com/codatta/brand-kit/main/logo/png/symbol_black.png"
LOGO_FOOTER_URL = "https://raw.githubusercontent.com/codatta/brand-kit/main/logo/png/symbol_black.png"

BRAND_NAME = "Humanbased"
BRAND_COLOR = "#1B1034"
FROM_ADDRESS = "Codatta <noreply@humanbased.ai>"


def render_email(
    *,
    heading: str,
    body_html: str,
    cta_label: str | None = None,
    cta_url: str | None = None,
    recipient_name: str | None = None,
) -> str:
    """Render a complete branded email HTML document."""
    header = _render_header()
    greeting = _render_greeting(recipient_name)
    cta = _render_cta(cta_label, cta_url)
    footer = _render_footer()

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head>',
        '<meta charset="UTF-8" />',
        '<meta name="viewport" content="width=device-width,initial-scale=1.0" />',
        f"<title>{heading}</title>",
        "<style>",
        "@media (prefers-color-scheme: dark) { .email-outer { background-color: #000000 !important; } }",
        "@media (prefers-color-scheme: light) { .email-outer { background-color: #ffffff !important; } }",
        "</style>",
        "</head>",
        '<body style="margin:0;padding:0;'
        "font-family:'DM Sans',-apple-system,BlinkMacSystemFont,"
        "'Segoe UI','Roboto','Helvetica Neue',Arial,sans-serif;"
        '-webkit-font-smoothing:antialiased;">',
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" '
        'width="100%" class="email-outer" style="background-color:#ffffff;">',
        "<tr>",
        '<td align="center" style="padding:40px 16px;">',
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" '
        f'width="100%" style="max-width:520px;background:#ffffff;border-radius:0;'
        f'overflow:hidden;border:1.5px solid {BRAND_COLOR};">',
        f'<tr><td style="padding:32px 32px 0 32px;">{header}</td></tr>',
        f'<tr><td style="padding:0 32px 24px 32px;">'
        f"{greeting}"
        f'<h1 style="font-size:22px;font-weight:700;color:{BRAND_COLOR};'
        f'margin:0 0 16px 0;line-height:1.3;">{heading}</h1>'
        f"{body_html}{cta}</td></tr>",
        f'<tr><td style="padding:24px 32px 32px 32px;'
        f'border-top:1.5px solid {BRAND_COLOR};">{footer}</td></tr>',
        "</table>",
        "</td></tr></table>",
        "</body></html>",
    ]
    return "".join(parts)


def _render_header() -> str:
    return (
        '<div style="margin-bottom:24px;">'
        f'<img src="{LOGO_HEADER_URL}" alt="{BRAND_NAME}" '
        'style="height:32px;width:auto;" />'
        "</div>"
    )


def _render_greeting(name: str | None) -> str:
    display = name.strip() if name and name.strip() else "there"
    return (
        '<p style="font-size:15px;color:#37352F;'
        f'line-height:1.6;margin:0 0 8px 0;">Hi {display},</p>'
    )


def _render_cta(label: str | None, url: str | None) -> str:
    if not label or not url:
        return ""
    return (
        '<div style="text-align:center;margin:28px 0;">'
        f'<a href="{url}" style="display:inline-block;'
        f"background:{BRAND_COLOR};color:#ffffff;"
        "font-size:14px;font-weight:500;"
        "padding:12px 28px;border-radius:0;"
        'text-decoration:none;">'
        f"{label}</a></div>"
    )


def _render_footer() -> str:
    return (
        '<div style="text-align:center;padding-top:16px;">'
        f'<img src="{LOGO_FOOTER_URL}" alt="{BRAND_NAME}" '
        'style="height:20px;margin-bottom:12px;" />'
        "<br />"
        '<a href="https://humanbased.ai" style="color:#37352F;'
        'font-size:12px;text-decoration:none;">humanbased.ai</a>'
        "<br />"
        '<span style="color:#9B9A97;font-size:11px;'
        'margin-top:8px;display:inline-block;">Codatta PTE LTD</span>'
        "</div>"
    )


def body_text(text: str, sub: str = "") -> str:
    """Build styled body HTML with primary text and subtext."""
    h = (
        "<p style='font-size:15px;color:#37352F;"
        f"line-height:1.6;margin:0 0 12px 0;'>{text}</p>"
    )
    if sub:
        h += (
            "<p style='font-size:14px;color:#9B9A97;"
            f"line-height:1.6;margin:0;'>{sub}</p>"
        )
    return h
