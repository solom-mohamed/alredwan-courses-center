import type { CourseQueryParams } from "@/actions/courses";

type SearchParams = { [key: string]: string | string[] | undefined };

const STATE_FILTERS = new Set(["ongoing", "upcoming", "ended"]);
const AVAILABILITY_FILTERS = new Set(["open", "full"]);

/**
 * Maps the `sort-by` keys of `sortConfig` (dashboard-all-courses-view-config)
 * to the `ordering` fields accepted by GET /api/courses/.
 */
const SORT_FIELDS: Record<string, string> = {
  title: "name",
  season: "season__name",
  startDate: "start_date",
  endDate: "end_date",
  price: "price",
  capacity: "capacity",
  enrollments: "_enrolled_count",
};

const getParam = (searchParams: SearchParams, key: string) => {
  const value = searchParams[key];
  return typeof value === "string" && value ? value : undefined;
};

/**
 * The physical-courses catalogue is paginated on the server, so the
 * search / filter / sort menus can't work on the current page alone —
 * translate their URL params into API query params instead.
 */
export function getCourseCatalogQuery(
  searchParams: SearchParams,
): CourseQueryParams {
  const query: CourseQueryParams = {
    page: Number(getParam(searchParams, "page")) || 1,
    page_size: 8,
    search: getParam(searchParams, "search"),
    season: getParam(searchParams, "season"),
  };

  const filter = getParam(searchParams, "filter");
  if (filter) {
    if (STATE_FILTERS.has(filter)) query.state = filter;
    else if (AVAILABILITY_FILTERS.has(filter)) query.availability = filter;
    else query.season_name = filter;
  }

  const [sortField, direction] = getParam(searchParams, "sort-by")?.split("-") ?? [];
  const ordering = sortField ? SORT_FIELDS[sortField] : undefined;
  if (ordering) {
    query.ordering = direction === "desc" ? `-${ordering}` : ordering;
  }

  return query;
}
