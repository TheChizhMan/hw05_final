from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm, CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


send_mail(
    'Тема письма',
    'Текст письма.',
    'from@example.com',  # Это поле "От кого"
    ['to@example.com'],  # Это поле "Кому" (можно указать список адресов)
    fail_silently=False
)


def only_user_view(request):
    if not request.user.is_authenticated:
        return redirect('/auth/login/')


def user_contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['body']
            name = name.strip()
            email = email.lower()
            contact = form.save(commit=False)
            contact.name = name
            contact.email = email
            contact.subject = subject
            contact.message = message
            contact.save()
            return redirect('/thank-you/')
        return render(request, 'contact.html', {'form': form})
    form = ContactForm()
    return render(request, 'contact.html', {'form': form})
