"use client";

import { useSearchParams } from "next/navigation";
import PublicCourseCard from "@/components/courses/PublicCourseCard";
import {
  buildAllCoursesView,
  getAllCoursesFilterConfig,
  sortConfig,
} from "@/components/dashboard/dashboard-all-courses-view-config";
import DataView from "@/components/ui/data-view/DataView";
import DataViewBodyLegacy from "@/components/ui/data-view/DataViewBody";
import DataViewCellLegacy from "@/components/ui/data-view/DataViewCell";
import DataViewFilterLegacy from "@/components/ui/data-view/DataViewFilter";
import { DataViewPaginationLegacy } from "@/components/ui/data-view/DataViewPagination";
import { DataViewHeaderLegacy } from "@/components/ui/data-view/DataViewRow";
import DataViewSearchLegacy from "@/components/ui/data-view/DataViewSearch";
import { cn } from "@/lib/utils";
import type { CourseListItem } from "@/types/entities";
import DataViewSortLegacy from "../ui/data-view/DataViewSort";

export default function DashboardAllCoursesView({
  courses: inputCourses = [],
  totalCount,
  totalPages,
  currentPage,
  linkTo = "dashboard",
  showEnroll = false,
}: {
  courses?: CourseListItem[];
  totalCount?: number;
  totalPages?: number;
  currentPage?: number;
  linkTo?: "dashboard" | "landing";
  showEnroll?: boolean;
}) {
  const courses = buildAllCoursesView(inputCourses);
  const searchParams = useSearchParams();
  const filterConfig = getAllCoursesFilterConfig(
    courses,
    searchParams.get("filter"),
  );

  return (
    <DataView
      data={courses}
      maxItemsPerPage={8}
      gridLayout={cn(
        "grid-cols-[minmax(0,0.5fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,2fr)_minmax(0,0.5fr)]",
      )}
      filterConfig={filterConfig}
      sortConfig={sortConfig}
      viewLayout="cards"
      totalCount={totalCount}
      totalPages={totalPages}
      currentPage={currentPage}
      manualPagination={totalPages !== undefined || totalCount !== undefined}
    >
      <div className="tablet:flex-col tablet:items-stretch tablet:gap-12 tablet:px-16 tablet-sm:px-4 relative z-60 mb-14 flex items-center justify-between gap-16 px-4">
        <div className="tablet:max-w-full w-full max-w-[400px]">
          <DataViewSearchLegacy />
        </div>
        <div className="tablet:w-full flex items-center gap-12">
          <div className="tablet:flex-1 w-auto">
            <DataViewSortLegacy />
          </div>
          <div className="tablet:flex-1 w-auto">
            <DataViewFilterLegacy />
          </div>
        </div>
      </div>

      <DataViewHeaderLegacy className="tablet:mx-16 tablet-sm:mx-4 mx-4">
        <DataViewCellLegacy>م</DataViewCellLegacy>
        <DataViewCellLegacy>الدورة</DataViewCellLegacy>
        <DataViewCellLegacy>الموسم</DataViewCellLegacy>
        <DataViewCellLegacy>البداية</DataViewCellLegacy>
        <DataViewCellLegacy>النهاية</DataViewCellLegacy>
        <DataViewCellLegacy></DataViewCellLegacy>
      </DataViewHeaderLegacy>

      <DataViewBodyLegacy
        className="tablet:px-16 tablet-sm:px-4 tablet-sm:!grid tablet-sm:!grid-cols-1 tablet-sm:!overflow-hidden w-full px-4 [&_>_div]:!min-w-0"
        render={{
          table: () => null,

          cards: (item: CourseListItem, index) => (
            <PublicCourseCard
              linkTo={linkTo}
              course={item}
              index={index}
              key={item.id}
              showEnroll={showEnroll}
            />
          ),
        }}
      />

      <DataViewPaginationLegacy />
    </DataView>
  );
}
