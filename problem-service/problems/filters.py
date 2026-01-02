from django_filters import rest_framework as filters
from .models import Problem
from django.db.models import Q

class ProblemFilter(filters.FilterSet):
    tags = filters.CharFilter(method="filter_tags")

    def filter_tags(self, queryset, name, value):
        tag_list = [tag.strip() for tag in value.split(",")]
        q = Q()
        for tag in tag_list:
            q |= Q(tags__contains=[tag])
        return queryset.filter(q)

    class Meta:
        model = Problem
        fields = ["difficulty", "category", "tags"]
