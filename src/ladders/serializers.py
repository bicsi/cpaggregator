from rest_framework import serializers

from data.models import UserProfile
from stats.models import LadderStatistics
from .models import LadderTask, Ladder


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username', 'avatar_url']


class LadderStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LadderStatistics
        fields = ['total_points', 'rank']


class LadderSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    statistics = LadderStatisticsSerializer()

    class Meta:
        model = Ladder
        fields = ['profile', 'statistics']
