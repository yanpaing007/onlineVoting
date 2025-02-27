from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.views import View
from .utils import get_event_status
from ..forms import RegisterForm


class RegistrationView(View):
    form_class = RegisterForm
    template_name = "voting/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")  # Redirect authenticated users
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration Successful!")
            return redirect("login")  # Redirect to login after successful registration
        return render(request, self.template_name, {"form": form})


class LoginView(View):
    template_name = "voting/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")  # Get the value of 'remember' checkbox

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Set session expiration based on 'remember' checkbox
            if remember:
                request.session.set_expiry(1209600)  # Set session to 2 weeks
            else:
                request.session.set_expiry(0)  # Set session to expire at browser close
            messages.success(request, "Login Success!")
            return redirect(
                "voting:event_list"
            )  # Redirect to a success page or home page
        else:
            messages.error(request, "Invalid username or password")

        return render(request, self.template_name)
