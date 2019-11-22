from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views import generic

from core.logging import log
from data.models import UserProfile, Task, Submission, UserGroup
from info.models import Assignment, TaskSheetTask
from info.utils import build_group_card_context


class RankListView(generic.ListView):
    template_name = 'info/rank_list.html'
    paginate_by = 10
    context_object_name = 'profile_list'
    queryset = UserProfile.objects.order_by('statistics__rank')

    def get_context_data(self, **kwargs):
        kwargs['user_count'] = UserProfile.objects.count()
        return super(RankListView, self).get_context_data(**kwargs)


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'info/dashboard_detail.html'
    model = UserProfile

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)

        task_list = Task.objects.select_related('statistics').order_by('-created_at')[:5]

        # Map task to verdict of current user.
        verdict_for_user_dict = {
            submission.task: submission.verdict for submission in
            Submission.objects.best().filter(
                author__user__user=self.request.user,
                task__in=task_list)}
        favorite_tasks = {self.request.user.profile.favorite_tasks.values_list('task', flat=True)}

        assigned_groups = self.request.user.profile.assigned_groups.all()

        assignments = Assignment.objects.filter(group__in=assigned_groups) \
            .active().select_related('sheet', 'group') \
            .annotate(task_count=Count('sheet__tasks')) \
            .order_by('-assigned_on')[:4]

        tasks = TaskSheetTask.objects.filter(sheet__in=assignments.values('sheet'))
        ac_submissions = Submission.objects.best().filter(
            author__user=self.request.user.profile,
            verdict='AC')
        solved_tasks = tasks.filter(task__in=ac_submissions.values('task'))

        solved_count = {
            sheet['sheet']: sheet['solved_count']
            for sheet in solved_tasks.values('sheet')
                .order_by('sheet')
                .annotate(solved_count=Count('sheet'))}

        context['active_assignments_data'] = [{
            "assignment": assignment,
            "task_count": assignment.task_count,
            "solved_count": solved_count.get(assignment.sheet.id, 0),
        } for assignment in assignments.all()]

        context['newly_added_task_list'] = [{
            'task': task,
            'verdict_for_user': verdict_for_user_dict.get(task),
            'faved': task.id in favorite_tasks,
        } for task in task_list]

        context['popular_group_list'] = build_group_card_context(
            self.request,
            UserGroup.public
                .annotate(member_count=Count('members'))
                .order_by('-member_count')[:3])

        context['recent_best_submissions'] = Submission.objects.best().order_by('-submitted_on')[:10]

        context['owned_groups_data'] = build_group_card_context(
            self.request,
            self.request.user.profile.owned_groups.all())

        context['assigned_groups_data'] = build_group_card_context(
            self.request,
            assigned_groups)

        return context
