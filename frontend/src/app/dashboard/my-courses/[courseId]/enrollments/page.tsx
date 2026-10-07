import { protect } from "@/actions/auth";
import { getCourseById } from "@/actions/courses";
import { getInstructorEnrollmentsByCourseId } from "@/actions/enrollments";
import CourseHeader from "@/components/courses/CourseHeader";
import CourseEnrollmentsView from "@/components/enrollments/CourseEnrollmentsView";

/** "الحجوزات" in the instructor sidebar: who is enrolled in this course. */
export default async function Page({
  params,
}: {
  params: Promise<{ courseId: string }>;
}) {
  await protect(["instructor"]);
  const { courseId } = await params;

  const [course, enrollments] = await Promise.all([
    getCourseById(courseId),
    getInstructorEnrollmentsByCourseId(courseId),
  ]);

  return (
    <div className="flex h-full w-full max-w-full flex-col gap-4 overflow-y-auto px-3 pt-4 pb-6 sm:gap-6 sm:px-6 md:gap-10 md:px-12 md:pb-10">
      <CourseHeader course={course} />
      <CourseEnrollmentsView enrollments={enrollments} />
    </div>
  );
}
