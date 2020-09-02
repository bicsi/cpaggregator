from rest_framework import serializers

from data.models import Task, Submission, UserProfile, UserHandle
from stats.models import TaskStatistics, LadderStatistics, Ladder


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


class ProfileSerializer(serializers.ModelSerializer):
    handles = serializers.SerializerMethodField('get_handles')

    def get_handles(self, profile):
        handles = UserHandle.objects.filter(user=profile).select_related('judge')
        return [{
            "judge_id": handle.judge.judge_id,
            "handle": handle.handle,
        } for handle in handles]

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username', 'avatar_url', 'handles']


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


class SubmissionSerializer(serializers.ModelSerializer):
    task = TaskSerializer()
    author = serializers.SerializerMethodField('get_author')

    def get_author(self, sub):
        return sub.author.handle

    class Meta:
        model = Submission
        fields = ['submission_id', 'submitted_on', 'author', 'verdict', 'task']