from rest_framework import serializers

from data.models import UserProfile, Task
from stats.models import LadderStatistics, TaskStatistics
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


class TaskStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatistics
        fields = ["users_tried_count", "users_solved_count",
                  "submission_count", "favorited_count",
                  "difficulty_score"]


class TaskSerializer(serializers.ModelSerializer):
    statistics = TaskStatisticsSerializer()
    judge_id = serializers.SerializerMethodField('get_judge_id')

    def get_judge_id(self, task):
        return task.judge.judge_id

    class Meta:
        model = Task
        fields = ["name", "task_id", "statistics", "judge_id"]