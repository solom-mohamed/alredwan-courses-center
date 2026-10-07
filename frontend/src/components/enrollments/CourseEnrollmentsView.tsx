"use client";

import { parseISO } from "date-fns";
import DataViewLegacy from "@/components/ui/data-view/DataView";
import DataViewBodyLegacy from "@/components/ui/data-view/DataViewBody";
import DataViewCellLegacy from "@/components/ui/data-view/DataViewCell";
import { DataViewPaginationLegacy } from "@/components/ui/data-view/DataViewPagination";
import {
  DataViewHeaderLegacy,
  DataViewRowLegacy,
} from "@/components/ui/data-view/DataViewRow";
import DataViewSearchLegacy from "@/components/ui/data-view/DataViewSearch";
import StatusBadge from "@/components/ui/StatusBadge";
import { cn, formatDate, toHindiDigits } from "@/lib/utils";
import type { InstructorEnrollmentListItem } from "@/types/entities";

const participantTranslationMap: Record<
  NonNullable<InstructorEnrollmentListItem["participant_type"]>,
  string
> = {
  child: "طفل",
  student: "طالب",
};

const enrollmentStatusMap: Record<
  InstructorEnrollmentListItem["status"],
  { label: string; color: string }
> = {
  active: {
    label: "نشط",
    color: cn("bg-green-300"),
  },
  completed: {
    label: "مكتمل",
    color: cn("bg-blue-300"),
  },
  dropped: {
    label: "ملغى",
    color: cn("bg-gray-300"),
  },
  refunded: {
    label: "مسترد",
    color: cn("bg-purple-300"),
  },
  suspended: {
    label: "معلق",
    color: cn("bg-amber-300"),
  },
};

export default function CourseEnrollmentsView({
  enrollments,
}: {
  enrollments: InstructorEnrollmentListItem[];
}) {
  return (
    <DataViewLegacy
      data={enrollments}
      gridLayout={cn("grid-cols-[0.25fr_1.5fr_1.5fr_1fr_1fr_1fr_1fr]")}
      maxItemsPerPage={5}
      filterConfig={{}}
      sortConfig={{}}
    >
      <div className="relative z-100 mb-14 flex items-center gap-32">
        <DataViewSearchLegacy />
        {/* <DataViewSort />
        <DataViewFilter /> */}
      </div>

      <DataViewHeaderLegacy>
        <DataViewCellLegacy>م</DataViewCellLegacy>
        <DataViewCellLegacy>الدورة</DataViewCellLegacy>
        <DataViewCellLegacy>الطالب</DataViewCellLegacy>
        <DataViewCellLegacy>نوع الطالب</DataViewCellLegacy>
        <DataViewCellLegacy>رقم الهاتف</DataViewCellLegacy>
        <DataViewCellLegacy>الحالة</DataViewCellLegacy>
        <DataViewCellLegacy>وقت الالتحاق</DataViewCellLegacy>
      </DataViewHeaderLegacy>

      <DataViewBodyLegacy<InstructorEnrollmentListItem>
        render={{
          table: (item, i) => {
            const { color: statusColor, label: statusLabel } =
              enrollmentStatusMap[item.status];

            return (
              <DataViewRowLegacy key={item.id} index={i}>
                <DataViewCellLegacy>{toHindiDigits(i + 1)}</DataViewCellLegacy>
                <DataViewCellLegacy>{item.course_name}</DataViewCellLegacy>
                <DataViewCellLegacy>{item.participant_name}</DataViewCellLegacy>
                <DataViewCellLegacy>
                  {item.participant_type
                    ? participantTranslationMap[item.participant_type]
                    : "غير محدد"}
                </DataViewCellLegacy>
                <DataViewCellLegacy>
                  {item.participant_phone
                    ? toHindiDigits(item.participant_phone.slice(2), true)
                    : "غير معرف"}
                </DataViewCellLegacy>
                <DataViewCellLegacy>
                  <StatusBadge className={statusColor}>
                    {statusLabel}
                  </StatusBadge>
                </DataViewCellLegacy>
                <DataViewCellLegacy>
                  {formatDate(parseISO(item.enrolled_at))}
                </DataViewCellLegacy>
              </DataViewRowLegacy>
            );
          },

          cards: () => null,
        }}
      />

      <DataViewPaginationLegacy />
    </DataViewLegacy>
  );
}
