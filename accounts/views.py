from .models import StudentProfile
from .forms import StudentProfileForm
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


# Регистрация пользователя
def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:dashboard')

    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


# Личный кабинет пользователя
@login_required
@login_required
def dashboard(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        'accounts/dashboard.html',
        {'profile': profile}
    )

@login_required
def edit_profile(request):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        form = StudentProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect('accounts:dashboard')

    else:
        form = StudentProfileForm(instance=profile)

    return render(
        request,
        'accounts/profile.html',
        {'form': form}
    )