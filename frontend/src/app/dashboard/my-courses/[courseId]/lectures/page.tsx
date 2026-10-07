import { redirect } from "next/navigation";
import { getUser } from "@/actions/auth";
import { getCourseById } from "@/actions/courses";
import { getLecturesByCourseId } from "@/actions/lectures";
import CourseHeader from "@/components/courses/CourseHeader";
import CourseLecturesView from "@/components/courses/CourseLecturesView";

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ courseId: string }>;
  searchParams?: Promise<{ child?: string }>;
}) {
  const { courseId } = await params;
  const { role } = await getUser();

  // Students and parents see the lectures on the course page itself; the
  // separate list is the instructor's "المحاضرات" sidebar entry.
  if (role !== "instructor") {
    const childId = ((await searchParams) ?? {}).child;
    redirect(
      `/dashboard/my-courses/${courseId}${childId ? `?child=${childId}` : ""}`,
    );
  }

  const [course, lectures] = await Promise.all([
    getCourseById(courseId),
    getLecturesByCourseId(courseId, { role: "instructor" }),
  ]);

  return (
    <div className="flex h-full w-full max-w-full flex-col gap-4 overflow-y-auto px-3 pt-4 pb-6 sm:gap-6 sm:px-6 md:gap-10 md:px-12 md:pb-10">
      <CourseHeader course={course} />
      <div className="shadow-soft flex w-full max-w-full transform-gpu flex-col gap-4 overflow-hidden rounded-2xl border border-white/60 bg-white/60 p-3 backdrop-blur-md sm:gap-6 sm:rounded-[2.5rem] sm:p-10">
        <h2 className="text-olive-700 mb-3 text-center text-xl font-bold sm:mb-10 sm:text-4xl">
          محاضرات الدورة
        </h2>
        <CourseLecturesView lectures={lectures} course={course} />
      </div>
    </div>
  );
}
