"use client";
import { cva, type VariantProps } from "class-variance-authority";
import { format, parseISO } from "date-fns";
import { ChevronDown, PlusCircle } from "lucide-react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import useAuthedWebSocket from "@/hooks/useAuthedWebSocket";

import {
  manualCheckIn,
  manualCheckOut,
  markAbsent,
} from "@/actions/admin-attendances";
import DeleteIcon from "@/components/icons/deleteIcon.svg";
import DetailsIcon from "@/components/icons/detailsIcon.svg";
import EditIcon from "@/components/icons/editIcon.svg";
import MicrosoftExcelLogo from "@/components/icons/microsoftExcelLogo.svg";
import SearchIcon from "@/components/icons/searchIcon.svg";
import ClientLocalTime from "@/components/ui/ClientLocalTime";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  dropdownMenuContentStyles,
} from "@/components/ui/DropdownMenu";
import DataViewLegacy from "@/components/ui/data-view/DataView";
import DataViewBodyLegacy from "@/components/ui/data-view/DataViewBody";
import DataViewCellLegacy from "@/components/ui/data-view/DataViewCell";
import { DataViewPaginationLegacy } from "@/components/ui/data-view/DataViewPagination";
import {
  DataViewHeaderLegacy,
  DataViewRowLegacy,
} from "@/components/ui/data-view/DataViewRow";
import StatusBadge from "@/components/ui/StatusBadge";
import { useMutateSearchParams } from "@/hooks/useMutateSearchParams";
import { cn, formatTime, toHindiDigits } from "@/lib/utils";
import { filterAttendances } from "@/lib/attendance";
import type { StaffAttendanceListItem } from "@/types/entities/staff-attendance";
import type { StaffAttendanceServerEvent } from "@/types/entities/staff-attendance-events";
import AttendanceGenerationModal from "./AttendanceGenerationModal";
import AttendanceRatingModal from "./AttendanceRatingModal";

// ─── Time Badge ──────────────────────────────────────────────────────────────

const timeBadgeStyles = cva(
  "grid h-11 w-40 place-items-center transition-colors text-xl",
  {
    variants: {
      status: {
        bonus: "bg-olive-300 text-gray-100",
        penalty: "bg-[#9F2E2E] text-gray-100",
        neutral: "bg-gray-200 text-gray-900",
      },
      revert: {
        true: "rounded-[1rem_0]",
        false: "rounded-[0_1rem]",
      },
    },
    defaultVariants: { status: "neutral", revert: false },
  },
);

function TimeBadge({
  status,
  revert,
  children,
}: {
  status?: VariantProps<typeof timeBadgeStyles>["status"];
  revert?: VariantProps<typeof timeBadgeStyles>["revert"];
  children: ReactNode;
}) {
  return (
    <span className={timeBadgeStyles({ status, revert })}>{children}</span>
  );
}

// ─── Single Row ───────────────────────────────────────────────────────────────

