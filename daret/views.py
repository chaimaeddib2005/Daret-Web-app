import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django import forms

from .models import Circle, CircleMembership, Contribution, Payout, Dispute, TrustRating


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name  = forms.CharField(max_length=30, required=False)
    email      = forms.EmailField(required=False)
    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class CircleForm(forms.ModelForm):
    class Meta:
        model  = Circle
        fields = ['name', 'description', 'contribution_amount', 'frequency', 'max_members', 'payout_order_method', 'rules']


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'daret/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to DARET!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'daret/register.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    circles = Circle.objects.filter(
        memberships__user=request.user, memberships__status='approved'
    ).distinct()
    for c in circles:
        c.approved_member_count = c.memberships.filter(status='approved').count()

    active_count = circles.filter(status='active').count()
    my_memberships = CircleMembership.objects.filter(user=request.user, status='approved')
    all_contributions = Contribution.objects.filter(membership__in=my_memberships)
    pending_count = all_contributions.filter(status='pending').count()
    recent_contributions = all_contributions.order_by('-created_at')[:5]
    all_payouts = Payout.objects.filter(recipient=request.user)
    total_received = sum(p.total_amount for p in all_payouts.filter(is_paid=True))
    upcoming_payouts = all_payouts.order_by('round_number')[:6]

    return render(request, 'daret/dashboard.html', {
        'circles': circles,
        'active_count': active_count,
        'pending_count': pending_count,
        'recent_contributions': recent_contributions,
        'total_received': total_received,
        'upcoming_payouts': upcoming_payouts,
    })


@login_required
def circle_list(request):
    circles = Circle.objects.filter(
        memberships__user=request.user, memberships__status='approved'
    ).distinct()
    for c in circles:
        c.approved_member_count = c.memberships.filter(status='approved').count()
    return render(request, 'daret/circle_list.html', {'circles': circles})


@login_required
def circle_create(request):
    if request.method == 'POST':
        form = CircleForm(request.POST)
        if form.is_valid():
            circle = form.save(commit=False)
            circle.organizer = request.user
            circle.save()
            CircleMembership.objects.create(
                circle=circle, user=request.user, status='approved', payout_order=1
            )
            messages.success(request, f'Circle "{circle.name}" created!')
            return redirect('circle_detail', pk=circle.id)
    else:
        form = CircleForm()
    return render(request, 'daret/circle_create.html', {'form': form})


