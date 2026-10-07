import type { FunctionComponent, SVGProps } from "react";
import type { ParentChildDetail } from "@/actions/user";
import EditChildButton from "@/components/dashboard/parent/EditChildButton";
import ActiveCourseIcon from "@/components/icons/ActiveCourseIcon";
import CheckBadgeIcon from "@/components/icons/CheckBadgeIcon";
import PendingTransactionIcon from "@/components/icons/PendingTransactionIcon";
import Avatar from "@/components/ui/Avatar";
import Button from "@/components/ui/Button";
import CopyToClipboardButton from "@/components/ui/CopyToClipboardButton";
import ItemCard from "@/components/ui/ItemCard";
import ProgressBarWithLabel from "@/components/ui/ProgressBarWithLabel";
import { cn, getArabicPlural, toHindiDigits } from "@/lib/utils";

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: FunctionComponent<SVGProps<SVGSVGElement>>;
  label: string;
  value: string;
}) {
  return (
    <div className="tablet-sm:gap-4 relative flex items-center rounded-[1rem_0] bg-gray-100 p-6 font-bold text-gray-500">
      <Icon className="text-olive-300 tablet-sm:me-0 me-4 h-10 w-auto shrink-0" />
      <span className="tablet-sm:min-w-0 tablet-sm:flex-1 me-auto">
        {label}
      </span>
      {/* Absolute on desktop (fills the row height); a static square in the flex row on phones. */}
      <div className="tablet-sm:static tablet-sm:h-12 tablet-sm:shrink-0 absolute inset-y-6 left-6 grid aspect-square w-auto place-items-center rounded-[0.5rem_0] bg-gray-50 shadow-[1px_2px_2.1px_0px_rgba(0,0,0,0.17)]">
        {value}
      </div>
    </div>
  );
}

export default function ChildCard({
  index,
  child,
  activeCoursesCount,
  pendingEnrollmentsCount,
  attendanceRate,
  showActions = true,
}: {
  index: number;
  child: ParentChildDetail;
  activeCoursesCount: number;
  pendingEnrollmentsCount: number;
  attendanceRate: number;
  showActions?: boolean;
}) {
  return (
    <ItemCard
      shape="square"
      index={index}
      className="bg-gray-50"
      cardHeader={
        <div className="tablet-sm:grid-cols-1 tablet-sm:justify-items-center tablet-sm:gap-y-3 tablet-sm:text-center relative grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] items-center gap-x-6">
          <div
            className={cn(
              "tablet-sm:row-span-1 relative row-span-full aspect-square h-24 w-auto",
              "overflow-hidden rounded-full bg-gray-100",
            )}
          >
            <Avatar
              src={child.image}
              alt="Child Image"
              className="object-cover"
            />
          </div>

          <div className="tablet-sm:w-full tablet-sm:items-center tablet-sm:pe-0 tablet-sm:text-center flex flex-col overflow-hidden pe-30 text-right">
            <span
              className="tablet-sm:line-clamp-2 tablet-sm:whitespace-normal block truncate text-[1.6rem] font-bold"
              title={`${child.first_name} ${child.last_name}`}
            >
              {`(${toHindiDigits(index + 1)}) ${child.first_name} ${child.last_name}`}
            </span>
            <span>
              {child.age}{" "}
              {getArabicPlural(child.age, {
                plural: "سنين",
                singular: "سنة",
                twofer: "سنتين",
              })}
            </span>
          </div>

          {/* Floats at the top-left corner on desktop; sits under the name on phones. */}
          <CopyToClipboardButton className="tablet-sm:static tablet-sm:mt-1 absolute top-4 left-0 rounded-[0_1rem] px-5 py-2 font-black shadow-[0_0.909px_0.909px_0_rgba(0,0,0,0.25),1.591px_1.364px_3.319px_0_rgba(0,0,0,0.25)]!">
            {child.unique_code}
          </CopyToClipboardButton>
        </div>
      }
      cardFooter={
        <div className="tablet-sm:flex-col tablet-sm:items-stretch flex w-full items-center justify-between gap-4">
          {showActions && (
            <div className="tablet-sm:justify-end flex items-center gap-2">
              <EditChildButton child={child} />
            </div>
          )}
          <Button
            size="small"
            className="bg-olive-300 tablet-sm:ms-0 tablet-sm:w-full ms-auto"
            href={`/dashboard/my-children/${child.id}`}
          >
            عرض لوحة التحكم
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-8 pt-8 pb-12">
        <StatCard
          icon={ActiveCourseIcon}
          label="الدورات النشطة"
          value={toHindiDigits(activeCoursesCount)}
        />
        <StatCard
          icon={PendingTransactionIcon}
          label="الطلبات المعلقة"
          value={toHindiDigits(pendingEnrollmentsCount)}
        />
        <ProgressBarWithLabel
          icon={CheckBadgeIcon}
          label="معدل الحضور"
          progress={attendanceRate}
        />
      </div>
    </ItemCard>
  );
}