function StaffAttendanceRow({
  attendance,
  index,
  onUpdate,
}: {
  attendance: StaffAttendanceListItem;
  index: number;
  onRate: () => void;
  onUpdate: (updated: Partial<StaffAttendanceListItem>) => void;
}) {
  const [nowTimestamp, setNowTimestamp] = useState<number | null>(null);
  const [scheduledCheckInTimestamp, setScheduledCheckInTimestamp] = useState<
    number | null
  >(null);
  const [scheduledCheckOutTimestamp, setScheduledCheckOutTimestamp] = useState<
    number | null
  >(null);
  const [isCheckingIn, setIsCheckingIn] = useState(false);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [isMarkingAbsent, setIsMarkingAbsent] = useState(false);

  const [checkInHours, checkInMinutes] = (
    attendance.scheduled_check_in_time ?? ""
  )
    .split(":")
    .map(Number);
  const [checkOutHours, checkOutMinutes] = (
    attendance.scheduled_check_out_time ?? ""
  )
    .split(":")
    .map(Number);

  const checkInTimestamp = attendance.check_in_time
    ? parseISO(attendance.check_in_time).getTime()
    : null;
  const checkOutTimestamp = attendance.check_out_time
    ? parseISO(attendance.check_out_time).getTime()
    : null;

  const isCheckInEarly =
    !!checkInTimestamp &&
    !!scheduledCheckInTimestamp &&
    scheduledCheckInTimestamp > checkInTimestamp;
  const isCheckInLate =
    !!checkInTimestamp &&
    !!scheduledCheckInTimestamp &&
    scheduledCheckInTimestamp < checkInTimestamp;
  const isCheckOutEarly =
    !!checkOutTimestamp &&
    !!scheduledCheckOutTimestamp &&
    scheduledCheckOutTimestamp > checkOutTimestamp;
  const isCheckOutLate =
    !!checkOutTimestamp &&
    !!scheduledCheckOutTimestamp &&
    scheduledCheckOutTimestamp < checkOutTimestamp;

  useEffect(() => {
    const ts = Date.now();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setNowTimestamp(ts);
    setScheduledCheckInTimestamp(
      new Date(ts).setHours(checkInHours, checkInMinutes, 0, 0),
    );
    setScheduledCheckOutTimestamp(
      new Date(ts).setHours(checkOutHours, checkOutMinutes, 0, 0),
    );
  }, [checkInHours, checkInMinutes, checkOutHours, checkOutMinutes]);

  // positional status
  const hasCheckedIn = !!attendance.check_in_time;
  const hasCheckedOut = !!attendance.check_out_time;
  const isLateNow =
    !hasCheckedIn &&
    !!nowTimestamp &&
    !!scheduledCheckInTimestamp &&
    nowTimestamp > scheduledCheckInTimestamp;

  return (
    <DataViewRowLegacy index={index} key={attendance.id}>
      {/* Row number */}
      <DataViewCellLegacy>{toHindiDigits(index + 1)}</DataViewCellLegacy>

      {/* Name */}
      <DataViewCellLegacy
        className="text-olive-700 overflow-clip font-bold text-ellipsis whitespace-nowrap"
        {...(attendance.instructor_name.length > 15
          ? { title: attendance.instructor_name }
          : {})}
      >
        {attendance.instructor_name}
      </DataViewCellLegacy>

      {/* Target */}
      <DataViewCellLegacy
        title={attendance.lecture_info?.lecture_title || undefined}
      >
        <div className="flex flex-col gap-1 whitespace-nowrap">
          <span className="text-xs text-gray-400">
            {attendance.attendance_type_display}
          </span>
          <span>{attendance.lecture_info?.course_title || "—"}</span>
        </div>
      </DataViewCellLegacy>

      {/* Scheduled check-in */}
      <DataViewCellLegacy className="whitespace-nowrap">
        <span>{formatTime(attendance.scheduled_check_in_time)}</span>
      </DataViewCellLegacy>

      {/* Scheduled checkout */}
      <DataViewCellLegacy className="whitespace-nowrap">
        <span>{formatTime(attendance.scheduled_check_out_time)}</span>
      </DataViewCellLegacy>

      {/* Divider */}
      <DataViewCellLegacy />

      {/* Actual check-in */}
      <DataViewCellLegacy className="py-0">
        <TimeBadge
          status={
            isCheckInEarly ? "bonus" : isCheckInLate ? "penalty" : "neutral"
          }
          revert
        >
          <ClientLocalTime iso={attendance.check_in_time} />
        </TimeBadge>
      </DataViewCellLegacy>

      {/* Actual checkout */}
      <DataViewCellLegacy className="py-0">
        <TimeBadge
          status={
            isCheckOutEarly ? "penalty" : isCheckOutLate ? "bonus" : "neutral"
          }
        >
          <ClientLocalTime iso={attendance.check_out_time} />
        </TimeBadge>
      </DataViewCellLegacy>

      {/* Status badge */}
      <DataViewCellLegacy className="whitespace-nowrap">
        <StatusBadge
          className={cn(
            "py-2 text-xl transition-colors",
            hasCheckedIn && !hasCheckedOut && "bg-[#dae9e0] text-[#027243]",
            hasCheckedIn && hasCheckedOut && "bg-[#c5c8fd] text-[#1227b4]",
            !hasCheckedIn && !isLateNow && "bg-gray-200 text-gray-700",
            isLateNow && "bg-[#efc2c2] text-[#952B2B]",
            attendance.status === "absent" && "bg-red-100 text-red-700",
          )}
        >
          {attendance.status === "absent"
            ? "غائب"
            : hasCheckedIn && hasCheckedOut
              ? "رحل"
              : hasCheckedIn
                ? "في المسجد"
                : isLateNow
                  ? "متأخر"
                  : "لم يأتِ بعد"}
        </StatusBadge>
      </DataViewCellLegacy>

      {/* Actions on left */}
      <DataViewCellLegacy className="flex items-center justify-center gap-5 py-0">
        {/* Mark absent */}
        <button
          title="تسجيل غياب"
          disabled={attendance.status === "absent" || isMarkingAbsent}
          className="rounded-full text-red-400 transition-colors disabled:cursor-not-allowed disabled:opacity-30"
          onClick={async () => {
            setIsMarkingAbsent(true);
            const result = await markAbsent(attendance.id);
            setIsMarkingAbsent(false);
            if (result)
              onUpdate({
                status: result.status,
                check_in_time: result.check_in_time,
                check_out_time: result.check_out_time,
              });
          }}
        >
          <Image
            src={DeleteIcon}
            alt="Delete"
            className="h-6 w-6 object-contain"
          />
        </button>

        {/* Check-in / check-out / rate */}
        {!hasCheckedIn && (
          <button
            title="تسجيل حضور"
            className="text-olive-300 rounded-full transition-colors"
            onClick={async () => {
              setIsCheckingIn(true);
              const result = await manualCheckIn(attendance.id);
              setIsCheckingIn(false);
              if (result)
                onUpdate({
                  status: result.status,
                  check_in_time: result.check_in_time,
                  check_out_time: result.check_out_time,
                });
            }}
          >
            <Image
              src={EditIcon}
              alt="Edit"
              className="h-6 w-6 object-contain"
            />
          </button>
        )}
        {hasCheckedIn && !hasCheckedOut && (
          <button
            title="تسجيل انصراف"
            className="text-olive-300 rounded-full transition-colors"
            onClick={async () => {
              setIsCheckingOut(true);
              const result = await manualCheckOut(attendance.id);
              setIsCheckingOut(false);
              if (result)
                onUpdate({
                  status: result.status,
                  check_in_time: result.check_in_time,
                  check_out_time: result.check_out_time,
                });
            }}
          >
            <Image
              src={EditIcon}
              alt="Edit"
              className="h-6 w-6 object-contain"
            />
          </button>
        )}
        <button
          title="تفاصيل"
          className="rounded-full text-gray-400 transition-colors"
        >
          <Image
            src={DetailsIcon}
            alt="Details"
            className="h-6 w-6 object-contain"
          />
        </button>
      </DataViewCellLegacy>
    </DataViewRowLegacy>
  );
}

