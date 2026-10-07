import { parseISO } from "date-fns";
import {
  ArrowRight,
  Book,
  Calendar,
  CalendarDays,
  Clock,
  ListOrdered,
  UserRound,
  Users,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { getOptionalUser } from "@/actions/auth";
import { getCourseById } from "@/actions/courses";
import CourseImage from "@/assets/course-img.jpg";
import PublicCourseHero from "@/components/courses/PublicCourseHero";
import RatingsSection from "@/components/ratings/RatingsSection";
import { getPublicCannotRateReason } from "@/lib/rating-access";
import Button from "@/components/ui/Button";
import {
  cn,
  formatDate,
  formatTime,
  getArabicPlural,
  toHindiDigits,
} from "@/lib/utils";
import type { LectureOutlineItem } from "@/types/entities/courses";

const LECTURE_STATUS_BADGES: Record<string, string> = {
  completed: "bg-green-500/10 text-green-700",
  cancelled: "bg-red-500/10 text-red-700",
};

function getAgeInfo({
  for_adults,
  min_age,
  max_age,
}: {
  for_adults: boolean;
  min_age: number | null;
  max_age: number | null;
}): string | null {
  if (for_adults) return "هذه الدورة مخصصة للكبار";
  if (min_age !== null && max_age !== null)
    return `مناسبة للأعمار من ${toHindiDigits(min_age)} إلى ${toHindiDigits(max_age)} سنة`;
  if (min_age !== null)
    return `مناسبة للأعمار من ${toHindiDigits(min_age)} سنة فأكثر`;
  if (max_age !== null)
    return `مناسبة للأعمار حتى ${toHindiDigits(max_age)} سنة`;
  return null;
}

function LectureOutline({ lectures }: { lectures: LectureOutlineItem[] }) {
  return (
    <ol className="divide-y divide-gray-100 overflow-hidden rounded-3xl border border-gray-100">
      {lectures.map((lecture) => {
        const badge = LECTURE_STATUS_BADGES[lecture.status];
        const isMuted =
          lecture.status === "completed" || lecture.status === "cancelled";

        return (
          <li
            key={lecture.id}
            className={cn(
              "flex items-center gap-4 bg-white px-5 py-4",
              isMuted && "bg-gray-50",
            )}
          >
            <span className="bg-olive-500/10 text-olive-700 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-lg font-black">
              {toHindiDigits(lecture.lecture_number)}
            </span>
            <div className="min-w-0 flex-1">
              <p
                className={cn(
                  "truncate text-xl font-bold text-gray-900",
                  lecture.status === "cancelled" && "line-through",
                )}
              >
                {lecture.title ||
                  `المحاضرة رقم ${toHindiDigits(lecture.lecture_number)}`}
              </p>
              <p className="text-base text-gray-500">
                {formatDate(parseISO(lecture.day))}
                {lecture.start_time && (
                  <>
                    {" · "}
                    <span dir="rtl">
                      {formatTime(lecture.start_time)} –{" "}
                      {formatTime(lecture.end_time)}
                    </span>
                  </>
                )}
              </p>
            </div>
            {badge && (
              <span
                className={cn(
                  "shrink-0 rounded-full px-3 py-1 text-sm font-bold",
                  badge,
                )}
              >
                {lecture.status_display}
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const course = await getCourseById(id);
  const session = await getOptionalUser();

  if (!course) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="mb-4 text-4xl font-bold">الدورة غير موجودة</h1>
          <Button href="/courses">العودة للدورات</Button>
        </div>
      </div>
    );
  }

  const lectureCount = course.num_lectures;
  const schedules = course.schedules ?? [];
  const lectures = course.lectures ?? [];
  const ageInfo = getAgeInfo(course);
  const hasPlan = schedules.length > 0 || lectures.length > 0 || !!ageInfo;
  const description = course.description?.trim();

  const canEnroll =
    session === null || session.role === "parent" || session.role === "student";
  const enrollHref =
    session === null
      ? "/?login=true"
      : `/dashboard/courses/${course.id}?openModal=1`;

  return (
    <main className="min-h-screen bg-white">
      <PublicCourseHero
        imageSrc={course.image || CourseImage}
        imageAlt={course.name}
      >
        {course.tags.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {course.tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-full bg-white/20 px-4 py-1 text-sm font-bold text-white backdrop-blur-md"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}
        <h1 className="tablet:text-4xl mb-6 text-5xl font-black lg:text-7xl">
          {course.name}
        </h1>
        <div className="tablet:gap-x-6 tablet:gap-y-3 flex flex-wrap gap-8 text-lg font-medium opacity-90">
          <div className="flex items-center gap-2">
            <Calendar className="text-olive-300 h-5 w-5" />
            <span>تبدأ {formatDate(parseISO(course.start_date))}</span>
          </div>
          <div className="flex items-center gap-2">
            <Book className="text-olive-300 h-5 w-5" />
            <span>
              {toHindiDigits(lectureCount)}{" "}
              {getArabicPlural(lectureCount, {
                singular: "محاضرة",
                twofer: "محاضرتان",
                plural: "محاضرات",
              })}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="text-olive-300 h-5 w-5" />
            <span>{toHindiDigits(course.available_spots)} مكان متاح</span>
          </div>
        </div>
      </PublicCourseHero>

      <div className="container mx-auto px-6 py-16 lg:px-20">
        <div className="grid grid-cols-1 gap-16 lg:grid-cols-12">
          {/* Main Content */}
          <div className="space-y-12 lg:col-span-8">
            <div className="space-y-6">
              <h2 className="flex items-center gap-3 text-3xl font-bold">
                <div className="bg-olive-500 h-8 w-2 rounded-full" />
                عن هذه الدورة
              </h2>
              {description ? (
                <p className="text-xl leading-relaxed break-words whitespace-pre-wrap text-gray-600">
                  {description}
                </p>
              ) : (
                <p className="text-xl leading-relaxed text-gray-400">
                  لم يُضف وصف لهذه الدورة بعد، تواصل معنا لمعرفة المزيد عن
                  محتواها.
                </p>
              )}
            </div>

            {hasPlan && (
              <div className="space-y-6">
                <h2 className="flex items-center gap-3 text-3xl font-bold">
                  <div className="bg-olive-500 h-8 w-2 rounded-full" />
                  خطة الدورة
                </h2>

                {ageInfo && (
                  <p className="flex items-center gap-3 rounded-2xl bg-gray-50 px-5 py-4 text-lg text-gray-600">
                    <UserRound className="text-olive-500 h-5 w-5 shrink-0" />
                    {ageInfo}
                  </p>
                )}

                {schedules.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="flex items-center gap-2 text-xl font-bold text-gray-700">
                      <CalendarDays className="text-olive-500 h-5 w-5" />
                      المواعيد الأسبوعية
                    </h3>
                    <ul className="flex flex-wrap gap-3">
                      {schedules.map((schedule) => (
                        <li
                          key={schedule.id}
                          className="bg-olive-500/10 text-olive-700 flex items-center gap-2 rounded-full px-4 py-2 text-base font-bold"
                        >
                          <span>{schedule.weekday_display}</span>
                          <span className="text-olive-500/60" aria-hidden>
                            |
                          </span>
                          <span>
                            {formatTime(schedule.start_time)} –{" "}
                            {formatTime(schedule.end_time)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {lectures.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="flex items-center gap-2 text-xl font-bold text-gray-700">
                      <ListOrdered className="text-olive-500 h-5 w-5" />
                      المحاضرات
                    </h3>
                    <LectureOutline lectures={lectures} />
                  </div>
                )}
              </div>
            )}

            <div className="space-y-6">
              <h2 className="flex items-center gap-3 text-3xl font-bold">
                <div className="bg-olive-500 h-8 w-2 rounded-full" />
                المعلم
              </h2>
              <Link
                href={`/instructors/${course.instructor.id}`}
                className="group hover:bg-olive-500/5 flex items-center gap-6 rounded-3xl bg-gray-50 p-6 transition-colors"
              >
                <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-2xl shadow-md ring-4 ring-white">
                  <Image
                    src={course.instructor.image_url || CourseImage}
                    alt={course.instructor.name}
                    fill
                    sizes="80px"
                    className="object-cover"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="group-hover:text-olive-500 text-2xl font-bold transition-colors">
                    {course.instructor.name}
                  </h4>
                  <p className="text-gray-500">خبير في التعليم والتدريب</p>
                </div>
                <ArrowRight className="group-hover:text-olive-500 h-6 w-6 shrink-0 text-gray-300 transition-all group-hover:translate-x-[-8px]" />
              </Link>
            </div>

            <RatingsSection
              type="course"
              id={id}
              showForm={
                session?.role === "student" || session?.role === "parent"
              }
              cannotRateReason={getPublicCannotRateReason(session?.role)}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-8 lg:col-span-4">
            <div className="sticky top-24 rounded-3xl border-2 border-gray-100 bg-white p-8 shadow-xl shadow-gray-100/50">
              <div className="space-y-6">
                <div>
                  <p className="mb-1 text-gray-500">رسوم الاشتراك</p>
                  <p className="text-olive-500 text-5xl font-black">
                    {toHindiDigits(course.price)} جنيه
                  </p>
                </div>

                <div className="space-y-4 border-t border-gray-100 pt-4">
                  <div className="flex items-center justify-between text-gray-600">
                    <div className="flex items-center gap-2">
                      <Clock className="h-5 w-5 opacity-40" />
                      <span>مدة المحاضرة</span>
                    </div>
                    <span className="font-bold">ساعتان</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-600">
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5 opacity-40" />
                      <span>السعة القصوى</span>
                    </div>
                    <span className="font-bold">
                      {toHindiDigits(course.capacity)} طلاب
                    </span>
                  </div>
                </div>

                {canEnroll && (
                  <Button
                    className="shadow-olive-500/20 h-14 w-full rounded-2xl text-lg font-bold shadow-lg"
                    href={enrollHref}
                  >
                    سجل الآن في الدورة
                  </Button>
                )}

                <p className="text-center text-sm text-gray-400">
                  الدفع متاح عبر فوري، المحافظ الإلكترونية، أو في المركز
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
