from django import template
from django.template.defaultfilters import stringfilter

register= template.Library()

@register.filter(name='change_price')
@stringfilter
def change_price(value, arg):
    """Alters the price to Nx larger and rounded to 2 sigfig"""
    value = round(float(value)*float(arg), 4)
    return "{:.2f}".format(value)



@register.filter
def multiply(value, arg):
    return float(value) * float(arg)



@register.filter
def addition(value, arg):
    return float(value) + float(arg)

#register_templates.filter('change_price', change_price)