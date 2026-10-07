import { format } from "date-fns";
import { getUser } from "@/actions/auth";
import { getAttendances } from "@/actions/admin-attendances";
import AdminAttendancesView from "@/components/dashboard/admin/AdminAttendancesView";

export default async function Page(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const searchParams = await props.searchParams;
  // Opened from an instructor's profile ("سجل الحضور الكامل"): show that
  // instructor's whole history unless a date is picked.
  const date =
    (searchParams.date as string) ||
    (searchParams.instructor ? undefined : format(new Date(), "yyyy-MM-dd"));

  const [user, attendances] = await Promise.all([
    getUser(),
    getAttendances({
      date,
      instructor: searchParams.instructor
        ? Number(searchParams.instructor)
        : undefined,
      status: searchParams.status as string,
      attendance_type: searchParams.attendance_type as string,
      season: searchParams.season ? Number(searchParams.season) : undefined,
      search: typeof searchParams.search === "string" ? searchParams.search : undefined,
    }),
  ]);

  const greetingName = user.first_name || "Admin";

  return (
    <div className="flex flex-col px-16 py-26 max-[1000px]:px-6 max-[1000px]:py-10">
      <div className="font-medad text-olive-300 mb-15 flex flex-col gap-10 text-6xl max-[1000px]:mb-8 max-[1000px]:gap-6 max-[1000px]:text-4xl">
        <span className="text-olive-700">السلام عليكم يا {greetingName}</span>
        <div className="flex items-end justify-between max-[1000px]:flex-col max-[1000px]:items-start max-[1000px]:gap-2">
          <span>سجل الحضور والغياب</span>
          <span className="text-2xl text-gray-400 max-[1000px]:text-lg">
            التاريخ: {date ?? "كل التواريخ"}
          </span>
        </div>
      </div>

      <AdminAttendancesView initialAttendances={attendances} />
    </div>
  );
}
