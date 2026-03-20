from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


FREQ_CHOICES = [
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
]

STATUS_CHOICES = [
    ('forming', 'Forming'),
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

CONTRIBUTION_STATUS = [
    ('paid', 'Paid'),
    ('pending', 'Pending'),
    ('late', 'Late'),
]

MEMBERSHIP_STATUS = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('left', 'Left'),
]

PAYOUT_ORDER_CHOICES = [
    ('lottery', 'Lottery'),
    ('seniority', 'Seniority'),
    ('manual', 'Manual'),
]


class Circle(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_circles')
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=FREQ_CHOICES, default='monthly')
    max_members = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='forming')
    current_round = models.IntegerField(default=0)
    payout_order_method = models.CharField(max_length=10, choices=PAYOUT_ORDER_CHOICES, default='manual')
    invite_token = models.CharField(max_length=64, unique=True, blank=True)
    rules = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_total_rounds(self):
        return self.memberships.filter(status='approved').count()

    def get_pot_amount(self):
        return self.contribution_amount * self.memberships.filter(status='approved').count()

    def get_frequency_display(self):
        return dict(FREQ_CHOICES).get(self.frequency, self.frequency)

    @property
    def approved_member_count(self):
        return self.memberships.filter(status='approved').count()

    def save(self, *args, **kwargs):
        if not self.invite_token:
            import secrets
            self.invite_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class CircleMembership(models.Model):
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circle_memberships')
    status = models.CharField(max_length=20, choices=MEMBERSHIP_STATUS, default='pending')
    payout_order = models.IntegerField(null=True, blank=True)
    trust_score = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    joined_at = models.DateTimeField(auto_now_add=True)
    has_received_payout = models.BooleanField(default=False)

    class Meta:
        unique_together = ('circle', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.circle.name}"


class Contribution(models.Model):
    membership = models.ForeignKey(CircleMembership, on_delete=models.CASCADE, related_name='contributions')
    round_number = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=CONTRIBUTION_STATUS, default='pending')
    paid_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('membership', 'round_number')

    def __str__(self):
        return f"{self.membership.user.username} - Round {self.round_number} - {self.status}"

    def mark_paid(self):
        self.status = 'paid'
        self.paid_date = timezone.now()
        self.save()


class Payout(models.Model):
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='payouts')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payouts')
    membership = models.ForeignKey(CircleMembership, on_delete=models.CASCADE, related_name='payout')
    round_number = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout to {self.recipient.username} - Round {self.round_number}"


class Dispute(models.Model):
    DISPUTE_STATUS = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='raised_disputes')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=DISPUTE_STATUS, default='open')
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Dispute in {self.circle.name} by {self.raised_by.username}"


class TrustRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='ratings')
    score = models.DecimalField(max_digits=2, decimal_places=1)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rater', 'rated_user', 'circle')

    def __str__(self):
        return f"{self.rater.username} rated {self.rated_user.username}: {self.score}"