@login_required
def circle_detail(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    membership_qs = circle.memberships.filter(user=request.user)
    my_membership = membership_qs.first()

    if not circle.memberships.filter(user=request.user, status='approved').exists() and circle.organizer != request.user:
        if my_membership is None:
            messages.error(request, 'You are not a member of this circle.')
            return redirect('circle_list')

    is_organizer = circle.organizer == request.user
    approved_members = circle.memberships.filter(status='approved').order_by('payout_order')
    pending_members  = circle.memberships.filter(status='pending')
    contributions    = Contribution.objects.filter(membership__circle=circle).order_by('round_number', 'membership__user__username')
    schedule         = Payout.objects.filter(circle=circle).order_by('round_number')
    disputes         = Dispute.objects.filter(circle=circle).order_by('-created_at')
    total_rounds     = circle.get_total_rounds()
    pot_amount       = circle.get_pot_amount()

    current_payout = circle.payouts.filter(round_number=circle.current_round).first()
    next_payout    = circle.payouts.filter(round_number=circle.current_round + 1).first()
    next_recipient = next_payout.recipient if next_payout else None

    tab = request.GET.get('tab', 'overview')

    return render(request, 'daret/circle_detail.html', {
        'circle': circle,
        'is_organizer': is_organizer,
        'my_membership': my_membership,
        'approved_members': approved_members,
        'pending_members': pending_members,
        'contributions': contributions,
        'schedule': schedule,
        'disputes': disputes,
        'total_rounds': total_rounds,
        'pot_amount': pot_amount,
        'current_payout': current_payout,
        'next_recipient': next_recipient,
        'tab': tab,
    })


@login_required
def circle_join(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if request.method == 'POST':
        if circle.status != 'forming':
            messages.error(request, 'Circle is not accepting members.')
            return redirect('circle_detail', pk=pk)
        if circle.memberships.filter(status='approved').count() >= circle.max_members:
            messages.error(request, 'Circle is full.')
            return redirect('circle_detail', pk=pk)
        _, created = CircleMembership.objects.get_or_create(
            circle=circle, user=request.user, defaults={'status': 'pending'}
        )
        if created:
            messages.success(request, 'Join request submitted.')
        else:
            messages.info(request, 'You already have a request for this circle.')
    return redirect('circle_detail', pk=pk)


@login_required
def join_by_invite(request):
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        try:
            circle = Circle.objects.get(invite_token=token)
        except Circle.DoesNotExist:
            messages.error(request, 'Invalid invite token.')
            return redirect('circle_list')
        if circle.status != 'forming':
            messages.error(request, 'Circle is not accepting members.')
            return redirect('circle_list')
        if circle.memberships.filter(status='approved').count() >= circle.max_members:
            messages.error(request, 'Circle is full.')
            return redirect('circle_list')
        _, created = CircleMembership.objects.get_or_create(
            circle=circle, user=request.user, defaults={'status': 'pending'}
        )
        if created:
            messages.success(request, f'Join request sent to "{circle.name}".')
        else:
            messages.info(request, 'You already have a request for this circle.')
    return redirect('circle_list')


@login_required
def approve_member(request, circle_pk, user_id):
    circle = get_object_or_404(Circle, pk=circle_pk, organizer=request.user)
    if request.method == 'POST':
        membership = get_object_or_404(CircleMembership, circle=circle, user_id=user_id, status='pending')
        if circle.memberships.filter(status='approved').count() >= circle.max_members:
            messages.error(request, 'Circle is full.')
        else:
            membership.status = 'approved'
            membership.save()
            messages.success(request, f'{membership.user.username} approved.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def reject_member(request, circle_pk, user_id):
    circle = get_object_or_404(Circle, pk=circle_pk, organizer=request.user)
    if request.method == 'POST':
        membership = get_object_or_404(CircleMembership, circle=circle, user_id=user_id, status='pending')
        membership.status = 'rejected'
        membership.save()
        messages.success(request, f'{membership.user.username} rejected.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def set_payout_order(request, circle_pk, user_id):
    circle = get_object_or_404(Circle, pk=circle_pk, organizer=request.user)
    if request.method == 'POST':
        order = request.POST.get('order')
        membership = get_object_or_404(CircleMembership, circle=circle, user_id=user_id, status='approved')
        membership.payout_order = int(order)
        membership.save()
        messages.success(request, f'Order #{order} set for {membership.user.username}.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def circle_start(request, pk):
    circle = get_object_or_404(Circle, pk=pk, organizer=request.user)
    if request.method == 'POST':
        if circle.status != 'forming':
            messages.error(request, 'Circle is not in forming status.')
            return redirect('circle_detail', pk=pk)
        approved = list(circle.memberships.filter(status='approved'))
        if len(approved) < 2:
            messages.error(request, 'Need at least 2 approved members to start.')
            return redirect('circle_detail', pk=pk)

        if circle.payout_order_method == 'lottery':
            random.shuffle(approved)
            for i, m in enumerate(approved):
                m.payout_order = i + 1
                m.save()
        elif circle.payout_order_method == 'seniority':
            approved.sort(key=lambda m: m.joined_at)
            for i, m in enumerate(approved):
                m.payout_order = i + 1
                m.save()

        circle.status = 'active'
        circle.current_round = 1
        circle.save()

        for m in circle.memberships.filter(status='approved'):
            Contribution.objects.create(
                membership=m, round_number=1,
                amount=circle.contribution_amount, status='pending'
            )

        recipient_m = circle.memberships.filter(status='approved', payout_order=1).first()
        if recipient_m:
            Payout.objects.create(
                circle=circle, recipient=recipient_m.user,
                membership=recipient_m, round_number=1,
                total_amount=circle.get_pot_amount()
            )

        messages.success(request, 'Circle started! Round 1 is now active.')
    return redirect('circle_detail', pk=pk)


@login_required
def circle_next_round(request, pk):
    circle = get_object_or_404(Circle, pk=pk, organizer=request.user)
    if request.method == 'POST':
        if circle.status != 'active':
            messages.error(request, 'Circle is not active.')
            return redirect('circle_detail', pk=pk)

        total = circle.get_total_rounds()
        if circle.current_round >= total:
            circle.status = 'completed'
            circle.save()
            messages.success(request, 'Circle completed! All members have been paid.')
            return redirect('circle_detail', pk=pk)

        current_payout = circle.payouts.filter(round_number=circle.current_round).first()
        if current_payout and not current_payout.is_paid:
            current_payout.is_paid = True
            current_payout.paid_at = timezone.now()
            current_payout.save()
            current_payout.membership.has_received_payout = True
            current_payout.membership.save()

        next_round = circle.current_round + 1
        circle.current_round = next_round
        circle.save()

        for m in circle.memberships.filter(status='approved'):
            Contribution.objects.get_or_create(
                membership=m, round_number=next_round,
                defaults={'amount': circle.contribution_amount, 'status': 'pending'}
            )

        recipient_m = circle.memberships.filter(status='approved', payout_order=next_round).first()
        if recipient_m:
            Payout.objects.create(
                circle=circle, recipient=recipient_m.user,
                membership=recipient_m, round_number=next_round,
                total_amount=circle.get_pot_amount()
            )

        messages.success(request, f'Advanced to round {next_round}.')
    return redirect('circle_detail', pk=pk)


@login_required
def mark_contribution_paid(request, circle_pk, contrib_pk):
    contribution = get_object_or_404(Contribution, pk=contrib_pk, membership__circle_id=circle_pk)
    if request.method == 'POST':
        if contribution.membership.circle.organizer != request.user:
            messages.error(request, 'Only the organizer can mark contributions.')
        else:
            contribution.mark_paid()
            messages.success(request, 'Contribution marked as paid.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def mark_contribution_late(request, circle_pk, contrib_pk):
    contribution = get_object_or_404(Contribution, pk=contrib_pk, membership__circle_id=circle_pk)
    if request.method == 'POST':
        if contribution.membership.circle.organizer != request.user:
            messages.error(request, 'Only the organizer can mark contributions.')
        else:
            contribution.status = 'late'
            contribution.save()
            messages.success(request, 'Contribution marked as late.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def raise_dispute(request, circle_pk):
    circle = get_object_or_404(Circle, pk=circle_pk)
    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        if description:
            Dispute.objects.create(circle=circle, raised_by=request.user, description=description)
            messages.success(request, 'Dispute submitted.')
        else:
            messages.error(request, 'Please describe the issue.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def resolve_dispute(request, circle_pk, dispute_pk):
    circle = get_object_or_404(Circle, pk=circle_pk, organizer=request.user)
    dispute = get_object_or_404(Dispute, pk=dispute_pk, circle=circle)
    if request.method == 'POST':
        resolution = request.POST.get('resolution', '').strip()
        dispute.status = 'resolved'
        dispute.resolution = resolution
        dispute.resolved_at = timezone.now()
        dispute.save()
        messages.success(request, 'Dispute resolved.')
    return redirect('circle_detail', pk=circle_pk)


@login_required
def my_finances(request):
    my_memberships   = CircleMembership.objects.filter(user=request.user, status='approved')
    contributions    = Contribution.objects.filter(membership__in=my_memberships).order_by('-created_at')
    payouts          = Payout.objects.filter(recipient=request.user).order_by('round_number')
    total_contributed = sum(c.amount for c in contributions.filter(status='paid'))
    total_received    = sum(p.total_amount for p in payouts.filter(is_paid=True))
    net_balance       = total_received - total_contributed
    tab = request.GET.get('tab', 'contributions')
    return render(request, 'daret/my_finances.html', {
        'contributions': contributions,
        'payouts': payouts,
        'total_contributed': total_contributed,
        'total_received': total_received,
        'net_balance': net_balance,
        'tab': tab,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name  = request.POST.get('last_name', '')
        request.user.email      = request.POST.get('email', '')
        request.user.save()
        messages.success(request, 'Profile updated.')
    return render(request, 'daret/profile.html')
