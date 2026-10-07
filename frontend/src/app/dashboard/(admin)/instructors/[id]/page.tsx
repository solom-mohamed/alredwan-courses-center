import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getInstructorAttendanceHistory,
  getInstructorDetail,
  getSupervisorSchedules,
} from "@/actions/admin-instructors";
import InstructorProfileView from "@/components/dashboard/admin/instructors/InstructorProfileView";
import InstructorTimetableView from "@/components/dashboard/admin/instructors/InstructorTimetableView";
import Button from "@/components/ui/Button";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function Page({ params }: PageProps) {
  const { id } = await params;

  // Parallel data fetching
  const [instructor, attendances, schedules] = await Promise.all([
    getInstructorDetail(id),
    getInstructorAttendanceHistory(id),
    getSupervisorSchedules(id),
  ]);

  if (!instructor) {
    notFound();
  }

  const isSupervisor = instructor.type === "supervisor";

  return (
    <div className="flex flex-col gap-32 px-16 py-32 max-[1000px]:gap-16 max-[1000px]:px-6 max-[1000px]:py-10">
      {/* Header with Navigation */}
      <div className="flex flex-col items-start justify-between gap-16 max-[1000px]:gap-6 md:flex-row md:items-center">
        <div>
          <h1 className="font-medad text-olive-800 text-4xl">تفاصيل المعلم</h1>
          <p className="text-olive-300">
            عرض وإدارة بيانات المعلم وجدول أعماله
          </p>
        </div>

        <div className="flex gap-12 max-[1000px]:w-full">
          <Link
            href={`/dashboard/all-attendances?instructor=${id}`}
            className="max-[1000px]:w-full"
          >
            <Button
              variant="outline"
              className="border-olive-200 text-olive-700 hover:bg-olive-50 max-[1000px]:w-full max-[1000px]:justify-center"
            >
              سجل الحضور الكامل
            </Button>
          </Link>
        </div>
      </div>

      {/* Profile Section */}
      <InstructorProfileView instructor={instructor} />

      {/* Timetable Section */}
      <InstructorTimetableView
        attendances={attendances}
        supervisorSchedules={schedules}
        isSupervisor={isSupervisor}
      />
    </div>
  );
}
