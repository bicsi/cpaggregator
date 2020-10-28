import json

from rest_framework import serializers

from data.models import Task, Submission, UserProfile, UserHandle, UserGroup, GroupMember, Judge, TaskStatement, \
    TaskSource, JudgeTaskStatistic
from info.models import Assignment, TaskSheet, TaskSheetTask
from stats.models import TaskStatistics, LadderStatistics, Ladder, UserStatistics
from core.logging import log


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


class TaskSourceSerializer(serializers.ModelSerializer):
    judge_id = serializers.SerializerMethodField('get_judge_id')

    def get_judge_id(self, src):
        return src.judge.judge_id

    class Meta:
        model = TaskSource
        exclude = ["id", "judge"]


class TaskStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatement
        exclude = ["task", "id"]

class JudgeTaskStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = JudgeTaskStatistic
        exclude = ["task", "id"]


class TaskSerializerFull(serializers.ModelSerializer):
    statistics = TaskStatisticsSerializer()
    judge_id = serializers.SerializerMethodField('get_judge_id')
    statement = TaskStatementSerializer()
    source = TaskSourceSerializer()
    judge_statistics = JudgeTaskStatisticSerializer(source='judge_statistic')

    def get_judge_id(self, task):
        return task.judge.judge_id

    class Meta:
        model = Task
        fields = ["name", "task_id", "statistics", "judge_id", "statement", 
            "source", "judge_statistics"]


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


class UserHandleSerializer(serializers.ModelSerializer):
    judge_id = serializers.CharField()

    def to_internal_value(self, data):
        user = self.context['user']
        value = super(UserHandleSerializer, self).to_internal_value(data)
        judge_id = Judge.objects.get(judge_id=value['judge_id']).pk
        value['judge_id'] = judge_id
        value['user'] = user
        return value

    def to_representation(self, handle):
        data = super(UserHandleSerializer, self).to_representation(handle)
        data['judge_id'] = handle.judge.judge_id
        return data

    class Meta:
        model = UserHandle
        fields = ['judge_id', 'handle']


class ProfileSerializer(serializers.ModelSerializer):
    handles = UserHandleSerializer(many=True)
    statistics = UserStatisticsSerializer()

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username',
                  'avatar_url', 'handles', 'created_at', 'statistics']


class ProfileSerializerTiny(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'username',
                  'avatar_url']

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
        return {
            "handle": sub.author.handle,
            "profile": ProfileSerializerTiny(sub.author.user).data,
        }

    class Meta:
        model = Submission
        fields = ['submission_id', 'submitted_on', 'author', 'verdict', 'task']


class GroupSerializer(serializers.ModelSerializer):
    author = ProfileSerializer()
    members_count = serializers.IntegerField()
    assignments_count = serializers.IntegerField()

    class Meta:
        model = UserGroup
        fields = ['group_id', 'name', 'description',
                  'author', 'visibility', 'members_count', 'assignments_count']


class GroupMemberSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

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
            'sheet_id': sheet.sheet_id,
            'tasks': self.get_tasks(sheet),
            'title': sheet.title,
            'description': sheet.description,
        }
        return data

    class Meta:
        model = Assignment
        fields = ["assigned_on", "end_on"]
