import { getOnlineCourseById } from "@/actions/online-courses";
import CourseImage from "@/assets/course-img.jpg";
import CourseDetailLayout, {
  CourseDetailUnavailable,
  CoursePurchaseAction,
} from "@/components/courses/CourseDetailLayout";
import {
  getCourseEnrollmentState,
  getDashboardCannotRateReason,
} from "@/lib/course-enrollment";

const BACK_HREF = "/dashboard/courses?type=online";

export default async function Page({
  params,
}: {
  params: Promise<{ courseId: string }>;
}) {
  const { courseId } = await params;
  const [course, enrollment] = await Promise.all([
    getOnlineCourseById(courseId),
    getCourseEnrollmentState({ courseId, courseType: "online" }),
  ]);

  if (!course) {
    return <CourseDetailUnavailable backHref={BACK_HREF} />;
  }

  return (
    <CourseDetailLayout
      backHref={BACK_HREF}
      header={
        <div className="flex flex-col gap-4">
          <h1 className="text-5xl font-black text-gray-900">{course.name}</h1>
          {course.instructor && (
            <p className="text-xl text-gray-500">
              المدرب: {course.instructor.name}
            </p>
          )}
        </div>
      }
      imageSrc={course.thumbnail || CourseImage}
      imageAlt={course.name}
      description={course.description}
      price={course.price}
      purchase={
        <CoursePurchaseAction
          enrollment={enrollment}
          courseId={course.id}
          coursePrice={course.price}
          courseType="online"
        />
      }
      ratings={{
        type: "online_course",
        id: courseId,
        showForm: enrollment.hasActiveEnrollment,
        cannotRateReason: getDashboardCannotRateReason(enrollment),
      }}
    />
  );
}
