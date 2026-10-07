from django.db.models import F, Q
from django.utils import timezone
from django_filters import CharFilter, ChoiceFilter, FilterSet
from courses.models import Course

"""

    filterset_fields = ['is_active', 'season',
                        'instructor', 'for_adults', 'tags']
"""


class CoursePriceFilter(FilterSet):
    """FilterSet for filtering courses by price range"""
    class Meta:
        model = Course
        fields = {
            'price': ['gte', 'lte'],
            'is_active': ['exact'],
            'season': ['exact'],
            'instructor': ['exact'],
            'for_adults': ['exact'],
            'tags': ['exact'],
            'name': ['icontains'],
            'description': ['icontains'],

        }


class CourseListFilter(FilterSet):
    """
    Filters for GET /api/courses/.

    On top of the plain field lookups it adds the catalogue filters the
    frontend offers in its "اختيار حسب" menu:
    - state: ongoing | upcoming | ended (relative to today)
    - availability: open | full (needs the ``_enrolled_count`` annotation)
    - season_name: exact season name
    """
    STATE_CHOICES = (
        ('ongoing', 'ongoing'),
        ('upcoming', 'upcoming'),
        ('ended', 'ended'),
    )
    AVAILABILITY_CHOICES = (
        ('open', 'open'),
        ('full', 'full'),
    )

    state = ChoiceFilter(choices=STATE_CHOICES, method='filter_state')
    availability = ChoiceFilter(
        choices=AVAILABILITY_CHOICES, method='filter_availability')
    season_name = CharFilter(field_name='season__name', lookup_expr='exact')

    class Meta:
        model = Course
        fields = {
            'is_active': ['exact'],
            'season': ['exact'],
            'instructor': ['exact'],
            'for_adults': ['exact'],
            'tags': ['exact'],
            'price': ['gte', 'lte'],
            'start_date': ['gte', 'lte'],
            'end_date': ['gte', 'lte'],
            'capacity': ['gte', 'lte'],
            'min_age': ['lte'],
            'max_age': ['gte'],
            'num_lectures': ['gte', 'lte'],
            'season__season_type': ['exact'],
            'season__is_active': ['exact'],
            'instructor__type': ['exact'],
        }

    def filter_state(self, queryset, name, value):
        today = timezone.localdate()
        if value == 'upcoming':
            return queryset.filter(start_date__gt=today)
        if value == 'ended':
            return queryset.filter(end_date__lt=today)
        # ongoing: started, and either open-ended or not finished yet
        return queryset.filter(start_date__lte=today).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today))

    def filter_availability(self, queryset, name, value):
        if value == 'full':
            return queryset.filter(_enrolled_count__gte=F('capacity'))
        return queryset.filter(_enrolled_count__lt=F('capacity'))
