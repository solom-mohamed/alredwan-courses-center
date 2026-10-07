/** Shown to signed-in staff (admin, instructor, supervisor) instead of the rating form. */
export const STAFF_CANNOT_RATE_MESSAGE =
  "التقييم متاح للطلاب وأولياء الأمور فقط.";

/** Shown to a student / parent who has no active enrollment in the course. */
export const NOT_ENROLLED_CANNOT_RATE_MESSAGE =
  "يمكنك تقييم الدورة بعد الاشتراك فيها.";

/**
 * Why a signed-in viewer can't rate on a public page; `undefined` for
 * visitors (they get the sign-in prompt) and for students / parents.
 */
export function getPublicCannotRateReason(
  role: string | undefined | null,
): string | undefined {
  if (!role || role === "student" || role === "parent") return undefined;
  return STAFF_CANNOT_RATE_MESSAGE;
}
