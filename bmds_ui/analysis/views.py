from typing import ClassVar

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, Template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
)

from ..common.views import HtmxView, action, desktop_only, int_or_404, uuid_or_404
from . import constants, forms, models
from .reporting.analytics import get_cached_analytics
from .utils import get_citation


class Home(TemplateView):
    template_name = "analysis/home.html"

    def _render_template(self, extra):
        context = RequestContext(self.request, extra)
        content = models.Content.get_cached_content(models.ContentType.HOMEPAGE)
        return Template(content["template"]).render(context)

    def days_to_keep(self, days: int) -> str:
        if days == 365:
            return "1 year"
        elif days < 365 or days % 365 > 0:
            return f"{days} days"
        return f"{days // 365} years"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            days_to_keep_analyses=self.days_to_keep(settings.DAYS_TO_KEEP_ANALYSES),
            citation=get_citation(),
        )
        context["page"] = self._render_template(context)
        return context


class DesktopHome(ListView):
    template_name = "analysis/desktop_home.html"
    model = models.Analysis
    queryset = models.Analysis.objects.all()
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        if q := self.request.GET.get("q"):
            qs = qs.filter(inputs__analysis_name__icontains=q)
        if self.request.GET.get("starred"):
            qs = qs.filter(starred=True)
        if c := self.request.GET.get("collection"):
            if c.isnumeric():
                qs = qs.filter(collections=c)
        if mt := self.request.GET.get("modeltype", ""):
            qs = qs.filter(inputs__dataset_type=mt)
        return qs.prefetch_related("collections").order_by("-last_updated", "-created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.request.GET.get("collection", "")
        context.update(
            q=self.request.GET.get("q", ""),
            starred=len(self.request.GET.get("starred", "")) > 0,
            collection=int(collection) if collection.isnumeric() else "",
            collection_qs=models.Collection.objects.all(),
            collections=models.Collection.opts(),
            model_types=constants.model_types,
            now=now(),
            has_query=len(self.request.GET) > 0,
        )
        return context


@method_decorator(desktop_only, name="dispatch")
class DesktopActions(HtmxView):
    actions: ClassVar[set[str]] = {
        "toggle_star",
        "collection_detail",
        "collection_create",
        "collection_update",
        "collection_delete",
    }

    @action()
    def toggle_star(self, request: HttpRequest, **kw):
        id = uuid_or_404(request.GET.get("id", ""))
        object = get_object_or_404(models.Analysis, id=id)
        object.starred = not object.starred
        models.Analysis.objects.bulk_update([object], ["starred"])
        return render(
            request,
            "analysis/fragments/td_star.html",
            {"object": object},
        )

    @action()
    def collection_detail(self, request: HttpRequest, **kw):
        id = int_or_404(request.GET.get("id", ""))
        object = get_object_or_404(models.Collection, id=id)
        return render(
            request,
            "analysis/fragments/collection_li.html",
            {"object": object},
        )

    def _render_collection_item(self, request: HttpRequest, instance: models.Collection):
        return render(
            request,
            "analysis/fragments/collection_li.html",
            {"object": instance},
        )

    def _render_collection_form(
        self,
        request: HttpRequest,
        form: forms.CollectionForm,
        instance: models.Collection | None,
    ):
        return render(
            request,
            "analysis/fragments/collection_form.html",
            {"form": form, "object": instance},
        )

    @action(methods=("get", "post"))
    def collection_create(self, request: HttpRequest, **kw):
        data = request.POST if request.method == "POST" else None
        form = forms.CollectionForm(data=data)
        if request.method == "POST" and form.is_valid():
            form.instance.save()
            return self._render_collection_item(request, form.instance)
        return self._render_collection_form(request, form, None)

    @action(methods=("get", "post"))
    def collection_update(self, request: HttpRequest, **kw):
        id = int_or_404(request.GET.get("id", ""))
        object = get_object_or_404(models.Collection, id=id)
        data = request.POST if request.method == "POST" else None
        form = forms.CollectionForm(instance=object, data=data)
        if request.method == "POST" and form.is_valid():
            form.save()
            return self._render_collection_item(request, form.instance)
        return self._render_collection_form(request, form, object)

    @action(methods=("delete",))
    def collection_delete(self, request: HttpRequest, **kw):
        id = int_or_404(request.GET.get("id", ""))
        object = get_object_or_404(models.Collection, id=id)
        object.delete()
        return HttpResponse("")


class AnalysisCreate(CreateView):
    model = models.Analysis
    form_class = forms.CreateAnalysisForm
    http_method_names: ClassVar[list[str]] = ["post"]

    def get_success_url(self):
        return self.object.get_edit_url()


class AnalysisHistory(TemplateView):
    template_name: str = "analysis/analysis_history.html"


@method_decorator(staff_member_required, name="dispatch")
class Analytics(TemplateView):
    template_name: str = "analysis/analytics.html"

    def get_context_data(self, **kwargs) -> dict:
        kwargs.update(config=get_cached_analytics())
        return super().get_context_data(**kwargs)


def get_analysis_or_404(pk: str, password: str | None = "") -> tuple[models.Analysis, bool]:
    """Return an analysis object and if a correct password is provided for this object.

    Args:
        pk (str): The UUID for the analysis
        password (Optional[str]): A edit password for this analysis

    Returns:
        tuple[models.Analysis, bool]: An analysis object and if it has a correct password

    Raises:
        Http404: if the selected object cannot be found
    """
    filters = dict(pk=pk)
    if password:
        filters["password"] = password
    analysis = get_object_or_404(models.Analysis, **filters)
    return analysis, "password" in filters


class AnalysisDetail(DetailView):
    model = models.Analysis

    def get_object(self, queryset=None):
        analysis, can_edit = get_analysis_or_404(self.kwargs["pk"], self.kwargs.get("password"))
        self.can_edit = can_edit
        return analysis

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["config"] = {
            "apiUrl": self.object.get_api_url(),
            "url": self.object.get_absolute_url(),
            "excelUrl": self.object.get_excel_url(),
            "wordUrl": self.object.get_word_url(),
            "future": settings.ALWAYS_SHOW_FUTURE
            or (self.request.user.is_staff and bool(self.request.GET.get("future"))),
            "is_desktop": settings.IS_DESKTOP,
            "cloneUrl": self.object.get_clone_url(),
        }
        if self.can_edit:
            context["config"]["editSettings"] = {
                "csrfToken": get_token(self.request),
                "editKey": self.object.password,
                "viewUrl": self.request.build_absolute_uri(self.object.get_absolute_url()),
                "editUrl": self.request.build_absolute_uri(self.object.get_edit_url()),
                "starUrl": self.request.build_absolute_uri(self.object.get_star_url()),
                "collectionUrl": self.request.build_absolute_uri(self.object.get_collections_url()),
                "renewUrl": self.request.build_absolute_uri(self.object.get_renew_url()),
                "deleteUrl": self.request.build_absolute_uri(self.object.get_delete_url()),
                "patchInputUrl": self.object.get_api_patch_inputs_url(),
                "executeUrl": self.object.get_api_execute_url(),
                "executeResetUrl": self.object.get_api_execute_reset_url(),
                "deleteDateStr": self.object.deletion_date_str,
                "deletionDaysUntilDeletion": self.object.days_until_deletion,
                "collections": models.Collection.opts(),
            }
        return context


class AnalysisRenew(RedirectView):
    """Renew the current analysis and redirect back to editing"""

    def get_redirect_url(self, *args, **kwargs):
        analysis, _ = get_analysis_or_404(self.kwargs["pk"], self.kwargs["password"])
        analysis.renew()
        analysis.save()
        return analysis.get_edit_url()


class AnalysisClone(RedirectView):
    """Clone the current analysis"""

    def get_redirect_url(self, *args, **kwargs):
        analysis, _ = get_analysis_or_404(self.kwargs["pk"])
        analysis.id = None
        analysis.inputs["analysis_name"] = analysis.inputs.get("analysis_name", "") + " (clone)"
        analysis.inputs["analysis_description"] = (
            analysis.inputs.get("analysis_description", "") + f" (cloned from {kwargs['pk']})"
        )
        analysis.save()
        return analysis.get_edit_url()


class AnalysisDelete(DeleteView):
    """Delete the current analysis"""

    model = models.Analysis
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        analysis, _ = get_analysis_or_404(self.kwargs["pk"], self.kwargs["password"])
        return analysis


class PolyKAdjustment(TemplateView):
    template_name: str = "analysis/polyk.html"


class RaoScottAdjustment(TemplateView):
    template_name: str = "analysis/rao-scott.html"
