# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils import six
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm
from djangular.forms import NgDeclarativeFieldsMetaclass, NgModelFormMetaclass, NgFormBaseMixin, NgModelFormMixin
from redactor.widgets import RedactorEditor


# Cette classe permet de générer les labels avant les inputs quand on utilise django-angular
class BiblioBootstrap3FormMixin(NgFormBaseMixin):
    field_css_classes = 'form-group has-feedback'
    widget_css_classes = 'form-control'
    form_error_css_classes = 'djng-form-errors'
    field_error_css_classes = 'djng-form-control-feedback djng-field-errors'
    field_mixins_module = 'djangular.styling.bootstrap3.field_mixins'

    def as_div(self):
        """
        Returns this form rendered as HTML with <div class="form-group">s for each form field.
        """
        # wrap non-field-errors into <div>-element to prevent re-boxing
        error_row = '<div class="djng-line-spreader">%s</div>'
        div_element = self._html_output(
            normal_row='<div%(html_class_attr)s>%(field)s%(label)s%(help_text)s%(errors)s</div>',
            error_row=error_row,
            row_ender='</div>',
            help_text_html='<span class="help-block">%s</span>',
            errors_on_separate_row=False)
        return div_element

class BiblioBaseForm(BaseForm):
    def __init__(self, data=None, *args, **kwargs):
        super(BiblioBaseForm, self).__init__(data, *args, **kwargs)
        for field in self.fields.itervalues():
            if field.label!='':
                field.widget.attrs['onfocus'] = u"this.placeholder = ''"
                field.widget.attrs['onblur'] = u"this.placeholder = '%s'" % field.label
                field.widget.attrs['placeholder'] = field.label

class BiblioBaseModelForm(BaseModelForm):
    def __init__(self, data=None, *args, **kwargs):
        super(BiblioBaseModelForm, self).__init__(data, *args, **kwargs)
        for field in self.fields.itervalues():
            if field.label!='':
                field.widget.attrs['onfocus'] = u"this.placeholder = ''"
                field.widget.attrs['onblur'] = u"this.placeholder = '%s'" % field.label
                field.widget.attrs['placeholder'] = field.label


class Bootstrap3Form(six.with_metaclass(NgDeclarativeFieldsMetaclass, BiblioBootstrap3FormMixin, NgFormBaseMixin, BiblioBaseForm)):
    """
    Convenience class to be used instead of Django's internal ``forms.Form`` when declaring
    a form to be used with AngularJS and Bootstrap3 styling.
    """


class Bootstrap3ModelForm(six.with_metaclass(NgModelFormMetaclass, BiblioBootstrap3FormMixin, NgFormBaseMixin, BiblioBaseModelForm)):
    """
    Convenience class to be used instead of Django's internal ``forms.ModelForm`` when declaring
    a model form to be used with AngularJS and Bootstrap3 styling.
    """
