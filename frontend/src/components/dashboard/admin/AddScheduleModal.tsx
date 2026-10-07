"use client";

import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import type { WeeklySchedule } from "@/actions/admin-schedules";
import type { CourseListItem } from "@/types/entities/courses";
import type { Instructor } from "@/types/entities/instructors";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
} from "@/components/ui/Modal";
import TimePickerPopover from "@/components/ui/TimePickerPopover";
import { cn } from "@/lib/utils";

// Backend Weekday enum: Saturday=0 … Friday=6 (courses.models.Weekday).
const DAYS = [
  { label: "السبت", value: 0 },
  { label: "الأحد", value: 1 },
  { label: "الاثنين", value: 2 },
  { label: "الثلاثاء", value: 3 },
  { label: "الأربعاء", value: 4 },
  { label: "الخميس", value: 5 },
  { label: "الجمعة", value: 6 },
];

interface AddScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (
    schedule: Partial<WeeklySchedule> & { grace_period_minutes?: number; auto_absent_after_minutes?: number },
    courseId?: number,
    instructorId?: number,
  ) => Promise<void>;
  defaultType?: "lecture" | "supervision";
  fixedType?: "lecture" | "supervision";
  courses?: CourseListItem[];
  instructors?: Instructor[];
  editSchedule?: {
    id: number;
    instructor: number;
    day_of_week: number;
    start_time: string;
    end_time: string;
    grace_period_minutes: number;
    auto_absent_after_minutes: number;
  };
}

