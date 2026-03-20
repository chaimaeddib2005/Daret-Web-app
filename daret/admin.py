from django.contrib import admin
from .models import Circle, CircleMembership, Contribution, Payout, Dispute, TrustRating


class CircleMembershipInline(admin.TabularInline):
    model = CircleMembership
    extra = 0


class ContributionInline(admin.TabularInline):
    model = Contribution
    extra = 0


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ['name', 'organizer', 'status', 'frequency', 'contribution_amount', 'current_round', 'created_at']
    list_filter = ['status', 'frequency', 'payout_order_method']
    search_fields = ['name', 'organizer__username']
    inlines = [CircleMembershipInline]


@admin.register(CircleMembership)
class CircleMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'circle', 'status', 'payout_order', 'trust_score', 'has_received_payout']
    list_filter = ['status']
    search_fields = ['user__username', 'circle__name']


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ['membership', 'round_number', 'amount', 'status', 'paid_date']
    list_filter = ['status']
    actions = ['mark_as_paid', 'mark_as_late']

    def mark_as_paid(self, request, queryset):
        for c in queryset:
            c.mark_paid()
    mark_as_paid.short_description = 'Mark selected contributions as paid'

    def mark_as_late(self, request, queryset):
        queryset.update(status='late')
    mark_as_late.short_description = 'Mark selected contributions as late'


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'circle', 'round_number', 'total_amount', 'is_paid', 'paid_at']
    list_filter = ['is_paid']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['circle', 'raised_by', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['circle__name', 'raised_by__username']


@admin.register(TrustRating)
class TrustRatingAdmin(admin.ModelAdmin):
    list_display = ['rater', 'rated_user', 'circle', 'score', 'created_at']
