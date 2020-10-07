import json

from rest_framework import serializers

from data.models import Task, Submission, UserProfile, UserHandle, UserGroup, GroupMember
from info.models import Assignment, TaskSheet, TaskSheetTask
from stats.models import TaskStatistics, LadderStatistics, Ladder, UserStatistics


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


class UserStatisticsSerializer(serializers.ModelSerializer):
    tag_stats = serializers.SerializerMethodField('get_tag_stats')
    activity = serializers.SerializerMethodField('get_activity')

    def get_tag_stats(self, profile):
        return json.loads(profile.tag_stats)

    def get_activity(self, profile):
        return json.loads(profile.activity)

    class Meta:
        model = UserStatistics
        fields = ['tasks_solved_count', 'tasks_tried_count', 'total_points', 'rank',
                  'tag_stats', 'activity']


class ProfileSerializer(serializers.ModelSerializer):
    handles = serializers.SerializerMethodField('get_handles')
    statistics = UserStatisticsSerializer()

    def get_handles(self, profile):
        handles = UserHandle.objects.filter(user=profile).select_related('judge')

        return [{
            "judge_id": handle.judge.judge_id,
            "handle": handle.handle,
        } for handle in handles]

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username', 'avatar_url', 'handles', 'created_at', 'statistics']


class ProfileSerializerTiny(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username', 'avatar_url', 'created_at']


class LadderStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LadderStatistics
        fields = ['total_points', 'rank']


class LadderSerializer(serializers.ModelSerializer):
    profile = ProfileSerializerTiny()
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


class GroupSerializer(serializers.ModelSerializer):
    author = ProfileSerializerTiny()

    class Meta:
        model = UserGroup
        fields = ['group_id', 'name', 'description', 'author', 'visibility']


class GroupMemberSerializer(serializers.ModelSerializer):
    profile = ProfileSerializerTiny()

    class Meta:
        model = GroupMember
        fields = ['profile', 'role']


class AssignmentSerializer(serializers.ModelSerializer):
    tasks_dict = None

    def __init__(self, list, **kwargs):
        self.list = list
        super(AssignmentSerializer, self).__init__(list, **kwargs)

    def get_tasks(self, sheet):
        if self.tasks_dict is None:
            tasks = list(TaskSheetTask.objects
                         .filter(sheet__in=[a.sheet for a in self.list])
                         .select_related('sheet', 'task', 'task__statistics', 'task__judge'))
            tasks_dict = {}
            for task in tasks:
                task_list = tasks_dict.get(task.sheet, [])
                task_list.append({
                    "task": TaskSerializer(task.task).data,
                    "score": task.score,
                })
                tasks_dict[task.sheet] = task_list
            self.tasks_dict = tasks_dict
        return self.tasks_dict.get(sheet, [])

    def to_representation(self, assignment):
        data = super(AssignmentSerializer, self).to_representation(assignment)
        sheet: TaskSheet = assignment.sheet
        data['sheet'] = {
            'tasks': self.get_tasks(sheet),
            'title': sheet.title,
            'description': sheet.description,
        }
        return data

    class Meta:
        model = Assignment
        fields = ["assigned_on", "end_on"]
