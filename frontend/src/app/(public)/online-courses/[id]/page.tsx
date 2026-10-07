import {
  ArrowRight,
  Book,
  Clock,
  Mail,
  Phone,
  PlayCircle,
  Radio,
} from "lucide-react";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { getOptionalUser } from "@/actions/auth";
import { getPublicOnlineCourseById } from "@/actions/online-courses";
import CourseImage from "@/assets/course-img.jpg";
import PublicCourseHero from "@/components/courses/PublicCourseHero";
import RatingsSection from "@/components/ratings/RatingsSection";
import { getPublicCannotRateReason } from "@/lib/rating-access";
import Button from "@/components/ui/Button";
import {
  CONTACT_EMAIL,
  CONTACT_EMAIL_HREF,
  CONTACT_PHONE,
  CONTACT_WHATSAPP_HREF,
} from "@/lib/contact";
import { formatDuration, getArabicPlural, toHindiDigits } from "@/lib/utils";

type PageProps = {
  params: Promise<{ id: string }>;
};

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { id } = await params;
  const course = await getPublicOnlineCourseById(id);

  if (!course) {
    return { title: "الدورة غير موجودة | واحة الرضوان" };
  }

  return {
    title: `${course.name} | واحة الرضوان`,
    description: course.description?.slice(0, 160) || undefined,
  };
}

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  const [course, session] = await Promise.all([
    getPublicOnlineCourseById(id),
    getOptionalUser(),
  ]);

  if (!course) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="mb-4 text-4xl font-bold">الدورة غير موجودة</h1>
          <Button href="/courses?type=online">العودة للدورات</Button>
        </div>
      </div>
    );
  }

  const lectureCount = course.video_count || 0;
  const videoLectures = course.video_lectures ?? [];
  const description = course.description?.trim();

  const canEnroll =
    session === null || session.role === "parent" || session.role === "student";
  const enrollHref =
    session === null
      ? "/?login=true"
      : `/dashboard/online-courses/${course.id}?openModal=1`;

  return (
    <main className="min-h-screen bg-white">
      <PublicCourseHero
        imageSrc={course.thumbnail || CourseImage}
        imageAlt={course.name}
      >
        <h1 className="tablet:text-4xl mb-6 text-5xl font-black lg:text-7xl">
          {course.name}
        </h1>
        <div className="flex flex-wrap gap-8 text-lg font-medium opacity-90">
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

            {videoLectures.length > 0 && (
              <div className="space-y-6">
                <h2 className="flex items-center gap-3 text-3xl font-bold">
                  <div className="bg-olive-500 h-8 w-2 rounded-full" />
                  محتوى الدورة
                </h2>
                <ol className="divide-y divide-gray-100 overflow-hidden rounded-3xl border border-gray-100">
                  {videoLectures.map((lecture, index) => (
                    <li
                      key={lecture.id}
                      className="flex items-center gap-4 bg-white px-5 py-4"
                    >
                      <span className="bg-olive-500/10 text-olive-700 grid h-11 w-11 shrink-0 place-items-center rounded-xl text-lg font-black">
                        {toHindiDigits(index + 1)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xl font-bold text-gray-900">
                          {lecture.title ||
                            `المحاضرة رقم ${toHindiDigits(index + 1)}`}
                        </p>
                        {!lecture.is_live_stream && (
                          <p className="flex items-center gap-1 text-base text-gray-500">
                            <PlayCircle className="h-4 w-4" />
                            {formatDuration(lecture.duration_seconds)}
                          </p>
                        )}
                      </div>
                      {lecture.is_live_stream && (
                        <span className="flex shrink-0 items-center gap-1 rounded-full bg-red-500/10 px-3 py-1 text-sm font-bold text-red-700">
                          <Radio className="h-4 w-4" />
                          بث مباشر
                        </span>
                      )}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {course.instructor && (
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
                  </div>
                  <ArrowRight className="group-hover:text-olive-500 h-6 w-6 shrink-0 text-gray-300 transition-all group-hover:translate-x-[-8px]" />
                </Link>
              </div>
            )}

            <RatingsSection
              type="online_course"
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
                    {toHindiDigits(Number(course.price))} جنيه
                  </p>
                </div>

                <div className="space-y-4 border-t border-gray-100 pt-4">
                  <div className="flex items-center justify-between text-gray-600">
                    <div className="flex items-center gap-2">
                      <Clock className="h-5 w-5 opacity-40" />
                      <span>إجمالي الساعات</span>
                    </div>
                    <span className="font-bold">
                      {formatDuration(course.total_duration_seconds)}
                    </span>
                  </div>
                </div>

                {canEnroll && (
                  <Button
                    href={enrollHref}
                    className="shadow-olive-500/20 h-14 w-full rounded-2xl text-lg font-bold shadow-lg"
                  >
                    سجل الآن في الدورة
                  </Button>
                )}

                <p className="text-center text-sm text-gray-400">
                  الدفع متاح عبر فوري، المحافظ الإلكترونية، أو في المركز
                </p>
              </div>
            </div>

            {/* الاستفسارات */}
            <div className="rounded-3xl border-2 border-gray-100 bg-white p-8 shadow-xl shadow-gray-100/50">
              <h3 className="mb-6 flex items-center gap-3 text-2xl font-bold">
                <div className="bg-olive-500 h-6 w-2 rounded-full" />
                الاستفسارات
              </h3>
              <div className="space-y-4">
                <a
                  href={CONTACT_WHATSAPP_HREF}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:border-olive-500/10 hover:bg-olive-500/5 flex items-center gap-4 rounded-2xl border border-transparent p-4 transition-colors"
                >
                  <div className="bg-olive-500/10 text-olive-500 flex h-12 w-12 shrink-0 items-center justify-center rounded-xl">
                    <Phone className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="mb-1 text-sm text-gray-500">واتساب</p>
                    <p className="font-bold text-gray-900" dir="ltr">
                      {CONTACT_PHONE}
                    </p>
                  </div>
                </a>
                <a
                  href={CONTACT_EMAIL_HREF}
                  className="hover:border-olive-500/10 hover:bg-olive-500/5 flex items-center gap-4 rounded-2xl border border-transparent p-4 transition-colors"
                >
                  <div className="bg-olive-500/10 text-olive-500 flex h-12 w-12 shrink-0 items-center justify-center rounded-xl">
                    <Mail className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="mb-1 text-sm text-gray-500">
                      البريد الإلكتروني
                    </p>
                    <p className="font-bold text-gray-900">{CONTACT_EMAIL}</p>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
