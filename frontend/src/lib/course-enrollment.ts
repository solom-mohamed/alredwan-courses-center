import { getUser, protect } from "@/actions/auth";
import {
  getMyEnrollmentRequests,
  getMyEnrollments,
} from "@/actions/enrollments";
import { getParentChildren, type ParentChildDetail } from "@/actions/user";
import {
  NOT_ENROLLED_CANNOT_RATE_MESSAGE,
  STAFF_CANNOT_RATE_MESSAGE,
} from "@/lib/rating-access";
import type { UserEntity } from "@/types/auth";
import type { EnrollmentRequestListItem } from "@/types/entities";

/** Roles allowed to open a course detail page (mirrors `dashboard/courses/layout.tsx`). */
export const COURSE_DETAIL_ROLES: UserEntity["role"][] = [
  "parent",
  "student",
  "admin",
  "instructor",
  "supervisor",
];

const ENROLLABLE_ROLES: UserEntity["role"][] = ["parent", "student"];

export type CoursePurchaseState =
  /** The viewer (or all of their children) already holds an active enrollment. */
  | "enrolled"
  /** A pending/processing enrollment request exists for this course. */
  | "pending"
  /** The viewer may submit an enrollment request. */
  | "enrollable"
  /** The viewer's role cannot enroll at all. */
  | "unavailable";

export interface CourseEnrollmentState {
  user: UserEntity;
  isParent: boolean;
  enrollmentRole: "parent" | "student";
  isEnrollable: boolean;
  /** Children of a parent who are not yet enrolled in this course. */
  childrenOptions: ParentChildDetail[];
  /** True when at least one `active` enrollment exists for this course. */
  hasActiveEnrollment: boolean;
  activeEnrollmentRequest: EnrollmentRequestListItem | undefined;
  purchaseState: CoursePurchaseState;
}

/**
 * Loads everything a course detail page needs to decide which enrollment
 * call-to-action to show. Guards the page with `protect` first, so it must
 * only be called from server components.
 */
export async function getCourseEnrollmentState({
  courseId,
  courseType,
}: {
  courseId: string;
  courseType: "physical" | "online";
}): Promise<CourseEnrollmentState> {
  await protect(COURSE_DETAIL_ROLES);

  const user = await getUser();
  const isParent = user.role === "parent";
  const enrollmentRole = isParent ? "parent" : "student";
  const isEnrollable = ENROLLABLE_ROLES.includes(user.role);
  const courseKey = courseType === "online" ? "online_course" : "course";

  // Enrollment endpoints are only open to parents and students; staff roles
  // just view the course, so skip the calls instead of logging 403s.
  const [myEnrollments, myEnrollmentRequests, parentChildren] =
    await Promise.all([
      isEnrollable ? getMyEnrollments() : Promise.resolve([]),
      isEnrollable && !isParent
        ? getMyEnrollmentRequests()
        : Promise.resolve([]),
      isParent ? getParentChildren() : Promise.resolve([]),
    ]);

  const enrollmentsInCourse = myEnrollments.filter(
    (enrollment) => String(enrollment[courseKey]) === String(courseId),
  );

  const enrolledChildIdsInCourse = new Set(
    enrollmentsInCourse
      .filter(
        (enrollment) =>
          (enrollment.participant_type === "child" ||
            Boolean(enrollment.child_id)) &&
          Boolean(enrollment.child_id),
      )
      .map((enrollment) => String(enrollment.child_id)),
  );

  const childrenOptions = parentChildren.filter(
    (child) => !enrolledChildIdsInCourse.has(String(child.id)),
  );

  const hasActiveEnrollment = enrollmentsInCourse.some(
    (enrollment) => enrollment.status === "active",
  );

  const activeEnrollmentRequest = myEnrollmentRequests.find(
    (request) =>
      String(request[courseKey]) === String(courseId) &&
      ["pending", "processing"].includes(request.status),
  );

  // A parent with children still left to enroll should see the purchase
  // modal even when one of their children is already enrolled.
  const canEnrollMoreChildren = isParent && childrenOptions.length > 0;

  let purchaseState: CoursePurchaseState;
  if (hasActiveEnrollment && !canEnrollMoreChildren) {
    purchaseState = "enrolled";
  } else if (activeEnrollmentRequest) {
    purchaseState = "pending";
  } else if (isEnrollable) {
    purchaseState = "enrollable";
  } else {
    purchaseState = "unavailable";
  }

  return {
    user,
    isParent,
    enrollmentRole,
    isEnrollable,
    childrenOptions,
    hasActiveEnrollment,
    activeEnrollmentRequest,
    purchaseState,
  };
}

/** Why the (always signed-in) dashboard viewer can't rate this course, if so. */
export function getDashboardCannotRateReason(
  enrollment: CourseEnrollmentState,
): string | undefined {
  if (enrollment.hasActiveEnrollment) return undefined;
  return enrollment.isEnrollable
    ? NOT_ENROLLED_CANNOT_RATE_MESSAGE
    : STAFF_CANNOT_RATE_MESSAGE;
}
