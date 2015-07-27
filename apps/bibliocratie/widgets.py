from django.forms import Textarea
from redactor.widgets import RedactorEditor
from django.utils.html import format_html
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from djangular.styling.bootstrap3.widgets import CheckboxInput
from django.utils.safestring import mark_safe


class RedactorWidget(RedactorEditor):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return format_html('<textarea redactor{0}>\r\n{1}</textarea>',
                           flatatt(final_attrs),
                           force_text(value))

class CheckboxIWidget(CheckboxInput):
    def __init__(self, attrs=None, check_test=None, label=None):
        self.label=label
        super(CheckboxIWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        attrs = attrs or self.attrs
        label_attrs = ['class="checkbox-inline"']
        if 'id' in self.attrs:
            label_attrs.append(format_html('for="{0}"', self.attrs['id']))
        label_for = mark_safe(' '.join(label_attrs))
        if self.label:
            label_checkbox = mark_safe(self.label)
        else:
            label_checkbox = mark_safe(self.attrs['placeholder'])
        tag = super(CheckboxInput, self).render(name, value, attrs)
        return format_html('<label {0}>{1}<i></i>{2}</label>', label_for, tag, label_checkbox)