// ─── Filter Bar ───────────────────────────────────────────────────────────────

function FilterBar({
  onExport,
  hideDate,
  onGenerate,
}: {
  onExport: () => void;
  hideDate?: boolean;
  onGenerate: () => void;
}) {
  const { mutateSearchParams, searchParams } = useMutateSearchParams();
  // Empty when one instructor's full history is shown (no date filter).
  const dateParam =
    searchParams.get("date") ||
    (searchParams.get("instructor") ? "" : format(new Date(), "yyyy-MM-dd"));
  const [localDate, setLocalDate] = useState(dateParam);
  const [prevDateParam, setPrevDateParam] = useState(dateParam);

  if (prevDateParam !== dateParam) {
    setPrevDateParam(dateParam);
    setLocalDate(dateParam);
  }

  const status = searchParams.get("status") || "";
  const attendanceType = searchParams.get("attendance_type") || "";
  const season = searchParams.get("season") || "";

  return (
    <div className="mb-14 flex flex-wrap items-center gap-6 max-[1000px]:flex-col max-[1000px]:items-stretch">
      {/* Search */}
      <div className="shadow-soft flex min-w-[220px] flex-1 items-center gap-8 rounded-[2rem_0] bg-[#F3F3F5] px-8 py-3 max-[1000px]:w-full max-[1000px]:rounded-lg">
        <Image src={SearchIcon} alt="Search" className="size-8 shrink-0" />
        <input
          placeholder="ابحث هنا..."
          defaultValue={searchParams.get("search") || ""}
          onChange={(e) =>
            mutateSearchParams([
              { key: "search", val: e.target.value },
              { key: "page", val: 1 },
            ])
          }
          className="flex-1 bg-transparent text-[1.8rem] placeholder:font-semibold placeholder:text-gray-500 focus:outline-none"
        />
      </div>

      {/* Date Filter */}
      {!hideDate && (
        <div
          onClick={(e) => {
            const input = e.currentTarget.querySelector("input");
            if (
              e.target !== input &&
              input &&
              "showPicker" in HTMLInputElement.prototype
            ) {
              try {
                input.showPicker();
              } catch (err) {}
            }
          }}
          className="shadow-soft flex cursor-pointer items-center gap-4 rounded-[0_2rem] bg-[#F3F3F5] px-8 py-3 transition-colors hover:bg-gray-100 max-[1000px]:justify-between max-[1000px]:rounded-lg"
        >
          <span className="pointer-events-none text-[1.6rem] text-gray-500">
            التاريخ:
          </span>
          <input
            type="date"
            value={localDate}
            onChange={(e) => {
              setLocalDate(e.target.value);
              // Only update URL if it looks like a full date (YYYY-MM-DD)
              if (e.target.value && e.target.value.length === 10) {
                mutateSearchParams([{ key: "date", val: e.target.value }]);
              }
            }}
            onBlur={() => {
              // Reset to today if cleared, or sync with URL if different and valid
              if (!localDate && !dateParam) return;
              if (!localDate) {
                const today = format(new Date(), "yyyy-MM-dd");
                setLocalDate(today);
                mutateSearchParams([{ key: "date", val: today }]);
              } else if (localDate.length === 10 && localDate !== dateParam) {
                mutateSearchParams([{ key: "date", val: localDate }]);
              }
            }}
            className="cursor-pointer bg-transparent text-[1.6rem] font-bold text-gray-700 focus:outline-none"
          />
        </div>
      )}

      {/* Status Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="shadow-soft flex items-center justify-between gap-8 rounded-[0_2rem] bg-[#F3F3F5] px-8 py-3 transition-colors hover:bg-gray-100 max-[1000px]:rounded-lg">
            <span className="text-[1.6rem]">
              {status === "present"
                ? "حاضر"
                : status === "absent"
                  ? "غائب"
                  : status === "late"
                    ? "متأخر"
                    : status === "not_started"
                      ? "لم يبدأ"
                      : "الحالة"}
            </span>
            <ChevronDown className="size-6 text-gray-400" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className={cn(
            dropdownMenuContentStyles,
            "z-9999 w-auto min-w-[150px]",
          )}
        >
          <DropdownMenuItem
            onClick={() => mutateSearchParams([{ key: "status", val: "" }])}
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            الكل
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([{ key: "status", val: "present" }])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            حاضر
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([{ key: "status", val: "absent" }])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            غائب
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => mutateSearchParams([{ key: "status", val: "late" }])}
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            متأخر
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([{ key: "status", val: "not_started" }])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            لم يبدأ
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Type Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="shadow-soft flex items-center justify-between gap-8 rounded-[0_2rem] bg-[#F3F3F5] px-8 py-3 transition-colors hover:bg-gray-100 max-[1000px]:rounded-lg">
            <span className="text-[1.6rem]">
              {attendanceType === "lecture"
                ? "محاضرة"
                : attendanceType === "supervision"
                  ? "إشراف"
                  : "نوع الحضور"}
            </span>
            <ChevronDown className="size-6 text-gray-400" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className={cn(
            dropdownMenuContentStyles,
            "z-9999 w-auto min-w-[150px]",
          )}
        >
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([{ key: "attendance_type", val: "" }])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            الكل
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([{ key: "attendance_type", val: "lecture" }])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            محاضرة
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() =>
              mutateSearchParams([
                { key: "attendance_type", val: "supervision" },
              ])
            }
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            إشراف
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Season Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="shadow-soft flex items-center justify-between gap-8 rounded-[0_2rem] bg-[#F3F3F5] px-8 py-3 transition-colors hover:bg-gray-100 max-[1000px]:rounded-lg">
            <span className="text-[1.6rem]">
              {season ? `الموسم ${toHindiDigits(Number(season))}` : "الموسم"}
            </span>
            <ChevronDown className="size-6 text-gray-400" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          className={cn(
            dropdownMenuContentStyles,
            "z-9999 max-h-60 w-auto min-w-[150px] overflow-y-auto",
          )}
        >
          <DropdownMenuItem
            onClick={() => mutateSearchParams([{ key: "season", val: "" }])}
            className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
          >
            الكل
          </DropdownMenuItem>
          {[1, 2, 3, 4, 5, 6].map((s) => (
            <DropdownMenuItem
              key={s}
              onClick={() =>
                mutateSearchParams([{ key: "season", val: s.toString() }])
              }
              className="cursor-pointer px-6 text-2xl hover:bg-gray-100"
            >
              الموسم {toHindiDigits(s)}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="mr-auto flex items-center gap-6 max-[1000px]:mr-0 max-[1000px]:w-full">
        {/* Generate Records Button */}
        <button
          onClick={onGenerate}
          className="shadow-soft bg-olive-700 hover:bg-olive-800 flex flex-1 items-center justify-center gap-4 rounded-lg px-6 py-3 text-white transition-colors"
        >
          <PlusCircle className="size-6" />
          <span className="text-[1.6rem] font-bold">توليد سجلات</span>
        </button>

        {/* Excel export */}
        <button
          onClick={onExport}
          className="shadow-soft flex shrink-0 items-center justify-center rounded-lg bg-[#F3F3F5] px-6 py-2 transition-colors hover:bg-gray-100"
        >
          <Image src={MicrosoftExcelLogo} alt="Excel" className="h-16 w-auto" />
        </button>
      </div>
    </div>
  );
}

