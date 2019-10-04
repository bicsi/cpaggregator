from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views import generic

from data.models import UserProfile, Task, Submission, UserGroup
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
            Submission.best.filter(
                author__user__user=self.request.user,
                task__in=task_list)}
        favorite_tasks = {self.request.user.profile.favorite_tasks.values_list('task', flat=True)}

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

        context['owned_groups_data'] = build_group_card_context(
            self.request,
            self.request.user.profile.owned_groups.all())

        context['assigned_groups_data'] = build_group_card_context(
            self.request,
            self.request.user.profile.assigned_groups.all())

        return context