export default function AddScheduleModal({
  isOpen,
  onClose,
  onAdd,
  defaultType = "lecture",
  fixedType,
  courses = [],
  instructors = [],
  editSchedule,
}: AddScheduleModalProps) {
  const [type, setType] = useState<"lecture" | "supervision">(fixedType || defaultType);
  const [courseId, setCourseId] = useState<number | "">("");
  const [instructorId, setInstructorId] = useState<number | "">("");
  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [startTime, setStartTime] = useState("06:00 pm");
  const [endTime, setEndTime] = useState("07:00 pm");
  const [gracePeriod, setGracePeriod] = useState<number>(20);
  const [autoAbsent, setAutoAbsent] = useState<number>(60);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const convertTo12HourFormat = (timeStr: string) => {
    if (!timeStr) return "06:00 pm";
    try {
      const parts = timeStr.split(":");
      let hours = parseInt(parts[0], 10);
      const minutes = parts[1];
      const period = hours >= 12 ? "pm" : "am";
      if (hours > 12) {
        hours = hours - 12;
      } else if (hours === 0) {
        hours = 12;
      }
      return `${hours.toString().padStart(2, "0")}:${minutes} ${period}`;
    } catch (e) {
      return timeStr;
    }
  };

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (editSchedule) {
      setType("supervision");
      setInstructorId(editSchedule.instructor);
      setSelectedDay(editSchedule.day_of_week);
      setStartTime(convertTo12HourFormat(editSchedule.start_time));
      setEndTime(convertTo12HourFormat(editSchedule.end_time));
      setGracePeriod(editSchedule.grace_period_minutes);
      setAutoAbsent(editSchedule.auto_absent_after_minutes);
    } else {
      setType(fixedType || defaultType);
      setInstructorId("");
      setSelectedDay(0);
      setStartTime("06:00 pm");
      setEndTime("07:00 pm");
      setGracePeriod(20);
      setAutoAbsent(60);
    }
  }, [editSchedule, isOpen]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const convertTo24HourFormat = (timeStr: string) => {
    if (!timeStr) return "00:00:00";
    try {
      const [time, modifier] = timeStr.toLowerCase().split(" ");
      let [hours, minutes] = time.split(":");

      if (hours === "12") {
        hours = "00";
      }

      if (modifier === "pm" || modifier === "م") {
        hours = (parseInt(hours, 10) + 12).toString();
      }

      hours = hours.padStart(2, "0");
      minutes = minutes.padStart(2, "0");

      return `${hours}:${minutes}:00`;
    } catch (e) {
      return timeStr;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (type === "lecture" && !courseId) {
      toast.error("يرجى اختيار الدورة");
      return;
    }

    if (type === "supervision" && !instructorId) {
      toast.error("يرجى اختيار المحاضر/المشرف");
      return;
    }

    setIsSubmitting(true);

    const selectedCourse = courses.find((c) => c.id === courseId);
    const selectedInstructor = instructors.find((i) => i.id === instructorId);

    await onAdd(
      {
        type,
        course_name: selectedCourse?.name || "إشراف",
        instructor_name:
          type === "lecture"
            ? selectedCourse?.instructor?.name || "غير محدد"
            : selectedInstructor?.name || "غير محدد",
        weekday: selectedDay,
        weekday_display: DAYS.find((d) => d.value === selectedDay)?.label || "",
        start_time: convertTo24HourFormat(startTime),
        end_time: convertTo24HourFormat(endTime),
        season_name: selectedCourse?.season?.name || "-",
        student_count: selectedCourse?.enrolled_count || 0,
        grace_period_minutes: gracePeriod,
        auto_absent_after_minutes: autoAbsent,
      },
      Number(courseId),
      Number(instructorId),
    );

    setIsSubmitting(false);
    onClose();
    setCourseId("");
    setInstructorId("");
  };

  return (
    <Modal open={isOpen} onOpenChange={onClose}>
      <ModalContent className="sm:max-w-[600px] bg-white rounded-3xl p-0 overflow-hidden">
        <ModalHeader className="bg-olive-300 py-10 px-12">
          <ModalTitle className="text-white text-4xl font-medad text-right">
            {editSchedule
              ? "تعديل فترة الإشراف"
              : type === "lecture"
              ? "إضافة دورة جديدة"
              : "إضافة فترة إشراف"}
          </ModalTitle>
        </ModalHeader>

        <form onSubmit={handleSubmit} className="p-12 flex flex-col gap-10">
          {!fixedType && (
            <div className="flex bg-[#F3F3F5] p-2 rounded-2xl gap-2">
              <button
                type="button"
                onClick={() => setType("lecture")}
                className={cn(
                  "flex-1 py-4 rounded-xl text-2xl font-bold transition-all",
                  type === "lecture"
                    ? "bg-white shadow-md text-olive-700"
                    : "text-gray-400"
                )}
              >
                دورة تعليمية
              </button>
              <button
                type="button"
                onClick={() => setType("supervision")}
                className={cn(
                  "flex-1 py-4 rounded-xl text-2xl font-bold transition-all",
                  type === "supervision"
                    ? "bg-white shadow-md text-olive-700"
                    : "text-gray-400"
                )}
              >
                فترة إشراف
              </button>
            </div>
          )}

          {type === "lecture" ? (
            <div className="flex flex-col gap-4">
              <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                اختر الدورة
              </label>
              <select
                value={courseId}
                onChange={(e) => setCourseId(Number(e.target.value))}
                className="bg-[#F3F3F5] p-6 rounded-2xl text-2xl focus:outline-none focus:ring-2 focus:ring-olive-300 transition-all text-right appearance-none"
              >
                <option value="" disabled>
                  -- الرجاء اختيار دورة --
                </option>
                {courses.map((course) => (
                  <option key={`course-${course.id}`} value={course.id}>
                    {course.name} - {course.season?.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                المحاضر / المشرف
              </label>
              <select
                value={instructorId}
                onChange={(e) => setInstructorId(Number(e.target.value))}
                className="bg-[#F3F3F5] p-6 rounded-2xl text-2xl focus:outline-none focus:ring-2 focus:ring-olive-300 transition-all text-right appearance-none"
              >
                <option value="" disabled>
                  -- الرجاء اختيار المحاضر --
                </option>
                {instructors.map((instructor) => (
                  <option key={`inst-${instructor.id}`} value={instructor.id}>
                    {instructor.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex flex-col gap-4">
              <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                اليوم
              </label>
              <select
                value={selectedDay}
                onChange={(e) => setSelectedDay(Number(e.target.value))}
                className="bg-[#F3F3F5] p-6 rounded-2xl text-2xl focus:outline-none focus:ring-2 focus:ring-olive-300 appearance-none text-right"
              >
                {DAYS.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-4">
              <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                النطاق الزمني
              </label>
              <div className="flex items-center gap-4 bg-[#F3F3F5] p-4 rounded-2xl justify-between">
                <TimePickerPopover
                  value={endTime}
                  onChange={setEndTime}
                  trigger={
                    <div className="text-xl font-bold text-gray-700 cursor-pointer hover:text-olive-500">
                      {endTime}
                    </div>
                  }
                />
                <span className="text-gray-400">إلى</span>
                <TimePickerPopover
                  value={startTime}
                  onChange={setStartTime}
                  trigger={
                    <div className="text-xl font-bold text-gray-700 cursor-pointer hover:text-olive-500">
                      {startTime}
                    </div>
                  }
                />
                <span className="text-gray-400">من</span>
              </div>
            </div>
          </div>

          {type === "supervision" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="flex flex-col gap-4">
                <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                  فترة السماح (بالدقائق)
                </label>
                <input
                  type="number"
                  min="0"
                  value={gracePeriod}
                  onChange={(e) => setGracePeriod(Number(e.target.value))}
                  className="bg-[#F3F3F5] p-6 rounded-2xl text-2xl focus:outline-none focus:ring-2 focus:ring-olive-300 text-right"
                />
              </div>
              <div className="flex flex-col gap-4">
                <label className="text-2xl font-bold text-gray-600 mr-2 text-right">
                  الغياب التلقائي بعد (بالدقائق)
                </label>
                <input
                  type="number"
                  min="0"
                  value={autoAbsent}
                  onChange={(e) => setAutoAbsent(Number(e.target.value))}
                  className="bg-[#F3F3F5] p-6 rounded-2xl text-2xl focus:outline-none focus:ring-2 focus:ring-olive-300 text-right"
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-6 mt-6">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-olive-300 text-white py-6 rounded-2xl text-2xl font-bold hover:bg-olive-400 transition-all shadow-lg active:scale-95 disabled:opacity-50"
            >
              {isSubmitting ? "جاري الحفظ..." : "حفظ البيانات"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-100 text-gray-500 py-6 rounded-2xl text-2xl font-bold hover:bg-gray-200 transition-all"
            >
              إلغاء
            </button>
          </div>
        </form>
      </ModalContent>
    </Modal>
  );
}
