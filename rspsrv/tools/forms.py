from django import forms


class BaseRespinaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BaseRespinaForm, self).__init__(*args, **kwargs)
        self.error_list = []

    def clean(self):
        cleaned_data = super(BaseRespinaForm, self).clean()

        for error in self.errors:
            data = self[error].errors.data[0]
            self.error_list.append({error: data.code})

        return cleaned_data


class BaseRespinaModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BaseRespinaModelForm, self).__init__(*args, **kwargs)
        self.error_list = []

    def clean(self):
        cleaned_data = super(BaseRespinaModelForm, self).clean()

        for error in self.errors:
            data = self[error].errors.data[0]
            self.error_list.append({error: data.code})

        return cleaned_data