// ─── Main View ────────────────────────────────────────────────────────────────

const WS_URL = `ws://${typeof window !== "undefined" ? window.location.hostname : "localhost"}:8001/ws/attendance/`;

export default function AdminAttendancesView({
  initialAttendances,
  hideDateFilter = false,
}: {
  initialAttendances: StaffAttendanceListItem[];
  hideDateFilter?: boolean;
}) {
  const [attendances, setAttendances] =
    useState<StaffAttendanceListItem[]>(initialAttendances);
  const [prevInitial, setPrevInitial] =
    useState<StaffAttendanceListItem[]>(initialAttendances);

  if (prevInitial !== initialAttendances) {
    setPrevInitial(initialAttendances);
    setAttendances(initialAttendances);
  }

  const searchParamsHook = useSearchParams();
  const [ratingModal, setRatingModal] = useState<{
    isOpen: boolean;
    attendance?: StaffAttendanceListItem;
  }>({ isOpen: false });

  const [generationModalOpen, setGenerationModalOpen] = useState(false);

  const { lastJsonMessage } =
    useAuthedWebSocket<StaffAttendanceServerEvent>(WS_URL);

  useEffect(() => {
    if (!lastJsonMessage) return;
    switch (lastJsonMessage.type) {
      case "attendance_update": {
        const { check_in_time, check_out_time, id, status } =
          lastJsonMessage.data;
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setAttendances((prev) =>
          prev.map((a) =>
            a.id === id ? { ...a, check_in_time, check_out_time, status } : a,
          ),
        );
        break;
      }
      case "attendance_rated": {
        const { id, rating } = lastJsonMessage.data;
        setAttendances((prev) =>
          prev.map((a) => (a.id === id ? { ...a, rating: Number(rating) } : a)),
        );
        break;
      }
    }
  }, [lastJsonMessage]);

  const updateAttendance = (
    id: number,
    updated: Partial<StaffAttendanceListItem>,
  ) => {
    setAttendances((prev) =>
      prev.map((a) => (a.id === id ? { ...a, ...updated } : a)),
    );
  };

  const filteredAttendances = filterAttendances(attendances, searchParamsHook);

  const handleExport = () => {
    if (filteredAttendances.length === 0) return;
    const headers = [
      "الرقم",
      "الاسم",
      "نوع الحضور",
      "الدورة",
      "ميعاد الحضور",
      "ميعاد الانصراف",
      "حضور فعلي",
      "انصراف فعلي",
      "الحالة",
    ];
    const csvContent = [
      headers.join(","),
      ...filteredAttendances.map((a, i) =>
        [
          i + 1,
          `"${a.instructor_name}"`,
          `"${a.attendance_type_display}"`,
          `"${a.lecture_info?.course_title || ""}"`,
          `"${a.scheduled_check_in_time}"`,
          `"${a.scheduled_check_out_time}"`,
          `"${a.check_in_time ? formatTime(a.check_in_time) : ""}"`,
          `"${a.check_out_time ? formatTime(a.check_out_time) : ""}"`,
          `"${a.status === "present" ? "حاضر" : a.status === "absent" ? "غائب" : a.status === "late" ? "متأخر" : "لم يبدأ"}"`,
        ].join(","),
      ),
    ].join("\n");
    const bom = "\uFEFF";
    const blob = new Blob([bom + csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `attendances_${format(new Date(), "yyyy-MM-dd")}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex h-full flex-1 flex-col">
      <FilterBar
        onExport={handleExport}
        hideDate={hideDateFilter}
        onGenerate={() => setGenerationModalOpen(true)}
      />

      <DataViewLegacy
        gridLayout="grid-cols-[minmax(0,0.4fr)_minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,0.8fr)_minmax(0,0.8fr)_minmax(0,0.25fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(0,1fr)_minmax(0,1.2fr)]"
        data={filteredAttendances}
        filterConfig={{}}
        sortConfig={{}}
      >
        <div className="flex w-full flex-1 flex-col">
          <div className="tablet-sm:overflow-x-visible w-full overflow-x-auto pb-4">
            <div className="tablet-sm:min-w-0 flex min-w-[1200px] flex-col">
              <DataViewHeaderLegacy>
                <DataViewCellLegacy>م</DataViewCellLegacy>
                <DataViewCellLegacy>الاسم</DataViewCellLegacy>
                <DataViewCellLegacy>الهدف</DataViewCellLegacy>
                <DataViewCellLegacy>الحضور</DataViewCellLegacy>
                <DataViewCellLegacy>الانصراف</DataViewCellLegacy>
                <DataViewCellLegacy />
                <DataViewCellLegacy>الحضور الفعلي</DataViewCellLegacy>
                <DataViewCellLegacy>الانصراف الفعلي</DataViewCellLegacy>
                <DataViewCellLegacy>الحالة</DataViewCellLegacy>
                <DataViewCellLegacy>إجراءات</DataViewCellLegacy>
              </DataViewHeaderLegacy>

              <DataViewBodyLegacy<StaffAttendanceListItem>
                render={{
                  table: (item, i) => (
                    <StaffAttendanceRow
                      key={item.id}
                      attendance={item}
                      index={i}
                      onRate={() =>
                        setRatingModal({ isOpen: true, attendance: item })
                      }
                      onUpdate={(updated) => updateAttendance(item.id, updated)}
                    />
                  ),
                  cards: () => null,
                }}
              />
            </div>
          </div>

          <div className="mt-auto w-full pt-10">
            <DataViewPaginationLegacy />
          </div>
        </div>
      </DataViewLegacy>

      {ratingModal.isOpen && ratingModal.attendance && (
        <AttendanceRatingModal
          isOpen={ratingModal.isOpen}
          onClose={() => setRatingModal({ isOpen: false })}
          attendanceId={ratingModal.attendance.id}
          instructorName={ratingModal.attendance.instructor_name}
          initialRating={ratingModal.attendance.rating || 0}
          onSuccess={(updated) =>
            updateAttendance(ratingModal.attendance!.id, {
              ...updated,
              rating: updated.rating ? Number(updated.rating) : null,
            })
          }
        />
      )}

      <AttendanceGenerationModal
        isOpen={generationModalOpen}
        onClose={() => setGenerationModalOpen(false)}
        onSuccess={() => {
          // You might want to refresh the page or show a toast
          window.location.reload();
        }}
      />
    </div>
  );
}
