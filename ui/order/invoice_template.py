import os
import json
from jinja2 import Environment, FileSystemLoader
from PySide6.QtGui import QImage
from utils.utils import to_float, resource_path

TEMPLATE_DIR = resource_path("ui/order")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def get_image_html(path, target_width=60):
    if not path or not os.path.exists(path):
        return ""
    img = QImage(path)
    if img.isNull():
        return ""
    aspect = img.height() / img.width()
    target_height = int(target_width * aspect)
    return f'<img src="{path}" width="{target_width}" height="{target_height}">'


def divider_html():
    return '''
    <table width="100%" cellspacing="0" cellpadding="0" style="margin:4px 0;">
        <tr><td style="border-top:1px dashed black; font-size:1px; line-height:1px;">&nbsp;</td></tr>
    </table>
    '''


def build_receipt_html(app, order, items):
    biz = app.settings.get_all()
    logo_img = get_image_html(biz.get("business_logo", ""), target_width=60)
    khqr_img = get_image_html(biz.get("khqr_image", ""), target_width=120)
    exchange_rate = to_float(biz.get("exchange_rate"))
    items_list = [dict(row) for row in items]
    items_total = sum(it["subtotal"] for it in items_list)
    order_dict = dict(order)
    order_dict.setdefault('paid_amount', 0)
    order_dict.setdefault('discount', 0)
    order_dict.setdefault('delivery_fee', 0)
    order_dict.setdefault('payment_method', 'Cash')
    order_dict.setdefault('payment_status', 'unpaid')
    order_dict.setdefault('pickup_time', '')
    order_dict.setdefault('phone', '')
    order_dict.setdefault('telegram', '')
    order_dict.setdefault('facebook', '')
    order_dict.setdefault('address', '')

    try:
        brands = json.loads(biz.get("business_brands", "[]") or "[]")
    except Exception:
        brands = []

    template = env.get_template("receipt.html")
    try:
        rendered = template.render(
            biz_name=biz.get("business_name", "My Shop"),
            biz_phone=biz.get("business_phone", ""),
            biz_mobile=biz.get("business_mobile", ""),
            biz_email=biz.get("business_email", ""),
            biz_address=biz.get("business_address", ""),
            biz_telegram=biz.get("business_telegram", ""),
            biz_facebook=biz.get("business_facebook", ""),
            receipt_header=biz.get("receipt_header", ""),
            receipt_footer=biz.get("receipt_footer", "Thank you for your purchase!"),
            invoice_prefix=biz.get("invoice_prefix", "INV"),
            biz_exchange_rate=exchange_rate,
            logo_img=logo_img,
            khqr_img=khqr_img,
            divider=divider_html(),
            order=order_dict,
            items=items_list,
            items_total=items_total,
            brands=brands,
        )
    except Exception as e:
        print(f"JINJA2 RENDER ERROR: {e}")
        raise

    return rendered