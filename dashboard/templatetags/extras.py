# dashboard/templatetags/extras.py
from django import template

register = template.Library()

@register.filter
def total_sale_price(sale):
    return sum(item.quantity * item.price for item in sale.items.all()
)
