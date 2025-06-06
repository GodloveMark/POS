from django import forms
from .models import Expenditure,Customer, Supplier


class ExpenditureForm(forms.ModelForm):
    class Meta:
        model = Expenditure
        fields = ['title', 'description', 'amount', 'date_spent']
    
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_spent': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }



class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
        }
    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         for field_name, field in self.fields.items():
             field.widget.attrs['class'] = 'form-control'


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            
        }
    def __init__(self, *args, **kwargs):
         super().__init__(*args, **kwargs)
         for field_name, field in self.fields.items():
             field.widget.attrs['class'] = 'form-control'



from .models import StockEntry, Product, Store

class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['product', 'quantity', 'cost_price', 'date_received', 'store']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select form-select-sm rounded-0'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm rounded-0', 'min': '1'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control form-control-sm rounded-0', 'step': '0.01', 'min': '0'}),
            'date_received': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm rounded-0'}),
            'store': forms.Select(attrs={'class': 'form-select form-select-sm rounded-0'}),
        }

    def __init__(self, *args, user=None, **kwargs):
      super().__init__(*args, **kwargs)

      store = Store.objects.filter(owner=user).first()

      if store:
          self.fields['product'].queryset = Product.objects.filter(store=store)
          self.fields['store'].queryset = Store.objects.filter(pk=store.pk)
          self.fields['store'].initial = store
          self.fields['store'].widget = forms.HiddenInput()
      else:
          self.fields['product'].queryset = Product.objects.none()
          self.fields['store'].queryset = Store.objects.none()
          self.fields['store'].widget = forms.HiddenInput()
