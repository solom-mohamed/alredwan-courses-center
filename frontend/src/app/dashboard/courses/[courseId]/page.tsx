import { getCourseById } from "@/actions/courses";
import CourseImage from "@/assets/course-img.jpg";
import CourseDetailLayout, {
  CourseDetailUnavailable,
  CoursePurchaseAction,
} from "@/components/courses/CourseDetailLayout";
import CourseHeader from "@/components/courses/CourseHeader";
import {
  getCourseEnrollmentState,
  getDashboardCannotRateReason,
} from "@/lib/course-enrollment";

export default async function Page({
  params,
}: {
  params: Promise<{ courseId: string }>;
}) {
  const { courseId } = await params;
  const [course, enrollment] = await Promise.all([
    getCourseById(courseId),
    getCourseEnrollmentState({ courseId, courseType: "physical" }),
  ]);

  if (!course) {
    return <CourseDetailUnavailable />;
  }

  return (
    <CourseDetailLayout
      header={<CourseHeader course={course} />}
      imageSrc={course.image || CourseImage}
      imageAlt={course.name}
      description={course.description}
      descriptionExtra={
        <div className="mt-6 flex flex-wrap gap-4">
          {course.tags.map((tag) => (
            <span
              key={tag.id}
              className="border-olive-100 bg-olive-50 text-olive-600 rounded-full border px-6 py-2 text-xl font-bold"
            >
              {tag.name}
            </span>
          ))}
        </div>
      }
      price={course.price}
      purchase={
        <CoursePurchaseAction
          enrollment={enrollment}
          courseId={courseId}
          coursePrice={course.price}
          courseType="physical"
        />
      }
      ratings={{
        type: "course",
        id: courseId,
        showForm: enrollment.hasActiveEnrollment,
        cannotRateReason: getDashboardCannotRateReason(enrollment),
      }}
    />
  );
}
